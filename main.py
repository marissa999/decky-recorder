import os
import sys
import subprocess
import signal
import time
from datetime import datetime

DEPSPATH = "/home/deck/homebrew/plugins/decky-recorder/bin"
GSTPLUGINSPATH = DEPSPATH + "/gstreamer-1.0"
TMPLOCATION = "/tmp"

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
	_filename = None

	async def start_recording(self):
		logger.info("Starting recording")
		if Plugin.is_recording(self) == True:
			logger.info("Error: Already recording")
			return

		os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"
		os.environ["XDG_SESSION_TYPE"] = "wayland"
		os.environ["HOME"] = "/home/deck"

		start_command = "GST_VAAPI_ALL_DRIVERS=1 GST_PLUGIN_PATH={} LD_LIBRARY_PATH={} gst-launch-1.0 -e -vvv".format(GSTPLUGINSPATH, DEPSPATH)

		videoPipeline = "pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse ! mp4mux name=sink !"

		cmd = "{} {}".format(start_command, videoPipeline)
		if (self._mode == "localFile"):
			logger.info("Local File Recording")
			self._filename = datetime.now().strftime("%d-%m-%Y_%H-%M-%S") + ".mp4"
			fileSinkPipeline = " filesink location={}/{}".format(TMPLOCATION, self._filename)
			cmd = cmd + fileSinkPipeline
		if (self._mode == "rtsp"):
			logger.info("RTSP-Server")
			return

		logger.info("Command: " + cmd)
		self._recording_process = subprocess.Popen(cmd, shell = True, stdout = std_out_file, stderr = std_err_file)
		logger.info("Recording started!")
		return

	async def end_recording(self):
		logger.info("Stopping recording")
		if Plugin.is_recording(self) == False:
			logger.info("Error: No recording process to stop")
			return
		logger.info("Sending sigin")
		self._recording_process.send_signal(signal.SIGINT)
		logger.info("Sigin sent. Waiting...")
		self._recording_process.wait()
		logger.info("Waiting finished")
		self._recording_process = None
		logger.info("Recording stopped!")

		# if recording was a local file
		if (self._mode == "localFile"):
			logger.info("Repairing file")
			tmpFilePath = "{}/{}".format(TMPLOCATION, self._filename)
			permanent_location = "/home/deck/Videos/Decky-Recorder_{}".format(self._filename)
			self._filename = None
			ffmpegCmd = "ffmpeg -i {} -c copy {}".format(tmpFilePath, permanent_location)
			logger.info("Command: " + ffmpegCmd)
			ffmpeg = subprocess.Popen(ffmpegCmd, shell = True, stdout = std_out_file, stderr = std_err_file)
			ffmpeg.wait()
			logger.info("File repaired")
			os.remove(tmpFilePath)
			logger.info("Tmpfile deleted")
		return

	async def is_recording(self):
		logger.info("Is recording? " + str(self._recording_process is not None))
		return self._recording_process is not None

	async def set_current_mode(self, mode):
		logger.info("New mode: " + mode)
		self._mode = mode

	async def get_current_mode(self):
		logger.info("Current mode: " + self._mode)
		return self._mode

	async def _main(self):
		return

	async def _unload(self):
		if Plugin.is_recording(self) == True:
			Plugin.end_recording(self)
		return