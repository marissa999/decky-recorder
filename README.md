# Decky Recorder

![Decky-Recorder Example Screenshot](decky-recorder-screenshot.jpg)

This plugin is heavily based on the Recapture-Plugin for Crankshaft from Avery: https://git.sr.ht/~avery/recapture
In particular a lot of code for the gst-launch-1.0-command itself and the additionally needed dependencies were taken from the Recapture-Plugin.

https://git.sr.ht/~avery/recapture/tree/0fdbe014ec1f11bce386dc9468a760f8aed492e9/item/record.go#L19
https://git.sr.ht/~avery/recapture/tree/0fdbe014ec1f11bce386dc9468a760f8aed492e9/item/plugin/src/index.tsx#L161
https://git.sr.ht/~avery/recapture/tree/0fdbe014ec1f11bce386dc9468a760f8aed492e9/item/plugin/Makefile#L22

This plugin was made with the decky-plugin-template (https://github.com/SteamDeckHomebrew/decky-plugin-template)

Please do not judge my code, I am bad!

This plugin is still in WIP.

### Thanks
- Huge huge thanks to [@safijari](https://github.com/safijari) for fully implementing Rolling Recording/Replay Mode (https://github.com/safijari/decky-recorder/tree/rolling-record)
- [@Newbytee](https://github.com/Newbytee) for pointing out that I forgot the "-e"-option in the gst-launch-1.0-command
- Avery for the original Recapture Plugin
- Epictek for inspiring me to setup a proper build process (https://github.com/Epictek/DeckyStream I found out about this plugin when I was basically already done q.q)
- [kleutzinger](https://github.com/kleutzinger) for fixing the file names and making it so it confirms with ISO_8601

### Known issues
- It seems like long recordings (over 30 minutes) dont get saved (https://github.com/marissa999/decky-recorder/issues/2#issuecomment-1445399044)
- It seems like starting a recording while docked and outputting to a 4k monitor causes the Deck to crash (https://github.com/marissa999/decky-recorder/issues/8)

### Building
If you want to build this plugin in theory you only need to run build-zip.sh. You will need the following:
- npm
- pnpm
- python + pip
- Docker
- zip
I only tested this on Arch Linux (which I use, btw!)

### TODO
- WIP: Adding the option to toggle game audio + mic audio (Current state: You can enable mic audio, but not disable game audio. Figure out a way to filter and remove audio from pipewiresrc?)
- WIP: Figuring out why sometimes recording stutter/audio + video don't align. Might require re-transcoding with ffmpeg to re-align dts-stuff? Dunno (Current state: FFmpeg will now copy the files from tmpfs to the ~/Videos-folder and fix dts while doing so. Not working: FFmpeg needs to run AFTER gst-launcher-1.0 finished, but because gst-launcher-1.0 is running through a python subprocess with shell=true this is apparently not that easy and I can not just wait for it?!)
- WIP: Finishing RTSP-Server-Sink (Current state: UI is done, I should have all libraries? I think? And if not I can easily add missing libraries. But... What is the actual pipeline that I need?)
