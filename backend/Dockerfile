FROM ghcr.io/steamdeckhomebrew/holo-base:latest

RUN pacman -Sy --noconfirm gstreamer-vaapi gst-plugin-pipewire gst-plugins-bad-libs gst-plugins-good  

ENTRYPOINT [ "/backend/entrypoint.sh" ]