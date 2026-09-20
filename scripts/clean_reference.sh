#!/usr/bin/env bash
set -euo pipefail

# Limpa um áudio de referência para clonagem de voz (XTTS-v2).
# Uso: ./clean_reference.sh entrada.wav saida.wav [dur_seg]
#
# Faz: 24kHz mono 16-bit > remove DC > reduz ruído > trima silêncios
#      (início/fim e pausas > 0.3s) > normaliza (loudnorm -16 LUFS)

IN="${1:?uso: $0 entrada.wav saida.wav [dur_seg]}"
OUT="${2:?uso: $0 entrada.wav saida.wav [dur_seg]}"
DUR="${3:-24}"

mkdir -p "$(dirname "$OUT")"

ffmpeg -y -nostdin -i "$IN" \
  -af "highpass=f=80,lowpass=f=8000,\
aresample=24000,\
aformat=channel_layouts=mono:channel_layouts=mono,\
silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.25,\
silenceremove=start_periods=1:stop_periods=-1:stop_threshold=-42dB:stop_silence=0.30,\
afftdn=nf=-22:nt=w,\
volume=2.0,\
loudnorm=I=-16:TP=-1.5:LRA=11,\
alimiter=limit=0.95,\
atrim=0:${DUR}" \
  -ar 24000 -ac 1 -c:a pcm_s16le "$OUT"

echo "OK -> $OUT"
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$OUT"