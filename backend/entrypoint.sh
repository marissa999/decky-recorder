#!/bin/sh
set -e

rm -rf /backend/out

cd /backend

mkdir -p /backend/out
cp -r /pacman/usr/lib/* /backend/out

# Heavily inspired by https://github.com/Epictek/DeckyStream/blob/ed63bc4fbb83d0cdcb277630f57de6042b36ac00/backend/entrypoint.sh