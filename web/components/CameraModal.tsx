"use client";

import { useEffect, useRef, useState } from "react";

function cameraError(e: unknown) {
  const name = e instanceof DOMException ? e.name : "";
  if (name === "NotAllowedError" || name === "PermissionDeniedError") return "Camera permission was denied. Allow camera access for this site in your browser settings, then try again.";
  if (name === "NotFoundError" || name === "DevicesNotFoundError") return "No camera was found on this device.";
  if (name === "NotReadableError" || name === "TrackStartError") return "The camera is being used by another app. Close it and try again.";
  if (name === "SecurityError") return "The camera needs a secure page (https or localhost).";
  return "Could not start the camera.";
}

export default function CameraModal({ onCapture, onClose }: { onCapture: (f: File) => void; onClose: () => void }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [facing, setFacing] = useState<"environment" | "user">("environment");
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);
  const [multi, setMulti] = useState(false);
  const [shot, setShot] = useState<{ blob: Blob; url: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function start() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: facing }, width: { ideal: 1920 }, height: { ideal: 1080 } },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        const v = videoRef.current;
        if (v) {
          v.srcObject = stream;
          await v.play();
        }
        setReady(true);
        const devices = await navigator.mediaDevices.enumerateDevices();
        if (!cancelled) setMulti(devices.filter((d) => d.kind === "videoinput").length > 1);
      } catch (e) {
        if (!cancelled) setError(cameraError(e));
      }
    }
    start();
    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, [facing]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  useEffect(() => () => { if (shot) URL.revokeObjectURL(shot.url); }, [shot]);

  async function capture() {
    const v = videoRef.current;
    if (!v || !v.videoWidth) return;
    const scale = Math.min(1, 2000 / Math.max(v.videoWidth, v.videoHeight));
    const c = document.createElement("canvas");
    c.width = Math.round(v.videoWidth * scale);
    c.height = Math.round(v.videoHeight * scale);
    c.getContext("2d")?.drawImage(v, 0, 0, c.width, c.height);
    const blob: Blob | null = await new Promise((res) => c.toBlob(res, "image/jpeg", 0.9));
    if (!blob) {
      setError("Could not capture the photo. Please try again.");
      return;
    }
    setShot({ blob, url: URL.createObjectURL(blob) });
  }

  function use() {
    if (!shot) return;
    onCapture(new File([shot.blob], `camera-${new Date().toISOString().replace(/[:.]/g, "-")}.jpg`, { type: "image/jpeg" }));
    onClose();
  }

  const btn = "rounded-full px-5 py-2 text-sm font-semibold";
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-3" role="dialog" aria-modal="true" aria-label="Camera">
      <div className="flex max-h-full w-full max-w-lg flex-col gap-3 rounded-2xl bg-white p-4 shadow-xl">
        <div className="flex items-center justify-between">
          <div className="text-xs uppercase tracking-[0.3em] text-blue-600">Camera</div>
          <button onClick={onClose} className="rounded-lg border border-slate-300 px-3 py-1 text-sm text-slate-700 hover:bg-slate-100">Close</button>
        </div>
        {error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{error}</div>
        ) : (
          <div className="relative min-h-0 overflow-hidden rounded-xl bg-black">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            {shot && <img src={shot.url} alt="Captured photo preview" className="max-h-[60vh] w-full object-contain" />}
            <video ref={videoRef} playsInline muted autoPlay className={`max-h-[60vh] w-full object-contain ${shot ? "hidden" : ""}`} />
            {!ready && !shot && <div className="absolute inset-0 flex items-center justify-center text-sm text-white/80">Starting camera... allow access if asked.</div>}
          </div>
        )}
        <div className="flex flex-wrap justify-center gap-2">
          {shot ? (
            <>
              <button onClick={() => setShot(null)} className={`${btn} border border-slate-300 text-slate-700 hover:bg-slate-100`}>Retake</button>
              <button onClick={use} className={`${btn} bg-blue-600 text-white hover:bg-blue-500`}>Use photo</button>
            </>
          ) : (
            <>
              {multi && (
                <button onClick={() => { setReady(false); setFacing(facing === "user" ? "environment" : "user"); }} className={`${btn} border border-slate-300 text-slate-700 hover:bg-slate-100`}>
                  Switch camera
                </button>
              )}
              <button onClick={capture} disabled={!ready} className={`${btn} bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-40`}>Take photo</button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
