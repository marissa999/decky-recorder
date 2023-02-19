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
	_mode: str = "localFile"
	_audioBitrate: int = 128
	_localFilePath: str = "/home/deck/Videos"
	_filename: str = None
	_fileformat: str = "mp4"

	# Starts the capturing process
	async def start_capturing(self):
		logger.info("Starting recording")
		if Plugin.is_capturing(self) == True:
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

		# If mode is localFile
		if (self._mode == "localFile"):
			logger.info("Local File Recording")
			self._filename = datetime.now().strftime("%d-%m-%Y_%H-%M-%S") + ".mp4"
			fileSinkPipeline = " filesink location={}/{}".format(TMPLOCATION, self._filename)
			cmd = cmd + fileSinkPipeline
		else:
			logger.info("Mode {} does not exist".format(self._mode))
			return

		# Creates audio pipeline
		monitor = subprocess.getoutput("pactl get-default-sink") + ".monitor"
		cmd = cmd + " pulsesrc device=\"Recording_{}\" ! audioconvert ! lamemp3enc target=bitrate bitrate={} cbr=true ! sink.audio_0".format(monitor, self._audioBitrate)

		# Starts the capture process
		logger.info("Command: " + cmd)
		self._recording_process = subprocess.Popen(cmd, shell = True, stdout = std_out_file, stderr = std_err_file)
		logger.info("Recording started!")
		return

	# Stops the capturing process and cleans up if the mode requires
	async def stop_capturing(self):
		logger.info("Stopping recording")
		if Plugin.is_capturing(self) == False:
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
			permanent_location = "{}/Decky-Recorder_{}".format(self._localFilePath ,self._filename)
			self._filename = None
			ffmpegCmd = "ffmpeg -i {} -c copy {}".format(tmpFilePath, permanent_location)
			logger.info("Command: " + ffmpegCmd)
			ffmpeg = subprocess.Popen(ffmpegCmd, shell = True, stdout = std_out_file, stderr = std_err_file)
			ffmpeg.wait()
			logger.info("File repaired")
			os.remove(tmpFilePath)
			logger.info("Tmpfile deleted")
		return

	# Returns true if the plugin is currently capturing
	async def is_capturing(self):
		logger.info("Is capturing? " + str(self._recording_process is not None))
		return self._recording_process is not None

	# Sets the current mode, supported modes are: localFile
	async def set_current_mode(self, mode: str):
		logger.info("New mode: " + mode)
		self._mode = mode

	# Gets the current mode
	async def get_current_mode(self):
		logger.info("Current mode: " + self._mode)
		return self._mode

	# Sets audio bitrate
	async def set_audio_bitrate(self, aduioBitrate: int):
		logger.info("New audio bitrate: " + aduioBitrate)
		self._audioBitrate = aduioBitrate

	# Gets the audio bitrate
	async def get_audio_bitrate(self):
		logger.info("Current audio bitrate: " + self._audioBitrate)
		return self._audioBitrate

	# Sets local FilePath
	async def set_local_filepath(self, localFilePath: str):
		logger.info("New local filepath: " + localFilePath)
		self._localFilePath = localFilePath

	# Gets the local FilePath
	async def get_local_filepath(self):
		logger.info("Current local filepath: " + self._localFilePath)
		return self._localFilePath

	# Sets local file format
	async def set_local_fileformat(self, _fileformat: str):
		logger.info("New local file format: " + _fileformat)
		self._fileformat = fileformat

	# Gets the file format
	async def get_local_fileformat(self):
		logger.info("Current local file format: " + self._fileformat)
		return self._fileformat

	async def loadConfig(self):
		logger.info("Loading config")
		### TODO: IMPLEMENT ###
		self._mode = "localFile"
		self._audioBitrate = 128
		self._localFilePath = "/home/deck/Videos"
		self._fileformat = "/home/deck/Videos"
		return

	async def saveConfig(self):
		logger.info("Saving config")
		### TODO: IMPLEMENT ###
		return

	async def _main(self):
		await Plugin.loadConfig(self)
		return

	async def _unload(self):
		if Plugin.is_capturing(self) == True:
			await Plugin.end_recording(self)
		await Plugin.saveConfig(self)
		return