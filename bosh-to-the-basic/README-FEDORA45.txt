BOSH TO THE BASIC - ADAPTACION PARA FEDORA 45 / KDE PLASMA / WAYLAND
================================================================

Esta adaptacion conserva las imagenes y el dibujo Cairo del paquete original.

CAMBIOS REALIZADOS
- CPU: Intel Core i5-3330, temperatura PACKAGE y promedio de nucleos.
- Temperaturas: lectura por etiqueta de coretemp.
- GPU: consulta de temperatura, carga y memoria NVIDIA con nvidia-smi.
- GPU Intel: lectura de actividad mediante intel_gpu_top.
- Red: deteccion automatica de la interfaz mediante la ruta predeterminada.
- Distro: lectura de /etc/os-release.
- Rutas Lua: HOME dinamico.
- Lua hook: conky_main.
- Panel redisenado y reducido a 273 px de ancho.
- Instalador con copia de seguridad de la instalacion anterior.

REQUISITOS
- Conky con soporte Lua/Cairo e Imlib2.
- Noto Sans.
- nvidia-smi para metricas NVIDIA.
- intel_gpu_top para metricas Intel.
- lm_sensors para temperaturas.

INSTALACION
1. Extraer el paquete.
2. Abrir una terminal en la carpeta raiz del proyecto.
3. Ejecutar:
   chmod +x install.sh
   ./install.sh
4. El instalador configura el inicio automatico en KDE.
5. Para probar Conky manualmente:
   conky -c "$HOME/.config/conky/bosh-to-the-basic/bosh-to-the-basic.conf" -d

NOTAS
- La posicion de la ventana puede requerir ajustes en KDE Wayland/Xwayland.
- El parametro xinerama_head permite seleccionar el monitor.
- / y /home son subvolumenes del mismo sistema BTRFS; sus cifras de espacio
  pueden coincidir.
- Las particiones NTFS no estan montadas, por eso no se muestran.
- Los scripts de sensores imprimen -- si un sensor o herramienta no esta disponible.
- Para volver atras, restaurar la carpeta .backup-* creada por el instalador.
