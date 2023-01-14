import os
import sys
import subprocess
import signal
from datetime import datetime

# append py_modules to PYTHONPATH
sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/py_modules")

DEPSPATH = "/home/deck/homebrew/decky-recorder/backend/out"
DEPSPLUGINSPATH = DEPSPATH + "/plugins"
DEPSLIBSSPATH = DEPSPATH + "/libs"

class Plugin:

	recording_process = None
	deps_installed = False

	async def start_recording(self):
		if self.recording_process is not None:
			return
		os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"
		os.environ["XDG_SESSION_TYPE"] = "wayland"
		os.environ["HOME"] = "/home/deck"
		# Heavily inspired by
		# https://git.sr.ht/~avery/recapture/tree/0fdbe014ec1f11bce386dc9468a760f8aed492e9/item/record.go#L19
		# https://git.sr.ht/~avery/recapture/tree/0fdbe014ec1f11bce386dc9468a760f8aed492e9/item/plugin/src/index.tsx#L161
		filename = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
		monitor = subprocess.getoutput("pactl get-default-sink") + ".monitor"
		cmd = "GST_VAAPI_ALL_DRIVERS=1 GST_PLUGIN_PATH={} LD_LIBRARY_PATH={} gst-launch-1.0 -e -vvv pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse ! mp4mux name=sink ! filesink location=/home/deck/Videos/{}.mp4 pulsesrc device=\"{}\" ! audioconvert ! lamemp3enc target=bitrate bitrate=128 cbr=true ! sink.audio_0".format(DEPSPLUGINSPATH, DEPSLIBSSPATH, filename, monitor)
		self.recording_process = subprocess.Popen(cmd, shell = True)
		return

	async def end_recording(self):
		if self.recording_process is None:
			return
		self.recording_process.send_signal(signal.SIGINT)
		self.recording_process = None
		return

	async def is_recording(self):
		return self.recording_process is not None

	async def _main(self):
		return

	async def _unload(self):
		if Plugin.is_recording(self):
			Plugin.end_recording(self)
		return