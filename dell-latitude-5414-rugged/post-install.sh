#!/bin/bash

apt update
apt list --upgradable
apt upgrade

apt install sudo
/sbin/usermod -aG sudo $USER

# Networking
apt install network-manager network-manager-openvpn network-manager-openconnect wireguard

# Desktop Environment
apt install i3 i3-status xinit rofi firefox-esr alacritty transmission xfonts-terminus ranger mpv pulseaudio

# Utilities
apt install smartmontools dosfstools ntfs-3g alsa-utils ncdu

# Programming
apt install vim git tig

# Configuration files

mkdir $HOME/github -p
git clone https://github.com/x61s/cfg.git $HOME/github/cfg
cp -rv $HOME/github/cfg/dell-latitude-5414-rugged/i3/config $HOME/.config/i3/config
cp -rv $HOME/github/cfg/dell-latitude-5414-rugged/i3status.conf $HOME/.config/i3status.conf
cp -rv $HOME/github/cfg/dell-latitude-5414-rugged/rofi/ $HOME/.config/
cp -rv $HOME/github/cfg/.config/alacritty/ $HOME/.config/

