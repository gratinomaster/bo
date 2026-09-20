#!/usr/bin/env python3
"""Cria um modelo de voz reutilizável a partir de um vídeo do TikTok.

Uso:
  ./make_voice.py --url <video_tiktok> --name boni [--dur 20]

Fluxo: download (yt-dlp) -> limpeza (ffmpeg) -> transcrição (faster-whisper)
       -> monta models/<name>/ com reference.wav + transcript.txt + config.json
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True, **kw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="URL do vídeo TikTok com a voz")
    ap.add_argument("--name", required=True, help="nome do modelo (ex.: boni)")
    ap.add_argument("--dur", type=int, default=20, help="segundos de fala limpa")
    ap.add_argument("--person", default="", help="descrição da pessoa (opcional)")
    args = ap.parse_args()

    vid_id = args.url.rstrip("/").rsplit("/", 1)[-1]
    raw = ROOT / "audio" / "raw"
    clean = ROOT / "audio" / "clean"
    vdir = ROOT / "models" / args.name

    raw.mkdir(parents=True, exist_ok=True)
    clean.mkdir(parents=True, exist_ok=True)
    vdir.mkdir(parents=True, exist_ok=True)

    # 1) download
    run([str(SCRIPTS / "download_tiktok.sh"), args.url, args.name])
    raws = sorted(raw.glob(f"{args.name}.*.wav"))
    if not raws:
        sys.exit("nenhum áudio baixado")
    src = raws[-1]

    # 2) limpeza
    cleaned = clean / f"{args.name}.clean.wav"
    run([str(SCRIPTS / "clean_reference.sh"), str(src), str(cleaned), str(args.dur)])

    # 3) transcrição
    from faster_whisper import WhisperModel

    print("transcrevendo (faster-whisper small)...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(str(cleaned), language="pt", vad_filter=True)
    transcript = " ".join(s.text.strip() for s in segs)

    # 4) monta o perfil
    (vdir / "reference.wav").write_bytes(cleaned.read_bytes())
    (vdir / "transcript.txt").write_text(transcript + "\n", encoding="utf-8")
    cfg = {
        "name": args.name,
        "person": args.person or f"voz de {args.url}",
        "source": args.url,
        "reference_wav": "reference.wav",
        "reference_transcript": "transcript.txt",
        "language": "pt",
        "sr": 24000,
        "duration_sec": args.dur,
        "engine": "XTTS-v2 via coqui-tts (free)",
    }
    (vdir / "config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")

    print(f"\nModelo criado: {vdir}")
    print(f"Reference: {vdir}/reference.wav")
    print(f"Transcript: {transcript[:200]}")
    print("Para usar: python3 scripts/speak.py --voice", args.name, '--text "Olá!"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())