import os
import sys
import subprocess
import signal
import time
from datetime import datetime
import traceback
from pathlib import Path

DEPSPATH = "/home/deck/homebrew/plugins/decky-recorder/bin"
GSTPLUGINSPATH = DEPSPATH + "/gstreamer-1.0"
TMPLOCATION = "/tmp"

import logging

logging.basicConfig(
    filename="/tmp/decky-recorder.log",
    format="Decky Recorder: %(asctime)s %(levelname)s %(message)s",
    filemode="w+",
    force=True,
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
std_out_file = open("/tmp/decky-recorder-std-out.log", "w")
std_err_file = open("/tmp/decky-recorder-std-err.log", "w")


class Plugin:

    _recording_process = None

    _tmpFilepath: str = None
    _filepath: str = None

    _mode: str = "localFile"
    _audioBitrate: int = 128
    _localFilePath: str = "/home/deck/Videos"
    _fileformat: str = "mp4"
    _rolling: bool = False

    # Starts the capturing process
    async def start_capturing(self):
        try:
            logger.info("Starting recording")
            if Plugin.is_capturing(self) == True:
                logger.info("Error: Already recording")
                return

            os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"
            os.environ["XDG_SESSION_TYPE"] = "wayland"
            os.environ["HOME"] = "/home/deck"

            # Start command including plugin path and ld_lib path
            start_command = (
                "GST_VAAPI_ALL_DRIVERS=1 GST_PLUGIN_PATH={} LD_LIBRARY_PATH={} gst-launch-1.0 -e -vvv".format(
                    GSTPLUGINSPATH, DEPSPATH
                )
            )

            # Video Pipeline
            if not self._rolling:
                videoPipeline = "pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse ! mp4mux name=sink !"
            else:
                videoPipeline = "pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse !"

            cmd = "{} {}".format(start_command, videoPipeline)

            # If mode is localFile
            if self._mode == "localFile":
                logger.info("Local File Recording")
                dateTime = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
                if not self._rolling:
                    logger.info("Setting tmp filepath no rolling")
                    self._tmpFilepath = f"{TMPLOCATION}/Decky-Recorder_{dateTime}.{self._fileformat}"
                else:
                    logger.info("Setting tmp filepath")
                    self._tmpFilepath = f"/dev/shm/Decky-Recorder-Rolling_%02d.{self._fileformat}"
                if not self._rolling:
                    logger.info("Setting local filepath no rolling")
                    self._filepath = f"{self._localFilePath}/Decky-Recorder_{dateTime}.{self._fileformat}"
                    fileSinkPipeline = f" filesink location={self._tmpFilepath} "
                else:
                    logger.info("Setting local filepath")
                    fileSinkPipeline = " splitmuxsink name=sink muxer=mp4mux muxer-pad-map=x-pad-map,audio=vid location={} max-size-time=1000000000 max-files=480".format(
                        self._tmpFilepath
                    )
                cmd = cmd + fileSinkPipeline
            else:
                logger.info(f"Mode {self._mode} does not exist")
                return

            logger.info("Making audio pipeline")
            # Creates audio pipeline
            monitor = subprocess.getoutput("pactl get-default-sink") + ".monitor"
            cmd = (
                cmd
                + f' pulsesrc device="Recording_{monitor}" ! audioconvert ! lamemp3enc target=bitrate bitrate={self._audioBitrate} cbr=true ! sink.audio_0'
            )

            # Starts the capture process
            logger.info("Command: " + cmd)
            self._recording_process = subprocess.Popen(cmd, shell=True, stdout=std_out_file, stderr=std_err_file)
            logger.info("Recording started!")
        except Exception:
            Plugin.stop_capturing(self)
            logger.info(traceback.format_exc())
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

        if not self._rolling:
            # if recording was a local file and not rolling
            if self._mode == "localFile":
                logger.info("Repairing file")
                ffmpegCmd = f"ffmpeg -i {self._tmpFilepath} -c copy {self._filepath}"
                logger.info("Command: " + ffmpegCmd)
                self._tmpFilepath = None
                self._filepath = None
                ffmpeg = subprocess.Popen(ffmpegCmd, shell=True, stdout=std_out_file, stderr=std_err_file)
                ffmpeg.wait()
                logger.info("File copied with ffmpeg")
                os.remove(self._tmpFilepath)
                logger.info("Tmpfile deleted")
        return

    # Returns true if the plugin is currently capturing
    async def is_capturing(self):
        logger.info("Is capturing? " + str(self._recording_process is not None))
        return self._recording_process is not None

    async def is_rolling(self):
        logger.info(f"Is Rolling? {self._rolling}")
        return self._rolling

    async def enable_rolling(self):
        logger.info("Enable rolling was called begin")
        # if capturing, stop that capture, then re-enable with rolling
        was_capturing = False
        if Plugin.is_capturing(self):
            was_capturing = True
            Plugin.stop_capturing(self)
        self._rolling = True
        if was_capturing:
            Plugin.start_capturing(self)
        logger.info("Enable rolling was called end")

    async def disable_rolling(self):
        logger.info("Disable rolling was called begin")
        if Plugin.is_capturing(self):
            Plugin.stop_capturing(self)
        self._rolling = False
        logger.info("Disable rolling was called end")

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
    async def set_local_fileformat(self, fileformat: str):
        logger.info("New local file format: " + fileformat)
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
        self._fileformat = "mp4"
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
            await Plugin.stop_capturing(self)
            await Plugin.saveConfig(self)
        return

    async def save_rolling_recording(self, clip_duration: float = 30.0, prefix="/dev/shm"):
        logger.info("Called save rolling function")
        try:
            files = list(Path(prefix).glob("Decky-Recorder-Rolling*"))
            times = [os.path.getmtime(p) for p in files]
            ft = sorted(zip(files, times), key=lambda x: -x[1])
            max_time = ft[0][1] - 1
            files_to_stitch = []
            for f, ftime in ft:
                if max_time - ftime < clip_duration:
                    files_to_stitch.append(f)
            with open(prefix + "/files", "w") as ff:
                for f in reversed(files_to_stitch):
                    ff.write(f"file {str(f)}\n")

            dateTime = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            ffmpeg = subprocess.Popen(
                f"ffmpeg -f concat -safe 0 -i {prefix}/files -c copy {self._localFilePath}/Decky-Recorder-{clip_duration}s-{dateTime}.{self._fileformat}",
                shell=True,
                stdout=std_out_file,
                stderr=std_err_file,
            )
            ffmpeg.wait()

            os.remove(prefix + "/files")
            logger.info("finish save rolling function")
        except Exception:
            logger.info(traceback.format_exc())
