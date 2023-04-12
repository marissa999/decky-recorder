import os
import sys
import traceback
import subprocess
import signal
import time
from datetime import datetime
from pathlib import Path
from settings import SettingsManager
import decky_plugin
import logging

# Get environment variable
settingsDir = os.environ["DECKY_PLUGIN_SETTINGS_DIR"]


import asyncio

DEPSPATH = Path(decky_plugin.DECKY_PLUGIN_DIR) / "backend/out"
GSTPLUGINSPATH = DEPSPATH / "gstreamer-1.0"

std_out_file = open(Path(decky_plugin.DECKY_PLUGIN_LOG_DIR) / "decky-recorder-std-out.log", "w")
std_err_file = open(Path(decky_plugin.DECKY_PLUGIN_LOG_DIR) / "decky-recorder-std-err.log", "w")

logger = decky_plugin.logger

from logging.handlers import TimedRotatingFileHandler
log_file = Path(decky_plugin.DECKY_PLUGIN_LOG_DIR) / "decky-recorder.log"
log_file_handler = TimedRotatingFileHandler(log_file, when="midnight", backupCount=2)
log_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.handlers.clear()
logger.addHandler(log_file_handler)

try:
    sys.path.append(str(DEPSPATH / "psutil"))
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

def in_gamemode():
    for child in psutil.process_iter():
        if "gamescope-session" in " ".join(child.cmdline()):
            return True
    return False

class Plugin:
    _recording_process = None
    _filepath: str = None
    _mode: str = "localFile"
    _audioBitrate: int = 192000
    _localFilePath: str = decky_plugin.HOME + "/Videos"
    _rollingRecordingFolder: str = "/dev/shm"
    _rollingRecordingPrefix: str = "Decky-Recorder-Rolling"
    _fileformat: str = "mp4"
    _rolling: bool = False
    _last_clip_time: float = time.time()
    _watchdog_task = None
    _muxer_map = {"mp4": "mp4mux", "mkv": "matroskamux", "mov": "qtmux"}
    _settings = None

    async def clear_rogue_gst_processes(self):
        gst_pids = find_gst_processes()
        curr_pid = self._recording_process.pid if self._recording_process is not None else None
        for pid in gst_pids:
            if pid != curr_pid:
                logger.info(f"Killing rogue process {pid}")
                os.kill(pid, signal.SIGKILL)

    @asyncio.coroutine
    async def watchdog(self):
        logger.info("Watchdog started")
        while True:
            try:
                in_gm = in_gamemode()
                is_cap = await Plugin.is_capturing(self, verbose=False)
                if not in_gm and is_cap:
                    logger.warn("Left gamemode but recording was still running, killing capture")
                    await Plugin.stop_capturing(self)
            except Exception:
                logger.exception("watchdog")
            await asyncio.sleep(5)

    # Starts the capturing process
    async def start_capturing(self, app_name: str = ""):
        try:
            logger.info("Starting recording")

            app_name = str(app_name)
            if app_name == "" or app_name == "null":
                app_name = "Decky-Recorder"

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
                    str(GSTPLUGINSPATH), str(DEPSPATH)
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
                if self._rolling:
                    logger.info("Setting tmp filepath")
                    self._filepath = (
                        f"{self._rollingRecordingFolder}/{self._rollingRecordingPrefix}_%02d.{self._fileformat}"
                    )
                if not self._rolling:
                    logger.info("Setting local filepath no rolling")
                    self._filepath = f"{self._localFilePath}/{app_name}_{dateTime}.{self._fileformat}"
                    fileSinkPipeline = f' filesink location="{self._filepath}" '
                else:
                    logger.info("Setting local filepath")
                    fileSinkPipeline = f" splitmuxsink name=sink muxer={muxer} muxer-pad-map=x-pad-map,audio=vid location={self._filepath} max-size-time=1000000000 max-files=480"
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
                + f' pulsesrc device="Recording_{monitor}" ! audio/x-raw, channels=2 ! audioconvert ! faac bitrate={self._audioBitrate} rate-control=2 ! sink.audio_0'
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
        proc = self._recording_process
        self._recording_process = None
        proc.send_signal(signal.SIGINT)
        logger.info("Sigin sent. Waiting...")
        try:
            proc.wait(timeout=10)
        except Exception:
            logger.warn("Could not interrupt gstreamer, killing instead")
            await Plugin.clear_rogue_gst_processes(self)
        logger.info("Waiting finished. Recording stopped!")

        return

    # Returns true if the plugin is currently capturing
    async def is_capturing(self, verbose=True):
        if verbose:
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
        await Plugin.saveConfig(self)
        logger.info("Enable rolling was called end")

    async def disable_rolling(self):
        logger.info("Disable rolling was called begin")
        if await Plugin.is_capturing(self):
            await Plugin.stop_capturing(self)
        self._rolling = False
        await Plugin.saveConfig(self)
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
        await Plugin.saveConfig(self)

    # Gets the local FilePath
    async def get_local_filepath(self):
        logger.info("Current local filepath: " + self._localFilePath)
        return self._localFilePath

    # Sets local file format
    async def set_local_fileformat(self, fileformat: str):
        logger.info("New local file format: " + fileformat)
        self._fileformat = fileformat
        await Plugin.saveConfig(self)

    # Gets the file format
    async def get_local_fileformat(self):
        logger.info("Current local file format: " + self._fileformat)
        return self._fileformat

    async def loadConfig(self):
        logger.info('Loading settings from: {}'.format(os.path.join(settingsDir, 'settings.json')))
        ### TODO: IMPLEMENT ###
        self._settings = SettingsManager(name="decky-loader-settings", settings_directory=settingsDir)
        self._settings.read()
        self._mode = "localFile"
        self._audioBitrate = 192000

        self._localFilePath = self._settings.getSetting("output_folder", "/home/deck/Videos")
        self._fileformat = self._settings.getSetting("format", "mp4")
        self._rolling = self._settings.getSetting("rolling", False)

        # Need this for initialization only honestly
        await Plugin.saveConfig(self)
        return

    async def saveConfig(self):
        logger.info("Saving config")
        self._settings.setSetting("format", self._fileformat)
        self._settings.setSetting("output_folder", self._localFilePath)
        self._settings.setSetting("rolling", self._rolling)
        return

    async def _main(self):
        loop = asyncio.get_event_loop()
        self._watchdog_task = loop.create_task(Plugin.watchdog(self))
        await Plugin.loadConfig(self)
        if self._rolling:
            await Plugin.start_capturing(self)
        return

    async def _unload(self):
        logger.info("Unload was called")
        if await Plugin.is_capturing(self) == True:
            logger.info("Cleaning up")
            await Plugin.stop_capturing(self)
            await Plugin.saveConfig(self)
        return

    async def save_rolling_recording(self, clip_duration: float = 30.0, app_name: str = ""):
        app_name = str(app_name)
        if app_name == "" or app_name == "null":
            app_name = "Decky-Recorder"
        clip_duration = int(clip_duration)
        logger.info("Called save rolling function")
        if time.time() - self._last_clip_time < 2:
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
                f'ffmpeg -hwaccel vaapi -hwaccel_output_format vaapi -vaapi_device /dev/dri/renderD128 -f concat -safe 0 -i {self._rollingRecordingFolder}/files -c copy "{self._localFilePath}/{app_name}-{clip_duration}s-{dateTime}.{self._fileformat}"',
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
