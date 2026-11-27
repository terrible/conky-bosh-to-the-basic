FROM docker.io/library/archlinux@sha256:bddb91b7a73f31ed6be307fc8ec75e5dd59ff8ccf6c5a1bbb8205f14702c6b4a
RUN pacman -Syu --noconfirm bash python lua conky shellcheck make xorg-server-xvfb xorg-xauth
WORKDIR /src
CMD ["bash", "-lc", "Xvfb :99 -screen 0 1024x768x24 -nolisten tcp >/tmp/xvfb.log 2>&1 & export DISPLAY=:99; sleep 1; make audit && make test"]
