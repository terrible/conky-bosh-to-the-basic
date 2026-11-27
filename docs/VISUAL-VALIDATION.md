# Validación visual aislada en Xwayland

## QA-21.4 — inspección KDE real reportada por el mantenedor

El mantenedor reportó una prueba temporal del candidato en KDE Plasma 6.8.3, sesión Wayland con Xwayland/KWin, usando HDMI-A-3 mientras producción permanecía en VGA-1. La inspección confirmó transparencia, posicionamiento, identidad visual, tipografía, colores, barra Intel, VRAM y carga NVIDIA, temperatura decimal corregida, además de CPU, RAM, almacenamiento, red y procesos.

La ventana de prueba utilizó una clase diferenciada. Por ello la prueba no valida la instalación completa ni reglas KWin que coincidan con la clase original. El resultado es evidencia humana reportada; no se conserva una captura QA-21.4 en el repositorio. Conky emitió una advertencia de inicialización de fuentes; el mantenedor no observó un problema tipográfico visible. La advertencia no se suprimió.

## Evidencia QA-19 (Xvfb)

El runner `tools/visual-compare.sh` verifica OPT-01, crea copias privadas y utiliza Xvfb autenticado, sin TCP, `DISPLAY` exclusivo, HOME/XDG temporales, 1024×1200 a 96 DPI. Las fixtures controlan hora, fecha, uptime, CPU, RAM, SWAP, GPU, temperaturas, red, almacenamiento y procesos sin sustituir el layout. QA-18 usaba una fixture Intel que reducía OPT-01 a una sola fila; QA-19 corrigió esa fixture para ejercitar la salida de dos filas original. Capturas QA-19: ambas 283×927 y `compare -metric AE`=0, exit 0. Logs sin errores Conky/Lua. `ARGB visual not available` es la limitación esperada sin compositor; Xvfb no representa la transparencia de KDE Plasma ni es validación Xwayland real.

El detector usa el XID reportado por Conky y espera geometría estable: inicialmente se observó 5×5, luego tamaño final. El smoke y benchmark físico QA-19 registran 283×893 para OPT-01 y candidato. La discrepancia previa de 17 px era la fila de barra Intel que faltaba en el candidato y estaba oculta por la fixture antigua. La igualdad Xvfb comprueba el caso controlado, no sustituye la revisión de KDE real.

QA-21.3 corrigió el render de temperatura NVIDIA decimal. La salida directa del renderer con GTX 1650 mostró `34°C`; smoke y benchmark volvieron a medir 283×893 para ambas variantes. La inspección de temperatura en KWin/Xwayland posterior a la corrección está pendiente; repetir solo en una sesión de prueba separada siguiendo el procedimiento siguiente. Xvfb no acredita la composición/transparencia real.

### Validación manual segura en KDE Wayland/Xwayland

No ejecutar esto en una sesión que muestre el Conky de producción en la misma posición. El administrador debe abrir primero una sesión de prueba separada (usuario de QA o escritorio de pruebas) y confirmar que el panel candidato no se superpondrá con producción. El siguiente procedimiento no instala ni cambia autostart/servicios; cada Conky se ejecuta en primer plano y se detiene con Ctrl-C. Se conserva el `DISPLAY`/`XAUTHORITY` de esa sesión para probar Xwayland, mientras HOME y XDG apuntan al directorio temporal:

```bash
cd /ruta/al/conky-bosh-to-the-basic
set -eu
umask 077
qa="$(mktemp -d "${XDG_RUNTIME_DIR:-/tmp}/bosh-kde-qa.XXXXXXXX")"
cleanup() { test -z "${qa:-}" || { test ! -d "$qa" || test -L "$qa" || rm -rf -- "$qa"; }; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
mkdir -m 700 -p "$qa/home" "$qa/config" "$qa/data" "$qa/cache" "$qa/state" "$qa/runtime"
chmod 700 "$qa/runtime"
cp -a bosh-to-the-basic "$qa/candidate"
python3 installer/conky_backend.py "$qa/candidate/bosh-to-the-basic.conf" "$qa/candidate/bosh-to-the-basic.conf" --xinerama-head 0
env HOME="$qa/home" XDG_CONFIG_HOME="$qa/config" XDG_DATA_HOME="$qa/data" \
  XDG_CACHE_HOME="$qa/cache" XDG_STATE_HOME="$qa/state" XDG_RUNTIME_DIR="$qa/runtime" \
  DISPLAY="${DISPLAY:?Ejecutar dentro de la sesión KDE de prueba}" \
  XAUTHORITY="${XAUTHORITY:?Se requiere la autoridad Xwayland de esa sesión}" \
  conky -c "$qa/candidate/bosh-to-the-basic.conf"
```

Tras Ctrl-C, el trap elimina exclusivamente el directorio temporal de esa ejecución. Repetir el bloque completo en una invocación nueva, cambiando `cp -a bosh-to-the-basic "$qa/candidate"` por `cp -a "$HOME/.local/share/bosh-opt01-audited/bosh-to-the-basic" "$qa/candidate"`; es decir, conservar el destino temporal `$qa/candidate` y la normalización para comparar OPT-01. Inspeccionar transparencia, ubicación, tipografía, colores y secciones; registrar manualmente cuál variante se vio. No parar el Conky productivo ni cambiar reglas KWin. Si no se dispone de una sesión separada, mantener esta comprobación como NOT RUN; Xvfb y Xephyr no sustituyen esta validación del compositor real.
