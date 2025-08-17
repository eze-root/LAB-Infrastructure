#!/bin/bash
# https://github.com/prometheus/node_exporter/releases
# linux-amd64, linux-arm64, darwin-amd64, darwin-arm64

ARCH=${1:-linux-amd64} 
OUTDIR="exporter/node_exporter"
TARGET="${ARCH}"
TARGET_BIN="$OUTDIR/$ARCH/node_exporter"

if [[ -x "$TARGET_BIN" ]]; then
  echo "Binary already exists: $TARGET_BIN (skip download)"
  exit 0
fi

if [ ! -d "$OUTDIR" ]; then
  mkdir -p "$OUTDIR"
fi


if [ ! -d "$OUTDIR/$ARCH" ]; then
  mkdir -p "$OUTDIR/$ARCH"
fi


URL=$(curl -s https://api.github.com/repos/prometheus/node_exporter/releases/latest \
  | grep browser_download_url \
  | grep "$TARGET" \
  | grep '.tar.gz' \
  | cut -d '"' -f 4)
FILENAME=$(basename "$URL")

curl -L -o "$OUTDIR/$FILENAME" "$URL"
tar -xzf "$OUTDIR/$FILENAME" -C "$OUTDIR/$ARCH" --strip-components=1
rm "$OUTDIR/$FILENAME"
chmod +x "$TARGET_BIN"
