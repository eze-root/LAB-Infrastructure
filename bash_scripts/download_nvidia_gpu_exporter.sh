#!/bin/bash
# https://github.com/utkuozdemir/nvidia_gpu_exporter/releases
# linux_amd64, linux_arm64, darwin_amd64

ARCH=${1:-linux_x86_64}
OUTDIR="exporter/nvidia_gpu_exporter"
TARGET="${ARCH}"
echo "Downloading Nvidia GPU Exporter for target: $TARGET"

if [ ! -d "$OUTDIR" ]; then
  mkdir -p "$OUTDIR"
fi

if [[ "$ARCH" == "linux_x86_64" ]]; then
  ARCH="linux-amd64"
fi

if [ ! -d "$OUTDIR/$ARCH" ]; then
  mkdir -p "$OUTDIR/$ARCH"
fi


URL=$(curl -s https://api.github.com/repos/utkuozdemir/nvidia_gpu_exporter/releases/latest \
  | grep browser_download_url \
  | grep "$TARGET" \
  | grep '.tar.gz' \
  | cut -d '"' -f 4)
FILENAME=$(basename "$URL")

# 将linux_x86_64转换为linux-amd64
curl -L -o "$OUTDIR/$FILENAME" "$URL"
tar -xzf "$OUTDIR/$FILENAME" -C "$OUTDIR/$ARCH" 
rm "$OUTDIR/$FILENAME"
chmod +x "$OUTDIR/$ARCH/nvidia_gpu_exporter"