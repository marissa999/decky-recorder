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
logger.setLevel(logging.INFO) # can be changed to logging.DEBUG for debugging issues

class Plugin:
    # A normal method. It can be called from JavaScript using call_plugin_function("method_1", argument1, argument2)
    async def start_recording(self):
        logger.info("Starting recording")
        p = subprocess.Popen("gst-launch-1.0 pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse ! mp4mux name=sink ! filesink location=/home/deck/Videos/test.mp4 pulsesrc device=\"echo-cancel-sink.monitor\" ! audioconvert ! lamemp3enc target=bitrate bitrate=128 cbr=true ! sink.audio_0", shell=True)
        time.sleep(3)
        logger.info("Stopping recording")
        p.send_signal(signal.SIGINT)
        pass

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        logger.info("Loading...")
        pass

    # Function called first during the unload process, utilize this to handle your plugin being removed
    async def _unload(self):
        logger.info("Unloading...")
        pass