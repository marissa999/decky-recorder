import os
import sys
import subprocess
import signal
import sleep
from datetime import datetime

DEPSPATH = "/home/deck/homebrew/plugins/decky-recorder/backend/out"
DEPSPLUGINSPATH = DEPSPATH + "/plugins"
DEPSLIBSSPATH = DEPSPATH + "/libs"
TMPLOCATION = "/tmp/recording.mp4"

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
	_deckaudio = True
	_mic = False
	_filename = None

	async def start_recording(self):
		logger.info("Starting recording")
		if Plugin.is_recording(self) == True:
			logger.info("Error: Already recording")
			return

		os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"
		os.environ["XDG_SESSION_TYPE"] = "wayland"
		os.environ["HOME"] = "/home/deck"

		start_command = "GST_VAAPI_ALL_DRIVERS=1 GST_PLUGIN_PATH={} LD_LIBRARY_PATH={} gst-launch-1.0 -e -vvv".format(DEPSPLUGINSPATH, DEPSLIBSSPATH)

		videoPipeline = " pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse ! mp4mux name=sink !"
		adderPipeline = " adder name=audiomix ! audioconvert ! lamemp3enc target=bitrate bitrate=320 cbr=false ! sink.audio_0"

		monitor = subprocess.getoutput("pactl get-default-sink") + ".monitor"
		monitorPipeline = " pulsesrc device=\"{}\" ! audiorate ! audioconvert ! audiomix.".format(monitor)

		microphone = subprocess.getoutput("pactl get-default-source")
		microphonePipeline = " pulsesrc device=\"{}\" ! audiorate ! audioconvert ! audiomix.".format(microphone)

		cmd = None
		if (self._mode == "localFile"):
			logger.info("Local File Recording")
			self._filename = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
			# Heavily inspired by
			# https://git.sr.ht/~avery/recapture/tree/0fdbe014ec1f11bce386dc9468a760f8aed492e9/item/record.go#L19
			# https://git.sr.ht/~avery/recapture/tree/0fdbe014ec1f11bce386dc9468a760f8aed492e9/item/plugin/src/index.tsx#L161
			fileSinkPipeline = " filesink location={}".format(TMPLOCATION)
			cmd = start_command + videoPipeline + fileSinkPipeline + adderPipeline
		if (self._mode == "rtsp"):
			logger.info("RTSP-Server")
			cmd = "GST_VAAPI_ALL_DRIVERS=1 GST_PLUGIN_PATH={} LD_LIBRARY_PATH={} gst-launch-1.0 -e -vvv pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse ! mp4mux name=sink ! rtpmp4vpay send-config=true ! udpsink host=127.0.0.1 port=5000 pulsesrc device=\"{}\" ! audioconvert ! lamemp3enc target=bitrate bitrate=128 cbr=true ! sink.audio_0".format(DEPSPLUGINSPATH, DEPSLIBSSPATH, monitor)

		if (self._deckaudio):
			cmd = cmd + monitorPipeline
		if (self._mic):
			cmd = cmd + microphonePipeline

		logger.info("Command: " + cmd)
		self._recording_process = subprocess.Popen(cmd, shell = True ,stdout = std_out_file, stderr = std_err_file)
		logger.info("Recording started!")
		return

	async def end_recording(self):
		logger.info("Stopping recording")
		if Plugin.is_recording(self) == False:
			logger.info("Error: No recording process to stop")
			return
		self._recording_process.send_signal(signal.SIGINT)
		self._recording_process.wait()
		logger.info("Recording stopped!")

		# if recording was a local file
		if (self._mode == "localFile"):
			time.sleep(10)
			logger.info("Repairing file")
			permanent_location = "/home/deck/Videos/{}.mp4".format(self._filename)
			logger.info("a")
			ffmpegCmd = "ffmpeg -i {} -c copy {}".format(TMPLOCATION, permanent_location)
			logger.info("a")
			logger.info("Command: " + ffmpegCmd)
			ffmpeg = subprocess.Popen(ffmpegCmd, shell = True, stdout = std_out_file, stderr = std_err_file)
			ffmpeg.wait()
			self._filename = None
			logger.info("File repaired")
		self._recording_process = None
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

	async def set_deckaudio(self, deckaudio):
		logger.info("Set deck audio: " + str(deckaudio))
		self._deckaudio = deckaudio

	async def get_deckaudio(self):
		logger.info("Deck audio: " + str(self._deckaudio))
		return self._deckaudio

	async def set_mic(self, mic):
		logger.info("Set microphone: " + str(mic))
		self._mic = mic

	async def get_mic(self):
		logger.info("Microhone: " + str(self._mic))
		return self._mic

	async def get_wlan_ip(self):
		ip = subprocess.getoutput("ip -f inet addr show wlan0 | sed -En -e 's/.*inet ([0-9.]+).*/\\1/p'")
		logger.info("IP: " + ip)
		return ip

	async def _main(self):
		return

	async def _unload(self):
		if Plugin.is_recording(self) == True:
			Plugin.end_recording(self)
		return