# Cambios

## v1.1.0 candidato local
- Mantiene X11/Xwayland y elimina el antiguo cargador de logo inactivo y las imágenes heredadas no utilizadas.
- Importación OPT-01 con rutas parametrizadas y presentación congelada.
- Consultas NVIDIA y térmicas consolidadas, timeouts y menos procesos.
- Instalador transaccional, migración de autostart y desinstalador reversible.
- Recurso Intel opcional, pruebas y benchmark.
- Corrección QA-18/19: el probe X11 valida el XID registrado por Conky aunque `_NET_WM_PID` falte. QA-19 identificó y restauró la barra de carga Intel que faltaba en datos válidos, preservando la alineación de OPT-01; la fixture visual heredada ahora ejercita las dos filas originales.
- Validación QA-19: captura sintética Xvfb AE=0, smoke físico y seis muestras físicas con geometría equivalente de 283×893. CPU mediana de un núcleo 10,061 % OPT-01 / 4,240 % candidato; NVIDIA 48 / 12 consultas por minuto, sin fallos. La licencia derivada todavía bloquea distribución pública; KDE/KWin real aún no está validado.
- QA-21.3: se corrigió el parseo estricto de temperaturas NVIDIA decimales. `34.22°C` ahora se muestra como `34°C`, manteniendo umbrales sobre el valor sin redondear, validación independiente de VRAM/utilización y una sola consulta por snapshot. La suite quedó en 90 pruebas; nuevo benchmark físico y evidencia en `docs/PERFORMANCE.md`. La repetición visual KDE posterior al cambio y la licencia derivada continúan pendientes.
- QA-21.4: el mantenedor reportó una inspección visual satisfactoria del candidato temporal en KDE Plasma 6.8.3, Wayland/Xwayland/KWin, con producción aislada en otra salida. Se verificaron transparencia, posición, identidad visual, tipografía, colores, barra Intel, métricas NVIDIA incluida la temperatura decimal y secciones de CPU/RAM/almacenamiento/red/procesos. La clase de ventana de prueba fue distinta, por lo que las reglas KWin de la clase original no quedan cubiertas. Se observó una advertencia de inicialización de fuentes sin defecto visible; no se suprimió.
- Cierre de ingeniería v1.1.0 dentro del alcance validado: 90/90 pruebas en EndeavourOS, Arch rootless y Fedora rootless; benchmark QA-21.3: medianas CPU por núcleo 9,845 % OPT-01 y 4,310 % candidato, consultas NVIDIA 48/12 por minuto. La redistribución sigue bloqueada por licencia upstream no acreditada.
