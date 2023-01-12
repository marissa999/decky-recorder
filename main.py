import os
import sys
import subprocess
import time

# append py_modules to PYTHONPATH
sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/py_modules")

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

	recording_process = None

	async def start_recording(self):
		logger.info("Starting recording")
		if self.recording_process is not None:
			logger.info("Error: recording already started")
			pass
		self.recording_process = subprocess.Popen("gst-launch-1.0 pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse ! mp4mux name=sink ! filesink location=/home/deck/Videos/test.mp4 pulsesrc device=\"echo-cancel-sink.monitor\" ! audioconvert ! lamemp3enc target=bitrate bitrate=128 cbr=true ! sink.audio_0", shell = True, stdout = std_out_file, stderr = std_err_file)
		pass

	async def end_recording(self):
		logger.info("Stopping recording")
		if self.recording_process is None:
			logger.info("Error: No recording process to stop")
			pass
        self.recording_process.send_signal(signal.SIGINT)
        self.recording_process = None
		pass

	async def _main(self):
		logger.info("Loading...")
		pass

	async def _unload(self):
		logger.info("Unloading...")
		if self.recording_process is not None:
			Plugin.end_recording(self)
		pass