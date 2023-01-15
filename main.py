import os
import sys
import subprocess
import signal
from datetime import datetime

DEPSPATH = "/home/deck/homebrew/plugins/decky-recorder/backend/out"
DEPSPLUGINSPATH = DEPSPATH + "/plugins"
DEPSLIBSSPATH = DEPSPATH + "/libs"

import logging
logging.basicConfig(filename="/tmp/decky-recorder.log",
					format='Decky Recorder: %(asctime)s %(levelname)s %(message)s',
					filemode='w+',
					force=True)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
std_out_file = open('/tmp/decky-recorder-std-out.log', 'w')
std_err_file = open('/tmp/decky-recorder-std-err.log', 'w')

class Plugin:

	_recording_process = None
	_mode = "localFile"

	async def start_recording(self):
		logger.info("Starting recording")
		if Plugin.is_recording(self) == True:
			logger.info("Error: Already recording")
			return

		os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"
		os.environ["XDG_SESSION_TYPE"] = "wayland"
		os.environ["HOME"] = "/home/deck"

		monitor = subprocess.getoutput("pactl get-default-sink") + ".monitor"
		
		cmd = None
		if (self._mode == "localFile"):
			filename = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
			# Heavily inspired by
			# https://git.sr.ht/~avery/recapture/tree/0fdbe014ec1f11bce386dc9468a760f8aed492e9/item/record.go#L19
			# https://git.sr.ht/~avery/recapture/tree/0fdbe014ec1f11bce386dc9468a760f8aed492e9/item/plugin/src/index.tsx#L161
			cmd = "GST_VAAPI_ALL_DRIVERS=1 GST_PLUGIN_PATH={} LD_LIBRARY_PATH={} gst-launch-1.0 -e -vvv pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse ! mp4mux name=sink ! filesink location=/home/deck/Videos/{}.mp4 pulsesrc device=\"Recording_{}\" ! audioconvert ! lamemp3enc target=bitrate bitrate=128 cbr=true ! sink.audio_0".format(DEPSPLUGINSPATH, DEPSLIBSSPATH, filename, monitor)
		if (self._mode == "rtsp"):
			cmd = "GST_VAAPI_ALL_DRIVERS=1 GST_PLUGIN_PATH={} LD_LIBRARY_PATH={} gst-launch-1.0 -e -vvv pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse ! mp4mux name=sink ! rtpmp4vpay send-config=true ! udpsink host=127.0.0.1 port=5000 pulsesrc device=\"{}\" ! audioconvert ! lamemp3enc target=bitrate bitrate=128 cbr=true ! sink.audio_0".format(DEPSPLUGINSPATH, DEPSLIBSSPATH, monitor)

		logger.info("Command: " + cmd)
		self._recording_process = subprocess.Popen(cmd, shell = True, stdout = std_out_file, stderr = std_err_file)
		logger.info("Recording started!")
		return

	async def end_recording(self):
		logger.info("Stopping recording")
		if Plugin.is_recording(self) == False:
			logger.info("Error: No recording process to stop")
			return
		self._recording_process.send_signal(signal.SIGINT)
		self._recording_process = None
		logger.info("Recording stopped!")
		return

	async def is_recording(self):
		logger.info("Is recording? " + str(self._recording_process is not None))
		return self._recording_process is not None

	async def set_current_mode(self, mode):
		logger.info("New mode: " + mode)
		self._mode = mode

	async def current_mode(self):
		logger.info("Current mode: " + self._mode)
		return self._mode

	async def wlan_ip(self):
		ip = subprocess.getoutput("ip -f inet addr show wlan0 | sed -En -e 's/.*inet ([0-9.]+).*/\\1/p'")
		logger.info("IP: " + ip)
		return ip

	async def _main(self):
		return

	async def _unload(self):
		if Plugin.is_recording(self) == True:
			Plugin.end_recording(self)
		return