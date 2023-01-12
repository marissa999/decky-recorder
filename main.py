import os
import sys
import subprocess
import time

# append py_modules to PYTHONPATH
sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/py_modules")

import logging

logging.basicConfig(filename="/tmp/template.log",
                    format='Decky Recorder: %(asctime)s %(levelname)s %(message)s',
                    filemode='w+',
                    force=True)
logger=logging.getLogger()
logger.setLevel(logging.DEBUG)

class Plugin:

    recording_process = None

    async def start_recording(self):
        logger.info("Starting recording")
        if self.recording_process is not None:
            logger.info("Error: recording already started")
            pass
        self.recording_process = subprocess.Popen("gst-launch-1.0 pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse ! mp4mux name=sink ! filesink location=/home/deck/Videos/test.mp4 pulsesrc device=\"echo-cancel-sink.monitor\" ! audioconvert ! lamemp3enc target=bitrate bitrate=128 cbr=true ! sink.audio_0", shell=True)
        pass

    async def end_recording(self):
        logger.info("Stopping recording")
        if self.recording_process is None:
            logger.info("Error: No recording process to stop")
            pass
        self.recording_process.send_signal(signal.SIGINT)
        self.recording_process = None
        pass

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        logger.info("Loading...")
        pass

    # Function called first during the unload process, utilize this to handle your plugin being removed
    async def _unload(self):
        logger.info("Unloading...")
        if self.recording_process is None:
            Plugin.end_recording(self)
        pass