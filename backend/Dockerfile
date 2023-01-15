FROM ghcr.io/steamdeckhomebrew/holo-base:latest

RUN pacman -Sydd --noconfirm gstreamer-vaapi gst-plugin-pipewire gst-plugins-bad-libs gst-plugins-good gst-rtsp-server  

ENTRYPOINT [ "/backend/entrypoint.sh" ]