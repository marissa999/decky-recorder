FROM ghcr.io/steamdeckhomebrew/holo-base:latest
 
RUN mkdir /pacman && pacman -Sydd --noconfirm --root /pacman --dbpath /var/lib/pacman gstreamer-vaapi gst-plugin-pipewire gst-plugins-bad-libs gst-plugins-good gst-rtsp-server

ENTRYPOINT [ "/backend/entrypoint.sh" ]