#!/bin/bash
# https://github.com/zxh326/clash-exporter/releases
# linux-amd64, linux-arm64, darwin-amd64, darwin-arm64

ARCH=${1:-linux-amd64} 
OUTDIR="exporter/clash_exporter"
TARGET="${ARCH}"
echo "Downloading Clash Exporter for target: $TARGET"

if [ ! -d "$OUTDIR" ]; then
  mkdir -p "$OUTDIR"
fi

if [ ! -d "$OUTDIR/$ARCH" ]; then
  mkdir -p "$OUTDIR/$ARCH"
fi


URL=$(curl -s https://api.github.com/repos/zxh326/clash-exporter/releases/latest \
  | grep browser_download_url \
  | grep "$TARGET" \
  | grep '.tar.gz' \
  | cut -d '"' -f 4)
FILENAME=$(basename "$URL")

curl -L -o "$OUTDIR/$FILENAME" "$URL"
tar -xzf "$OUTDIR/$FILENAME" -C "$OUTDIR/$ARCH" 
rm "$OUTDIR/$FILENAME"
BIN_PATH=$(find "$OUTDIR"  -type f -name 'clash-exporter*' | head -n1)
echo "Binary path: $BIN_PATH"
mv $BIN_PATH "$OUTDIR/$ARCH/clash_exporter"
chmod +x "$OUTDIR/$ARCH/clash_exporter"