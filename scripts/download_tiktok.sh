#!/usr/bin/env bash
set -euo pipefail

# Baixa o áudio de um vídeo/perfil do TikTok (áudio só, WAV).
# Uso: ./download_tiktok.sh <url-do-video-ou-perfil> [nome_base]
# Ex.: ./download_tiktok.sh https://www.tiktok.com/@oladobdeboni/video/7424152515362491654

URL="${1:?uso: $0 <url_tiktok> [nome_base]}"
NAME="${2:-audio}"
OUTDIR="audio/raw"

mkdir -p "$OUTDIR"
exec python3 -m yt_dlp --impersonate chrome -x \
  --audio-format wav --audio-quality 0 \
  --no-playlist \
  -o "$OUTDIR/$NAME.%(id)s.%(ext)s" \
  "$URL"