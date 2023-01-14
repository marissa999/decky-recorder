#!/bin/sh
set -e

# Docker
## Building Docker
docker build -t decky-recorder-build backend/.
## Running Docker
docker run -v $PWD/backend:/backend decky-recorder-build

# pnpmsetup
pnpm i

# build
npm run build

# Cleaning up potential old tmp dir
TMPDIR="/tmp/decky-recorder-zip"
if [ -d "$TMPDIR" ]; then
    rm -rf $TMPDIR
fi 

# Creating tmp dir
mkdir $TMPDIR

# Copying important files
mkdir $TMPDIR/backend
cp -R $PWD/backend/out $TMPDIR/backend/
cp -R $PWD/dist $TMPDIR/dist
cp $PWD/LICENSE $TMPDIR
cp $PWD/LICENSE.md $TMPDIR
cp $PWD/README.md $TMPDIR
cp $PWD/plugin.json $TMPDIR
cp $PWD/package.json $TMPDIR

zip -r $PWD/Decky-Recorder.zip $TMPDIR