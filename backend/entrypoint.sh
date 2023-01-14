#!/bin/sh
set -e

cd /backend
mkdir -p /backend/out/plugins/vaapi
mkdir -p /backend/out/plugins/pipewire
mkdir -p /backend/out/plugins/bad
mkdir -p /backend/out/plugins/good
mkdir -p /backend/out/libs

cp /usr/lib/gstreamer-1.0/libgstvaapi.so /backend/out/plugins/

cp /usr/lib/gstreamer-1.0/libgstpipewire.so /backend/out/plugins/

cp /usr/lib/libgstcodecparsers* /backend/out/libs/
cp /usr/lib/gstreamer-1.0/libgstvideoparsersbad.so /backend/out/plugins/

cp /usr/lib/gstreamer-1.0/libgstisomp4.so /backend/out/plugins/
cp /usr/lib/gstreamer-1.0/libgstpulseaudio.so /backend/out/plugins/
cp /usr/lib/gstreamer-1.0/libgstlame.so /backend/out/plugins/