#!/bin/sh
set -e

rm -rf /backend/out

cd /backend

mkdir -p /backend/out/plugins/vaapi
mkdir -p /backend/out/plugins/pipewire
mkdir -p /backend/out/plugins/bad
mkdir -p /backend/out/plugins/good
mkdir -p /backend/out/libs

cp /usr/lib/gstreamer-1.0/libgstvaapi.so /backend/out/plugins/vaapi

cp /usr/lib/gstreamer-1.0/libgstpipewire.so /backend/out/plugins/pipewire

cp /usr/lib/libgstcodecparsers* /backend/out/libs/
cp /usr/lib/gstreamer-1.0/libgstvideoparsersbad.so /backend/out/plugins/bad

cp /usr/lib/gstreamer-1.0/libgstisomp4.so /backend/out/plugins/good
cp /usr/lib/gstreamer-1.0/libgstpulseaudio.so /backend/out/plugins/good
cp /usr/lib/gstreamer-1.0/libgstlame.so /backend/out/plugins/good

# Heavily inspired by https://github.com/Epictek/DeckyStream/blob/ed63bc4fbb83d0cdcb277630f57de6042b36ac00/backend/entrypoint.sh