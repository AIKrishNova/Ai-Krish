"""NEXUS safe updater: review, approve, backup, apply and rollback."""

import difflib
import hashlib
import json
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UPDATE_DIR = ROOT / "backups" / "safe-updater"
PROPOSALS = UPDATE_DIR / "proposals"
SNAPSHOTS = UPDATE_DIR / "snapshots"
AUDIT = UPDATE_DIR / "audit.jsonl"

BLOCKED_PARTS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
}
BLOCKED_NAMES = {
    ".env", ".env.local", ".env.production",
    "id_rsa", "id_ed25519",
}
SECRET_PATTERN = re.compile(
    r"(api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*"
    r"""['"]?[^'"\s,]+""",
    re.IGNORECASE,
)


def safe_path(relative):
    p = Path(relative)
    if p.is_absolute() or not p.parts or ".." in p.parts:
        raise ValueError("Invalid project-relative path.")
    if any(x in BLOCKED_PARTS for x in p.parts):
        raise ValueError("Protected directory.")
    if any(x.lower() in BLOCKED_NAMES for x in p.parts):
        raise ValueError("Protected file.")

    target = ROOT / p
    if not target.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Path escapes the project.")
    if target.is_symlink() or not target.is_file():
        raise ValueError("Only existing regular files can be updated.")
    return p, target


def audit(action, **details):
    UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "action": action,
        **details,
    }
    with AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def digest(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def propose(relative, new_content):
    p, target = safe_path(relative)
    if target.stat().st_size > 1_000_000:
        raise ValueError("Current file exceeds 1 MB.")
    if not isinstance(new_content, str) or len(new_content) > 1_000_000:
        raise ValueError("Proposal must be text no larger than 1 MB.")
    if SECRET_PATTERN.search(new_content):
        raise ValueError("Possible secret detected; proposal rejected.")

    old = target.read_text(encoding="utf-8")
    if old == new_content:
        raise ValueError("No changes to propose.")

    if p.suffix == ".py":
        compile(new_content, str(p), "exec")

    diff = "".join(difflib.unified_diff(
        old.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"current/{p}",
        tofile=f"proposed/{p}",
    ))

    PROPOSALS.mkdir(parents=True, exist_ok=True)
    proposal_id = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    record = {
        "id": proposal_id,
        "path": p.as_posix(),
        "original_sha256": digest(old),
        "diff": diff,
        "new_content": new_content,
        "status": "pending_review",
    }
    (PROPOSALS / f"{proposal_id}.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8"
    )
    audit("proposal_created", id=proposal_id, path=p.as_posix())
    return proposal_id, diff


def load_proposal(proposal_id):
    file = PROPOSALS / f"{proposal_id}.json"
    if not file.is_file() or file.is_symlink():
        raise ValueError("Proposal not found.")
    proposal = json.loads(file.read_text(encoding="utf-8"))
    if proposal.get("id") != proposal_id:
        raise ValueError("Proposal ID mismatch.")
    return file, proposal


def apply(proposal_id):
    file, proposal = load_proposal(proposal_id)
    if proposal.get("status") != "pending_review":
        raise ValueError("Proposal is not pending review.")

    p, target = safe_path(proposal["path"])
    old = target.read_text(encoding="utf-8")

    if digest(old) != proposal["original_sha256"]:
        raise ValueError("File changed since proposal; create a new proposal.")

    new = proposal["new_content"]
    if SECRET_PATTERN.search(new):
        raise ValueError("Possible secret detected.")
    if p.suffix == ".py":
        compile(new, str(p), "exec")

    print("\nExact proposed diff:\n")
    print(proposal["diff"])
    print("\nBackup will be created before applying.")
    print("To approve, type this exact proposal ID:")
    print(proposal_id)
    if input("> ").strip() != proposal_id:
        audit("approval_cancelled", id=proposal_id)
        print("Cancelled. No project files changed.")
        return

    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    backup = SNAPSHOTS / f"{proposal_id}.original"
    shutil.copy2(target, backup)

    # Recheck immediately before writing.
    if digest(target.read_text(encoding="utf-8")) != digest(old):
        raise ValueError("File changed during approval; update cancelled.")

    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8",
            dir=target.parent, delete=False
        ) as temp:
            temp.write(new)
            temp.flush()
            temp_name = temp.name
        shutil.copystat(target, temp_name)
        Path(temp_name).replace(target)
        temp_name = None

        if p.suffix == ".py":
            compile(target.read_text(encoding="utf-8"), str(p), "exec")

        proposal["status"] = "applied"
        proposal["backup"] = str(backup.relative_to(ROOT))
        file.write_text(json.dumps(proposal, indent=2), encoding="utf-8")
        audit("update_applied", id=proposal_id, path=p.as_posix())
        print("Update applied. Backup:", backup)
    except Exception:
        shutil.copy2(backup, target)
        audit("update_failed_restored", id=proposal_id)
        raise
    finally:
        if temp_name and Path(temp_name).exists():
            Path(temp_name).unlink()



def rollback(proposal_id):
    file, proposal = load_proposal(proposal_id)
    if proposal.get("status") != "applied":
        raise ValueError("Only applied proposals can be rolled back.")

    p, target = safe_path(proposal["path"])

    current = target.read_text(encoding="utf-8")
    if digest(current) != digest(proposal["new_content"]):
        raise ValueError(
            "File changed after the update. Rollback cancelled "
            "to protect newer edits."
        )

    backup = SNAPSHOTS / f"{proposal_id}.original"
    if proposal.get("backup") != str(backup.relative_to(ROOT)):
        raise ValueError("Backup path does not match the expected snapshot.")

    if not backup.is_file() or backup.is_symlink():
        raise ValueError("Backup is missing or unsafe.")

    if input(
        f"Type ROLLBACK {proposal_id} to restore the backup:\n> "
    ).strip() != f"ROLLBACK {proposal_id}":
        print("Cancelled. No files changed.")
        return

    current_backup = SNAPSHOTS / f"{proposal_id}.before-rollback"
    shutil.copy2(target, current_backup)
    shutil.copy2(backup, target)

    proposal["status"] = "rolled_back"
    file.write_text(json.dumps(proposal, indent=2), encoding="utf-8")
    audit("rollback_completed", id=proposal_id, path=p.as_posix())
    print("Rollback complete. Previous updated file saved at:", current_backup)



def main():
    if len(sys.argv) == 1 or sys.argv[1] == "list":
        print("NEXUS safe updater")
        print("Project:", ROOT)
        for item in sorted(PROPOSALS.glob("*.json")) if PROPOSALS.exists() else []:
            p = json.loads(item.read_text(encoding="utf-8"))
            print(p["id"], "-", p["status"], "-", p["path"])
        print("Commands: list, apply PROPOSAL_ID, rollback PROPOSAL_ID")
        return

    if len(sys.argv) != 3:
        raise ValueError("Usage: manager.py list | apply ID | rollback ID")

    command, proposal_id = sys.argv[1:]
    if not re.fullmatch(r"\d{8}T\d{12}Z", proposal_id):
        raise ValueError("Invalid proposal ID format.")

    if command == "apply":
        apply(proposal_id)
    elif command == "rollback":
        rollback(proposal_id)
    else:
        raise ValueError("Unknown command.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print("Updater error:", exc)
        sys.exit(1)
