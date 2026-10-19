# Sets up AI KRISH on Windows after you have cloned the repository.
# Run in PowerShell, from anywhere:
#   powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

function Need($cmd, $hint) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "$cmd was not found. $hint" }
}
Need "git"  "Install Git from https://git-scm.com/download/win, then open a new PowerShell window."
Need "node" "Install the LTS version from https://nodejs.org, then open a new PowerShell window."
$major = [int](node -p "process.versions.node.split('.')[0]")
if ($major -lt 20) { throw "Node $(node -v) is too old. Install Node 20 or newer (the LTS) from https://nodejs.org" }
if (-not (Test-Path "package-lock.json")) { throw "package-lock.json is missing. Are you inside the AI KRISH folder?" }

Write-Host "`n== Installing dependencies (npm ci)"
npm.cmd ci
if ($LASTEXITCODE -ne 0) { throw "npm ci failed (see the messages above)." }

Write-Host "`n== Environment file"
if (Test-Path ".env.local") {
  Write-Host ".env.local already exists. Leaving it alone."
} else {
  if (-not (Test-Path ".env.example")) { throw ".env.example is missing." }
  Copy-Item ".env.example" ".env.local"
  Write-Host "Created .env.local from .env.example."
}
if (Select-String -Path ".env.local" -Pattern "your-|choose-a-long" -Quiet) {
  Write-Host "NOTE: .env.local still has placeholder values. Open it in Notepad and fill in your own keys."
  Write-Host "      (Never paste keys into chat or commit this file.)"
}

Write-Host "`n== Done"
Write-Host "Start the app:     npm.cmd run dev     then open http://localhost:3000"
Write-Host "Production check:  npm.cmd run build ; npm.cmd run start"
