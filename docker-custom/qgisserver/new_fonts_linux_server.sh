#!/usr/bin/env bash

# sudo su
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root (sudo)." >&2
  exit 1
fi

# create directory
FONT_DIR="/usr/share/fonts/myfonts"
mkdir -p "$FONT_DIR"

# Copy fonts to the new directory
SOURCE_DIR="/fonts_location"
if [ -d "$SOURCE_DIR" ]; then
  cp "$SOURCE_DIR"/* "$FONT_DIR"/
else
  echo "Source directory for fonts ($SOURCE_DIR) not found." >&2
  exit 1
fi

# Set proper ownership and permissions
chown -R root:root "$FONT_DIR"
chmod -R 644 "$FONT_DIR"/*

# Update the font cache
fc-cache -f -v

echo "Fonts installed successfully."
