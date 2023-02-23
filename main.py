import os
import sys
import subprocess
import signal
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

	_mode: str = "localFile"
	_tmpFilepath: str = None
	_filepath: str = None

	# Starts the recording process
	async def start_recording(self, mode: str, localFilePath: str, fileformat: str):
		logger.info("Starting recording")
		if self._recording_process is not None:
			logger.info("Error: Already recording")
			return

		os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"
		os.environ["XDG_SESSION_TYPE"] = "wayland"
		os.environ["HOME"] = "/home/deck"

		# Start command including plugin path and ld_lib path
		start_command = "GST_VAAPI_ALL_DRIVERS=1 GST_PLUGIN_PATH={} LD_LIBRARY_PATH={} gst-launch-1.0 -e -vvv".format(GSTPLUGINSPATH, DEPSPATH)

		# Video Pipeline
		videoPipeline = "pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse ! mp4mux name=sink !"
		cmd = "{} {}".format(start_command, videoPipeline)

		self._mode = mode
		# If mode is localFile
		if (self._mode == "localFile"):
			logger.info("Local File Recording")
			dateTime = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
			self._tmpFilepath = "{}/Decky-Recorder_{}.mp4".format(TMPLOCATION, dateTime)
			self._filepath = "{}/Decky-Recorder_{}.{}".format(localFilePath, dateTime, fileformat)
			fileSinkPipeline = " filesink location={}".format(self._tmpFilepath)
			cmd = cmd + fileSinkPipeline
		else:
			logger.info("Mode {} does not exist".format(mode))
			return

		# Creates audio pipeline
		monitor = subprocess.getoutput("pactl get-default-sink") + ".monitor"
		cmd = cmd + " pulsesrc device=\"Recording_{}\" ! audioconvert ! lamemp3enc target=bitrate bitrate=128 cbr=true ! sink.audio_0".format(monitor)

		# Starts the recorde process
		logger.info("Command: " + cmd)
		self._recording_process = subprocess.Popen(cmd, shell = True, stdout = std_out_file, stderr = std_err_file)
		logger.info("Recording started!")
		return

	# Stops the recording process and cleans up if the mode requires
	async def stop_recording(self):
		logger.info("Stopping recording")
		if self._recording_process is None:
			logger.info("Error: No recording process to stop")
			return
		logger.info("Sending sigint")
		self._recording_process.send_signal(signal.SIGINT)
		logger.info("Sigint sent. Waiting...")
		self._recording_process.wait()
		logger.info("Waiting finished")
		self._recording_process = None
		logger.info("Recording stopped!")

		# if recording was a local file
		if (self._mode == "localFile"):
			logger.info("Repairing file")
			ffmpegCmd = "ffmpeg -i {} -c copy {}".format(self._tmpFilepath, self._filepath)
			logger.info("Command: " + ffmpegCmd)
			self._tmpFilepath = None
			self._filepath = None
			ffmpeg = subprocess.Popen(ffmpegCmd, shell = True, stdout = std_out_file, stderr = std_err_file)
			ffmpeg.wait()
			logger.info("File copied with ffmpeg")
			os.remove(self._tmpFilepath)
			logger.info("Tmpfile deleted")
		return

	async def _main(self):
		return

	async def _unload(self):
		if self._recording_process is not None:
			await Plugin.end_recording(self)
		await Plugin.saveConfig(self)
		return