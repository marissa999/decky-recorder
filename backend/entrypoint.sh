#!/bin/sh
set -e

rm -rf /backend/out

cd /backend

mkdir -p /backend/out/plugins
mkdir -p /backend/out/libs

cp /usr/lib/gstreamer-1.0/libgstvaapi.so /backend/out/plugins

cp /usr/lib/gstreamer-1.0/libgstpipewire.so /backend/out/plugins

cp /usr/lib/libgstcodecparsers* /backend/out/libs/
cp /usr/lib/gstreamer-1.0/libgstvideoparsersbad.so /backend/out/plugins

cp /usr/lib/gstreamer-1.0/libgstisomp4.so /backend/out/plugins
cp /usr/lib/gstreamer-1.0/libgstpulseaudio.so /backend/out/plugins
cp /usr/lib/gstreamer-1.0/libgstlame.so /backend/out/plugins
cp /usr/lib/gstreamer-1.0/libgstrtp.so /backend/out/plugins
cp /usr/lib/gstreamer-1.0/libgstrtpmanager.so /backend/out/plugins
cp /usr/lib/gstreamer-1.0/libgstrtsp.so /backend/out/plugins
cp /usr/lib/gstreamer-1.0/libgstudp.so /backend/out/plugins

cp /usr/lib/girepository-1.0/GstRtspServer-1.0.typelib /backend/out/plugins
cp /usr/lib/gstreamer-1.0/libgstrtspclientsink.so /backend/out/plugins
cp /usr/lib/libgstrtspserver-1.0.so /backend/out/libs
cp /usr/lib/libgstrtspserver-1.0.so.0 /backend/out/libs

# Heavily inspired by https://github.com/Epictek/DeckyStream/blob/ed63bc4fbb83d0cdcb277630f57de6042b36ac00/backend/entrypoint.sh