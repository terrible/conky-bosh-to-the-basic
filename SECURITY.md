# Seguridad

Instalación solo en HOME. El instalador rechaza root, enlaces, destinos solapados, limita archivos a lista fija y usa lock, manifiesto hash y journal de rollback en estado XDG privado. La desinstalación conserva cambios del usuario. No instala paquetes ni requiere privilegios.

La unidad Intel es opcional y no se instala ni activa. Define DynamicUser, CAP_PERFMON, grupos DRM y aislamiento. Validar localmente permisos y compatibilidad de systemd.
