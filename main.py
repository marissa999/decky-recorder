import os
import sys
import traceback
import subprocess
import signal
import time
from datetime import datetime
from pathlib import Path
from settings import SettingsManager
import asyncio
import decky_plugin

# Get environment variable
settingsDir = os.environ["DECKY_PLUGIN_SETTINGS_DIR"]

DEPSPATH = Path(decky_plugin.DECKY_PLUGIN_DIR) / "backend/out"
GSTPLUGINSPATH = DEPSPATH / "gstreamer-1.0"
START_COMMAND = f"GST_VAAPI_ALL_DRIVERS=1 GST_PLUGIN_PATH={GSTPLUGINSPATH} LD_LIBRARY_PATH={DEPSPATH} gst-launch-1.0 -e -vvv"

std_out_file = open(Path(decky_plugin.DECKY_PLUGIN_LOG_DIR) / "decky-recorder-std-out.log", "w")
std_err_file = open(Path(decky_plugin.DECKY_PLUGIN_LOG_DIR) / "decky-recorder-std-err.log", "w")

logger = decky_plugin.logger

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

    # Options
    _localFilePath: str = "/home/deck/Videos"
    _mode: str = "localFile"
    _fileformat: str = "mp4"
    _bufferLength: int = 30
    _audioBitrate: int = 192000
    _replaymode_autostart: bool = False

    _watchdog_task = None
    _muxer_map = {"mp4": "mp4mux", "mkv": "matroskamux", "mov": "qtmux"}
    _settings = None

    async def clear_rogue_gst_processes(self):
        gst_pids = find_gst_processes()
        record_pid = self._local_file_recording_process.pid if self._local_file_recording_process is not None else None
        rolling_pid = self._rolling_process.pid if self._rolling_process is not None else None
        for pid in gst_pids:
            if pid != record_pid and pid != rolling_pid:
                logger.info(f"Killing rogue process {pid}")
                os.kill(pid, signal.SIGKILL)

    @asyncio.coroutine
    async def watchdog(self):
        print("in watchdog")
        while True:
            print("watchdog ping")
            try:
                in_gm = in_gamemode()
                is_cap = await Plugin.is_capturing(self)
                print(in_gm, is_cap)
                if not in_gm and is_cap:
                    await Plugin.stop_capturing(self)
            except Exception:
                logger.exception("watchdog")
            await asyncio.sleep(5)

    ###################
    # Local file mode #
    ###################
    _local_file_recording_process = None

    # start local file recording
    async def start_local_file_recording(self):
        try:
            logger.info("Starting local file recording recording")

            if await Plugin.is_local_file_recording(self) is True:
                logger.info("Error: Already recording")
                return

            videoPipeline = Plugin.video_pipeline(self._fileformat)

            # Filesink Pipeline
            dateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            fullFilePath = f"{self._localFilePath}/Decky-Recorder_{dateTime}.{self._fileformat}"
            fileSinkPipeline = f"filesink location={fullFilePath}"

            audioPipeline = Plugin.audio_pipeline(self._audioBitrate)

            self._local_file_recording_process = Plugin.start_proces(
                f"{videoPipeline} ! {fileSinkPipeline} {audioPipeline}")
            logger.info("Recording started!")
        except Exception:
            await Plugin.stop_local_file_recording(self)
            logger.info(traceback.format_exc())
        return

    # Stops the capturing process and cleans up if the mode requires
    async def stop_local_file_recording(self):
        logger.info("Stopping local file recording")
        if await Plugin.is_local_file_recording(self) is False:
            logger.info("Error: No local file recording process to stop")
            return
        Plugin.stop_process(self._local_file_recording_process)
        self._local_file_recording_process = None
        logger.info("Local file recording stopped!")
        return

    async def is_local_file_recording(self):
	    return self._local_file_recording_process is not None

    ###############
    # Replay mode #
    ###############
    _rolling_process = None
    _last_clip_time: float = time.time()
    ROLLINGRECORDINGFOLDER: str = "/dev/shm"
    ROLLINGRECORDINGPREFIX: str = "Decky-Recorder-Rolling"

    async def enable_rolling(self):
        logger.info("Enable rolling was called begin")
        # if capturing, stop that capture, then re-enable with rolling
        if await Plugin.is_rolling(self):
            await Plugin.disable_rolling(self)
        try:
            logger.info("Starting replay")
            if await Plugin.is_rolling(self) == True:
                logger.info("Error: Already recording")
                return
            await Plugin.clear_rogue_gst_processes(self)

            videoPipeline = Plugin.video_pipeline(None)

            # Splitmux Pipeline
            logger.info("Setting local filepath")
            filepath = f"{Plugin.ROLLINGRECORDINGFOLDER}/{Plugin.ROLLINGRECORDINGPREFIX}_%02d.{self._fileformat}"
            muxer = Plugin._muxer_map.get(self._fileformat, "mp4mux")
            splitmuxPipeline = f"splitmuxsink name=sink muxer={muxer} muxer-pad-map=x-pad-map,audio=vid location={filepath} max-size-time=1000000000 max-files=480"

            audioPipeline = Plugin.audio_pipeline(self._audioBitrate)

            self._rolling_process = Plugin.start_proces(
                f"{videoPipeline} ! {splitmuxPipeline} {audioPipeline}")
            logger.info("Replay started!")
        except Exception:
            await Plugin.disable_rolling(self)
            logger.info(traceback.format_exc())
        logger.info("Enable rolling was called end")

    # Stops the capturing process and cleans
    async def disable_rolling(self):
        logger.info("Disable rolling was called begin")
        if await Plugin.is_rolling(self):
            logger.info("Stopping replay")
            Plugin.stop_process(self._rolling_process)
            self._rolling_process = None
        try:
            for path in list(Path(Plugin.ROLLINGRECORDINGFOLDER).glob(f"{Plugin.ROLLINGRECORDINGPREFIX}*")):
                os.remove(str(path))
            logger.info("Deleted all files in rolling buffer")
        except Exception:
            logger.exception("Failed to delete rolling recording buffer files")
        await Plugin.saveConfig(self)
        logger.info("Disable rolling was called end")

    async def save_rolling_recording(self, clip_duration: float = 30.0):
        clip_duration = int(clip_duration)
        logger.info("Called save rolling function")
        if time.time() - self._last_clip_time < 5:
            logger.info("Too early to record another clip")
            return 0
        try:
            clip_duration = float(clip_duration)
            files = list(Path(Plugin.ROLLINGRECORDINGFOLDER).glob(f"{Plugin.ROLLINGRECORDINGPREFIX}*.{self._fileformat}"))
            times = [os.path.getctime(p) for p in files]
            ft = sorted(zip(files, times), key=lambda x: -x[1])
            max_time = time.time()
            files_to_stitch = []
            actual_dur = 0.0
            for f, ftime in ft:
                if max_time - ftime <= clip_duration:
                    actual_dur = max_time - ftime
                    files_to_stitch.append(f)
            with open(Plugin.ROLLINGRECORDINGFOLDER + "/files", "w") as ff:
                for f in reversed(files_to_stitch):
                    ff.write(f"file {str(f)}\n")

            dateTime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            ffmpeg = subprocess.Popen(
                f"ffmpeg -sseof -{clip_duration} -hwaccel vaapi -hwaccel_output_format vaapi -vaapi_device /dev/dri/renderD128 -f concat -safe 0 -i {Plugin.ROLLINGRECORDINGFOLDER}/files -c copy {self._localFilePath}/Decky-Recorder-{clip_duration}s-{dateTime}.{self._fileformat}",
                shell=True,
                stdout=std_out_file,
                stderr=std_err_file,
            )
            ffmpeg.wait()
            os.remove(Plugin.ROLLINGRECORDINGFOLDER + "/files")
            self._last_clip_time = time.time()
            logger.info("finish save rolling function")
            return int(actual_dur)
        except Exception:
            logger.info(traceback.format_exc())
        return -1

    async def is_rolling(self):
	    return self._rolling_process is not None

    ###########
    # General #
    ###########

    async def is_capturing(self):
        if Plugin.is_local_file_recording(self) is True:
            return True
        if Plugin.is_local_file_recording(self) is True:
            return True
        return False

    async def stop_capturing(self):
        if Plugin.is_local_file_recording(self) is True:
            await Plugin.stop_local_file_recording(self)
        if Plugin.is_local_file_recording(self) is True:
            return Plugin.disable_rolling(self)

    #############
    # Gstreamer #
    #############

    def video_pipeline(muxer: str):
        logger.info("Making video pipeline")
        videoPipeline = "pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse"
        if muxer is not None:
            mux = Plugin._muxer_map.get(muxer, "mp4mux")
            videoPipeline = f"{videoPipeline} ! {mux} name=sink"
        return videoPipeline

    def audio_pipeline(audioBitrate: int):
        logger.info("Making audio pipeline")
        audio_device_output = subprocess.getoutput("pactl get-default-sink")
        logger.info(f"Audio device output {audio_device_output}")
        for line in audio_device_output.split("\n"):
            if "alsa_output" in line:
                monitor = line + ".monitor"
                break
        audioPipeline = f"pulsesrc device=\"Recording_{monitor}\" ! audio/x-raw, channels=2 ! audioconvert ! faac bitrate={self._audioBitrate} rate-control=2 ! sink.audio_0"
        return audioPipeline

    def start_proces(pipeline: str):
        cmd = f"{START_COMMAND} {pipeline}"
        logger.info("Command: " + cmd)
        return subprocess.Popen(cmd, shell=True, stdout=std_out_file, stderr=std_err_file)

    async def stop_process(process):
        logger.info("Sending sigint")
        process.send_signal(signal.SIGINT)
        logger.info("Sigint sent. Waiting...")
        try:
            process.wait(timeout=10)
        except Exception:
            logger.warn("Could not interrupt gstreamer, killing instead")
            process.kill()
        logger.info("Waiting finished. Recording stopped!")

    ###########
    # Options #
    ###########

    # Sets the current mode, supported modes are: localFile
    async def set_current_mode(self, mode: str):
        logger.info("New mode: " + mode)
        self._mode = mode
        await Plugin.saveConfig(self)

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

    # Sets local file format
    async def set_buffer_length(self, bufferLength: int):
        logger.info("New buffer length: " + bufferLength)
        self._bufferLength = bufferLength
        await Plugin.saveConfig(self)

    # Gets the file format
    async def get_buffer_length(self):
        logger.info("Current buffer length: " + self._bufferLength)
        return self._bufferLength

    # Sets rolling autostart
    async def set_replaymode_autostart(self, replaymode_autostart: bool):
        logger.info("New rolling autostart: " + replaymode_autostart)
        self._replaymode_autostart = replaymode_autostart
        await Plugin.saveConfig(self)

    # Gets rolling autostart
    async def get_replaymode_autostart(self):
        logger.info("Current rolling autostart: " + self._replaymode_autostart)
        return self._replaymode_autostart

    async def loadConfig(self):
        logger.info('Loading settings from: {}'.format(os.path.join(settingsDir, 'settings.json')))
        self._settings = SettingsManager(name="decky-loader-settings", settings_directory=settingsDir)
        self._settings.read()

        self._localFilePath = self._settings.getSetting("output_folder", "/home/deck/Videos")
        self._fileformat = self._settings.getSetting("format", "mp4")
        self._mode = self._settings.getSetting("mode", "localFile")
        self._replaymode_autostart = self._settings.getSetting("replay_autostart", False)
        self._audioBitrate = self._settings.getSetting("audioBitrate", 192000)
        self._bufferLength = self._settings.getSetting("bufferLength", 30)

        # Need this for initialization only honestly
        await Plugin.saveConfig(self)
        return

    async def saveConfig(self):
        logger.info("Saving config")
        self._settings.setSetting("format", self._fileformat)
        self._settings.setSetting("output_folder", self._localFilePath)
        self._settings.setSetting("mode", self._mode)
        self._settings.setSetting("audioBitrate", self._audioBitrate)
        self._settings.setSetting("bufferLength", self._bufferLength)
        self._settings.setSetting("replay_autostart", self._replaymode_autostart)
        return

    #########
    # Other #
    #########

    async def _main(self):
        os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"
        os.environ["XDG_SESSION_TYPE"] = "wayland"
        os.environ["HOME"] = "/home/deck"
        loop = asyncio.get_event_loop()
        self._watchdog_task = loop.create_task(Plugin.watchdog(self))
        await Plugin.loadConfig(self)
        if self._replaymode_autostart is True:
            await Plugin.set_current_mode(self, "replayMode")
            await Plugin.enable_rolling(self)
        return

    async def _unload(self):
        logger.info("Unload was called")
        await Plugin.clear_rogue_gst_processes(self)
        await Plugin.saveConfig(self)
        return