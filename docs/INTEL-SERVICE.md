# Recolector Intel opcional

`resources/intel/bosh-conky-intel.py` y `.service` son recursos de referencia, no se instalan ni activan. El servicio usa DynamicUser, CAP_PERFMON, grupos DRM, directorio temporal runtime y protecciones systemd. Publica solo el porcentaje Render/3D en `/run/bosh-conky/intel-load`. Antes de empaquetarlo, valida versión de systemd, acceso DRM y política local de capacidades. No ejecutes la unidad desde este repositorio durante la validación.
