#!/bin/bash

# Define the screenshot directory and filename
screenshot_dir="$HOME/Pictures/Screenshots"
screenshot_file="$(date +%Y-%m-%d_%H-%M-%S).png"

# Create the directory if it doesn't exist
mkdir -p "$screenshot_dir"

# Take the screenshot
sound="$HOME/.local/share/sounds/camera-shutter-click-01.wav"
scrot "$screenshot_dir/$screenshot_file" && aplay $sound

# Notify user about the screenshot
notify-send "Screenshot Taken" "Saved as $screenshot_file"
