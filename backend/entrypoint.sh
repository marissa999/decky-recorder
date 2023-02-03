#!/bin/sh
set -e

OUTDIR="/backend/decky-out"
if [ -d "$OUTDIR" ]; then
    sudo rm -rf $OUTDIR
fi

cd /backend

mkdir -p /backend/decky-out
cp -r /pacman/usr/lib/* /backend/decky-out

# Heavily inspired by https://github.com/Epictek/DeckyStream/blob/ed63bc4fbb83d0cdcb277630f57de6042b36ac00/backend/entrypoint.sh
