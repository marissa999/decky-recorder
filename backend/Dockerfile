FROM ghcr.io/steamdeckhomebrew/holo-base:latest
 
RUN mkdir /pacman && pacman -Sydd --noconfirm --root /pacman --dbpath /var/lib/pacman gstreamer gstreamer-vaapi gst-plugin-pipewire gst-plugins-bad-libs gst-plugins-good

RUN pacman -Sydd --noconfirm --dbpath /var/lib/pacman python-pip

RUN pip3 install psutil --target=/psutil

ENTRYPOINT [ "/backend/entrypoint.sh" ]