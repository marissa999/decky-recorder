import os
import sys
import subprocess
import signal
from datetime import datetime

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

DEPSPATH = "/home/deck/.decky-recorder-deps"

DEPSPLUGINSPATH = DEPSPATH + "/plugins"

VAAPIPATH = DEPSPLUGINSPATH + "/vaapi"
PIPEWIREPATH = DEPSPLUGINSPATH + "/pipewire"
BADPATH = DEPSPLUGINSPATH + "/bad"
GOODPATH = DEPSPLUGINSPATH + "/good"

DEPSLIBSSPATH = DEPSPATH + "/libs"

class Plugin:

	recording_process = None
	deps_installed = False

	async def start_recording(self):
		logger.info("Starting recording")
		if self.recording_process is not None:
			logger.info("Error: Already recording")
			return
		if Plugin.check_if_deps_installed(self) == False:
			logger.info("Error: Dependencies not installed")
			return
		os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"
		os.environ["XDG_SESSION_TYPE"] = "wayland"
		os.environ["HOME"] = "/home/deck"
		# Heavily inspired by
		# https://git.sr.ht/~avery/recapture/tree/0fdbe014ec1f11bce386dc9468a760f8aed492e9/item/record.go#L19
		# https://git.sr.ht/~avery/recapture/tree/0fdbe014ec1f11bce386dc9468a760f8aed492e9/item/plugin/src/index.tsx#L161
		filename = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
		monitor = subprocess.getoutput("pactl get-default-sink") + ".monitor"
		cmd = "GST_VAAPI_ALL_DRIVERS=1 GST_PLUGIN_PATH={} LD_LIBRARY_PATH={} gst-launch-1.0 -e -vvv pipewiresrc do-timestamp=true ! vaapipostproc ! queue ! vaapih264enc ! h264parse ! mp4mux name=sink ! filesink location=/home/deck/Videos/{}.mp4 pulsesrc device=\"{}\" ! audioconvert ! lamemp3enc target=bitrate bitrate=128 cbr=true ! sink.audio_0".format(DEPSPLUGINSPATH, DEPSLIBSSPATH, filename, monitor)
		logger.info("Launch command: " + cmd)
		self.recording_process = subprocess.Popen(cmd, shell = True, stdout = std_out_file, stderr = std_err_file)
		logger.info("Started recording!")
		pass

	async def end_recording(self):
		logger.info("Stopping recording")
		if self.recording_process is None:
			logger.info("Error: No recording process to stop")
			pass
		self.recording_process.send_signal(signal.SIGINT)
		self.recording_process = None
		pass

	async def is_recording(self):
		return self.recording_process is not None

	async def install_deps(self):
		logger.info("Installing dependencies")
		# Heavily inspired by https://git.sr.ht/~avery/recapture/tree/0fdbe014ec1f11bce386dc9468a760f8aed492e9/item/plugin/Makefile#L22
		os.mkdir(DEPSPATH)
		os.mkdir(DEPSPLUGINSPATH)
		os.mkdir(VAAPIPATH)
		os.mkdir(PIPEWIREPATH)
		os.mkdir(GOODPATH)
		os.mkdir(DEPSLIBSSPATH)
		os.mkdir(BADPATH)
		TMP_DEPS_PATH = "/tmp/deps"
		os.mkdir(TMP_DEPS_PATH)
		GST_VAAPI_DL = "https://steamdeck-packages.steamos.cloud/archlinux-mirror/extra-3.3/os/x86_64/gstreamer-vaapi-1.18.5-1-x86_64.pkg.tar.zst"
		GST_PLUGIN_PIPEWIRE_DL = "https://steamdeck-packages.steamos.cloud/archlinux-mirror/extra-3.3/os/x86_64/gst-plugin-pipewire-1%3A0.3.44-1-x86_64.pkg.tar.zst"
		GST_PLUGIN_BAD_LIBS_DL = "https://steamdeck-packages.steamos.cloud/archlinux-mirror/extra-3.3/os/x86_64/gst-plugins-bad-libs-1.18.5-5-x86_64.pkg.tar.zst"
		GST_PLUGIN_GOOD_DL = "https://steamdeck-packages.steamos.cloud/archlinux-mirror/extra-3.3/os/x86_64/gst-plugins-good-1.18.5-2-x86_64.pkg.tar.zst"
		VAAPIZSTPATH = TMP_DEPS_PATH + "/vaapi.pkg.tar.zst"
		PIPEWIREZSTPATH = TMP_DEPS_PATH + "/pipewire.pkg.tar.zst"
		BADLIBSZSTPATH = TMP_DEPS_PATH + "/bad-libs.pkg.tar.zst"
		GOODZSTPATH = TMP_DEPS_PATH + "/good.pkg.tar.zst"
		os.system("wget -O {} {}".format(VAAPIZSTPATH, GST_VAAPI_DL))
		os.system("wget -O {} {}".format(PIPEWIREZSTPATH, GST_PLUGIN_PIPEWIRE_DL))
		os.system("wget -O {} {}".format(BADLIBSZSTPATH, GST_PLUGIN_BAD_LIBS_DL))
		os.system("wget -O {} {}".format(GOODZSTPATH, GST_PLUGIN_GOOD_DL))
		VAAPIZSTUNTARPATH = TMP_DEPS_PATH + "/vaapi"
		PIPEWIREUNTARPATH = TMP_DEPS_PATH + "/pipewire"
		BADLIBSUNTARPATH = TMP_DEPS_PATH + "/bad"
		GOODUNTARPATH = TMP_DEPS_PATH + "/good"
		os.mkdir(VAAPIZSTUNTARPATH)
		os.mkdir(PIPEWIREUNTARPATH)
		os.mkdir(BADLIBSUNTARPATH)
		os.mkdir(GOODUNTARPATH)
		os.system("tar --use-compress-program=unzstd -xf {} -C {}".format(VAAPIZSTPATH, VAAPIZSTUNTARPATH))
		os.system("tar --use-compress-program=unzstd -xf {} -C {}".format(PIPEWIREZSTPATH, PIPEWIREUNTARPATH))
		os.system("tar --use-compress-program=unzstd -xf {} -C {}".format(BADLIBSZSTPATH, BADLIBSUNTARPATH))
		os.system("tar --use-compress-program=unzstd -xf {} -C {}".format(GOODZSTPATH, GOODUNTARPATH))

		os.system("cp {}/usr/lib/gstreamer-1.0/libgstvaapi.so {}".format(VAAPIZSTUNTARPATH, VAAPIPATH))

		os.system("cp {}/usr/lib/gstreamer-1.0/libgstpipewire.so {}".format(PIPEWIREUNTARPATH, PIPEWIREPATH))

		os.system("cp {}/usr/lib/libgstcodecparsers* {}".format(BADLIBSUNTARPATH, DEPSLIBSSPATH))
		os.system("cp {}/usr/lib/gstreamer-1.0/libgstvideoparsersbad.so {}".format(BADLIBSUNTARPATH, BADPATH))

		os.system("cp {}/usr/lib/gstreamer-1.0/libgstisomp4.so {}".format(GOODUNTARPATH, GOODPATH))
		os.system("cp {}/usr/lib/gstreamer-1.0/libgstpulseaudio.so {}".format(GOODUNTARPATH, GOODPATH))
		os.system("cp {}/usr/lib/gstreamer-1.0/libgstlame.so {}".format(GOODUNTARPATH, GOODPATH))


	async def uninstall_deps(self):
		logger.info("Uninstalling dependencies")
		os.system("rm -rf {}".format(DEPSPATH))

	async def check_if_deps_installed(self):
		deps_installed = os.path.exists(DEPSPLUGINSPATH)
		if deps_installed:
			logger.info("Dependencies already installed")
		else:
			logger.info("Dependencies not installed")
		return deps_installed

	async def _main(self):
		logger.info("Loading...")
		pass

	async def _unload(self):
		logger.info("Unloading...")
		if self.recording_process is not None:
			Plugin.end_recording(self)
		pass