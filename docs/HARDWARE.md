# Hardware y plataformas

Objetivos: Arch Linux, EndeavourOS y Fedora KDE. CPU térmica: hwmon `coretemp` o `k10temp`. NVIDIA usa opcionalmente `nvidia-smi`. Intel GPU puede leer el archivo de métricas del recolector opcional `intel_gpu_top`/systemd, que no se instala ni activa por el tema. La ausencia, antigüedad o invalidez de los sensores se representa con `N/D` o con el espaciador condicional de OPT-01.

QA-19: EndeavourOS host 87/87 pruebas y Conky/Xvfb con GTX 1650. Arch y Fedora: 87/87 en contenedores sin escritorio KDE. Hay pruebas funcionales para Intel válido 0/100 y datos ausentes/inválidos; NVIDIA presente/ausente/timeout; SWAP, temperaturas, interfaces de red y CPU variable. Son pruebas de software y un benchmark aislado, no validación del escritorio KDE de cada distribución. El backend de referencia es X11/Xwayland; no se afirma soporte del backend Wayland nativo. Falta la inspección visual en KWin/Xwayland real.

Actualización QA-21.3: EndeavourOS, Arch y Fedora pasan 90/90 pruebas. La GTX 1650 entregó temperatura decimal real y el renderer la presentó como entero redondeado conforme a OPT-01. El benchmark físico y su protocolo están en `PERFORMANCE.md`. La suite de contenedores no acredita un escritorio KDE. La revisión de temperatura en KWin/Xwayland debe repetirse después de esta corrección.
