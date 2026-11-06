#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
command -v ffmpeg
command -v ffprobe
command -v tesseract
python -m venv --system-site-packages .local/analysis
.local/analysis/bin/python -m pip install 'opencv-python-headless==5.0.0.93'
python -m venv .local/asr
.local/asr/bin/python -m pip install 'faster-whisper==1.2.1' 'tesserocr==2.12.0' 'Pillow==13.0.0'
mkdir -p .local/tessdata
if ! [ -f .local/tessdata/por.traineddata ]; then
  curl --fail --location --proto '=https' --output .local/tessdata/por.traineddata https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/por.traineddata
fi
printf '%s\n' 'c4932b937207a9514b7514d518b931a99938c02a28a5a5a553f8599ed58b7deb  .local/tessdata/por.traineddata' | sha256sum --check
# Speech-model download is a separate step, after configured network access works.
