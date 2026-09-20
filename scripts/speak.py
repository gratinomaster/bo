#!/usr/bin/env python3
"""Fala qualquer texto com a voz clonada (XTTS-v2).

Uso:
  ./speak.py --text "Olá, eu sou o Boni!" [--voice models/boni] [--out output/x.wav]
"""
import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("COQUI_TOS_AGREED", "1")
os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")


def _patch_torchaudio():
    """torchaudio 2.11+ usa backend torchcodec por padrão (indisponível aqui).
    Redireciona a leitura de wav/flac/ogg para soundfile, que já está instalado."""
    import torch
    import torchaudio
    import numpy as np
    import soundfile as sf

    def _load(path, out=None, normalization=True, channels_first=True,
              num_frames=0, offset=0, format=None, backend=None, **kw):
        if isinstance(path, str) and path.lower().endswith((".wav", ".flac", ".ogg")):
            data, sr = sf.read(path, dtype="float32", always_2d=True)
            t = torch.from_numpy(np.ascontiguousarray(data))
            t = t.T if channels_first else t.unsqueeze(0)
            if out is not None:
                out.copy_(t)
                return out, sr
            return t, sr
        return None

    torchaudio.load = _load


if not os.environ.get("_TTS_PATCHED"):
    _patch_torchaudio()
    os.environ["_TTS_PATCHED"] = "1"

VOICES_DIR = Path(__file__).resolve().parent.parent / "models"


def main() -> int:
    ap = argparse.ArgumentParser(description="Clona voz por referência (XTTS-v2)")
    ap.add_argument("--voice", default="boni", help="nome do modelo em models/")
    ap.add_argument("--text", required=True, help="texto a ser falado (pt-BR)")
    ap.add_argument("--out", default="output/speech.wav", help="arquivo de saída")
    ap.add_argument("--speed", type=float, default=1.0, help="velocidade (0.5-2.0)")
    args = ap.parse_args()

    vdir = VOICES_DIR / args.voice
    cfg = json.loads((vdir / "config.json").read_text())
    ref = vdir / cfg["reference_wav"]
    lang = cfg.get("language", "pt")

    if not ref.exists():
        sys.exit(f"erro: referencia não existe: {ref}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    from TTS.api import TTS

    print("carregando XTTS-v2 (primeira vez baixa o modelo ~1.8GB)...")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
    tts.tts_to_file(
        text=args.text,
        file_path=str(out),
        speaker_wav=str(ref),
        language=lang,
        speed=args.speed,
    )
    print(f"OK -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())