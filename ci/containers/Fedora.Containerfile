FROM registry.fedoraproject.org/fedora@sha256:6440fc8f3481de718c4a4e1b5685d3d3b4b5407e0e89a26c3cab258b0d9c79dc
RUN dnf -y install bash python3 lua conky ShellCheck make xorg-x11-server-Xvfb xorg-x11-xauth && dnf clean all
WORKDIR /src
CMD ["bash", "-lc", "Xvfb :99 -screen 0 1024x768x24 -nolisten tcp >/tmp/xvfb.log 2>&1 & export DISPLAY=:99; sleep 1; make audit && make test"]
