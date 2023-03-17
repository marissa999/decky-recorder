import os
import sys
import traceback
import subprocess
import signal
import time
from datetime import datetime
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

try:
    sys.path.append("/home/deck/homebrew/plugins/decky-recorder/bin/psutil")
    import psutil
    logger.info("Successfully loaded psutil")
except Exception:
    logger.info(traceback.format_exc())


def find_gst_processes():
    pids = []
    for child in psutil.process_iter():
        if "Decky-Recorder" in " ".join(child.cmdline()):
            pids.append(child.pid)
    return pids


class Plugin:
    _recording_process = None

    _tmpFilepath: str = None
    _filepath: str = None

    _mode: str = "localFile"
    _audioBitrate: int = 128
    _localFilePath: str = "/home/deck/Videos"
    _rollingRecordingFolder: str = "/dev/shm"
    _rollingRecordingPrefix: str = "Decky-Recorder-Rolling"
    _fileformat: str = "mp4"
    _rolling: bool = False
    _last_clip_time: float = time.time()
    _muxer_map = {"mp4": "mp4mux", "mkv": "matroskamux", "mov": "qtmux"}

    async def clear_rogue_gst_processes(self):
        gst_pids = find_gst_processes()
        curr_pid = self._recording_process.pid if self._recording_process is not None else None
        for pid in gst_pids:
            if pid != curr_pid:
                logger.info(f"Killing rogue process {pid}")
                os.kill(pid, signal.SIGKILL)

    # Starts the capturing process
    async def start_capturing(self):
        try:
            logger.info("Starting recording")
            muxer = Plugin._muxer_map.get(self._fileformat, "mp4mux")
            logger.info(f"Starting recording for {self._fileformat} with mux {muxer}")
            if await Plugin.is_capturing(self) == True:
                logger.info("Error: Already recording")
                return

            await Plugin.clear_rogue_gst_processes(self)

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
                videoPipeline = f"pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse ! {muxer} name=sink !"
            else:
                videoPipeline = "pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse !"

            cmd = "{} {}".format(start_command, videoPipeline)

            # If mode is localFile
            if self._mode == "localFile":
                logger.info("Local File Recording")
                dateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                if not self._rolling:
                    logger.info("Setting tmp filepath no rolling")
                    self._tmpFilepath = f"{TMPLOCATION}/Decky-Recorder_{dateTime}.{self._fileformat}"
                else:
                    logger.info("Setting tmp filepath")
                    self._tmpFilepath = f"{self._rollingRecordingFolder}/{self._rollingRecordingPrefix}_%02d.{self._fileformat}"
                if not self._rolling:
                    logger.info("Setting local filepath no rolling")
                    self._filepath = f"{self._localFilePath}/Decky-Recorder_{dateTime}.{self._fileformat}"
                    fileSinkPipeline = f" filesink location={self._tmpFilepath} "
                else:
                    logger.info("Setting local filepath")
                    fileSinkPipeline = f" splitmuxsink name=sink muxer={muxer} muxer-pad-map=x-pad-map,audio=vid location={self._tmpFilepath} max-size-time=2000000000 max-files=240"
                cmd = cmd + fileSinkPipeline
            else:
                logger.info(f"Mode {self._mode} does not exist")
                return

            logger.info("Making audio pipeline")
            # Creates audio pipeline
            audio_device_output = subprocess.getoutput("pactl get-default-sink")
            logger.info(f"Audio device output {audio_device_output}")
            for line in audio_device_output.split("\n"):
                if "alsa_output" in line:
                    monitor = line + ".monitor"
                    break
            cmd = (
                cmd
                + f' pulsesrc device="Recording_{monitor}" ! audioconvert ! lamemp3enc target=bitrate bitrate={self._audioBitrate} cbr=true ! sink.audio_0'
            )

            # Starts the capture process
            logger.info("Command: " + cmd)
            self._recording_process = subprocess.Popen(cmd, shell=True, stdout=std_out_file, stderr=std_err_file)
            logger.info("Recording started!")
        except Exception:
            await Plugin.stop_capturing(self)
            logger.info(traceback.format_exc())
        return

    # Stops the capturing process and cleans up if the mode requires
    async def stop_capturing(self):
        logger.info("Stopping recording")
        if await Plugin.is_capturing(self) == False:
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
                ffmpeg = subprocess.Popen(ffmpegCmd, shell=True, stdout=std_out_file, stderr=std_err_file)
                ffmpeg.wait()
                logger.info("File copied with ffmpeg")
                try:
                    os.remove(self._tmpFilepath)
                    logger.info("Tmpfile deleted")
                except Exception:
                    logger.error("Could not delete tmp file" + traceback.format_exc())
                self._tmpFilepath = None
                self._filepath = None
        return

    # Returns true if the plugin is currently capturing
    async def is_capturing(self):
        logger.info("Is capturing? " + str(self._recording_process is not None))
        return self._recording_process is not None

    async def is_rolling(self):
        logger.info(f"Is Rolling? {self._rolling}")
        await Plugin.clear_rogue_gst_processes(self)
        return self._rolling

    async def enable_rolling(self):
        logger.info("Enable rolling was called begin")
        # if capturing, stop that capture, then re-enable with rolling
        if await Plugin.is_capturing(self):
            await Plugin.stop_capturing(self)
        self._rolling = True
        await Plugin.start_capturing(self)
        logger.info("Enable rolling was called end")

    async def disable_rolling(self):
        logger.info("Disable rolling was called begin")
        if await Plugin.is_capturing(self):
            await Plugin.stop_capturing(self)
        self._rolling = False
        try:
            for path in list(Path(self._rollingRecordingFolder).glob(f"{self._rollingRecordingPrefix}*")):
                os.remove(str(path))
            logger.info("Deleted all files in rolling buffer")
        except Exception:
            logger.exception("Failed to delete rolling recording buffer files")
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
    async def set_audio_bitrate(self, audioBitrate: int):
        logger.info(f"New audio bitrate: {audioBitrate}")
        self._audioBitrate = audioBitrate

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
        logger.info("Unload was called")
        if await Plugin.is_capturing(self) == True:
            logger.info("Cleaning up")
            await Plugin.stop_capturing(self)
            await Plugin.saveConfig(self)
        return

    async def save_rolling_recording(self, clip_duration: float = 30.0):
        clip_duration = int(clip_duration)
        logger.info("Called save rolling function")
        if time.time() - self._last_clip_time < 5:
            logger.info("Too early to record another clip")
            return 0
        try:
            clip_duration = float(clip_duration)
            files = list(Path(self._rollingRecordingFolder).glob(f"{self._rollingRecordingPrefix}*.{self._fileformat}"))
            times = [os.path.getctime(p) for p in files]
            ft = sorted(zip(files, times), key=lambda x: -x[1])
            max_time = time.time()
            files_to_stitch = []
            actual_dur = 0.0
            for f, ftime in ft:
                if max_time - ftime <= clip_duration:
                    actual_dur = max_time - ftime
                    files_to_stitch.append(f)
            with open(self._rollingRecordingFolder + "/files", "w") as ff:
                for f in reversed(files_to_stitch):
                    ff.write(f"file {str(f)}\n")

            dateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            ffmpeg = subprocess.Popen(
                f"ffmpeg -sseof -{clip_duration} -hwaccel vaapi -hwaccel_output_format vaapi -vaapi_device /dev/dri/renderD128 -f concat -safe 0 -i {self._rollingRecordingFolder}/files -c copy {self._localFilePath}/Decky-Recorder-{clip_duration}s-{dateTime}.{self._fileformat}",
                shell=True,
                stdout=std_out_file,
                stderr=std_err_file,
            )
            ffmpeg.wait()
            os.remove(self._rollingRecordingFolder + "/files")
            self._last_clip_time = time.time()
            logger.info("finish save rolling function")
            return int(actual_dur)
        except Exception:
            logger.info(traceback.format_exc())
        return -1
