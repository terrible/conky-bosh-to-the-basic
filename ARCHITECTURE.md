# Arquitectura

La configuración Lua conserva OPT-01. Lua obtiene CPU y SWAP con caché y usa Cairo. Los lectores consolidan hwmon/Intel y hacen una consulta NVIDIA por intervalo. La red detecta la ruta por defecto con interfaz validada.

El instalador Python gestiona preflight, migración de autostart, manifiesto y rollback. La unidad Intel queda como recurso opcional. X11/Xwayland es la referencia. Conky 1.25.2-pre pasó prueba de consola con Lua/Cairo y ruta con espacios. El renderizado KDE sigue pendiente.
