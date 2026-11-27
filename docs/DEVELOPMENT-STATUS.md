# Estado de estabilización · candidato v1.1.0

## QA-21.4 — cierre del release freeze — 2026-11-27

- El mantenedor reportó validación visual satisfactoria del candidato temporal en KDE Plasma 6.8.3, Wayland/Xwayland/KWin. La prueba usó HDMI-A-3 y mantuvo la instancia de producción en VGA-1; clase temporal diferenciada. Confirmó transparencia, posición, identidad visual, fuentes, colores, barra Intel, VRAM/carga/temperatura NVIDIA decimal y CPU/RAM/almacenamiento/red/procesos. No valida reglas KWin de la clase original ni equivale a instalación completa.
- Conky emitió una advertencia de inicialización de fuentes en los logs QA; no se ocultó. El mantenedor no observó defecto visual de tipografía en QA-21.4.
- QA-21.3 sigue siendo la medición de rendimiento vigente: seis muestras válidas; medianas CPU/núcleo 9.845 % OPT-01 / 4.310 % candidato (56.22 % menos), consultas NVIDIA 48/12 por minuto, cero fallidas y 283×893 ambas. No se ejecutaron benchmarks ni suites nuevas para este cierre documental.
- Cierre técnico del candidato: **PASS dentro del alcance validado**. Evidencias: 90/90 local EndeavourOS, 90/90 Arch rootless, 90/90 Fedora rootless (270 ejecuciones acumuladas); ShellCheck, audit, doctor, benchmark sintético y smoke físico PASS; comparación Xvfb AE=0; validación visual humana QA-21.4 reportada por el mantenedor. Contenedores Arch/Fedora no equivalen a escritorios KDE.
- Distribución: **BLOCKED**. Falta evidencia autoritativa de licencia/permisos aplicables al código derivado de Hybrid Back To Basic v1.0.1 y a la configuración Conky heredada; no se asigna GPLv3. Se requiere copia/documento de licencia aplicable al código concreto o autorización explícita de los titulares identificados.
- No se hizo staging, commit, publicación ni cambio funcional. Rama `develop/v1.1.0`, HEAD `96bffb439c0d6fd946add540c0aed834236d154b`.

## QA-21.3 — corrección del parser térmico NVIDIA — 2026-11-27

- **Causa raíz:** la consulta ordenada `memory.used,memory.total,utilization.gpu,temperature.gpu` devolvió `586,4096,16,34.22`; el parser aplicaba `int()`/`isdecimal()` por igual y convertía solo la temperatura decimal en `None`.
- **Corrección/TDD:** prueba funcional RED con respuesta equivalente y comprobación de una consulta por snapshot; luego parser decimal finito independiente, rango inclusivo 0–150, manteniendo validación entera de memoria/utilización. El renderer redondea para presentación sin cambiar umbrales sobre el valor crudo.
- **Casos:** enteros/decimales, límites 0/150, 74.9/75/85, negativos, >150, NaN/Inf, N/A, `[Not Supported]`, vacío, texto y notación no admitida. Temperatura inválida conserva VRAM/utilización. Salida histórica entera preservada.
- **Hardware:** `python3 -BEs bosh-to-the-basic/scripts/temperature-panel.py --all` PASS en GTX 1650; temperatura real 34°C, memoria/utilización presentes; exit 0.
- **Pruebas:** focalizadas PASS; `make test` 90/90 PASS local, Arch y Fedora (exit 0 cada uno); `make audit`, `make doctor`, benchmark sintético, ShellCheck y `git diff --check` PASS.
- **Smoke:** PASS; 3 s warmup + 5 s medida por variante; X11 válido y geometría 283×893 en ambas; consultas NVIDIA 4/1, fallidas 0; referencia OPT-01 verificada 38/38 antes/después.
- **Benchmark físico posterior al cambio:** tres muestras alternadas de 60 s y 30 s warmup; mediana CPU por núcleo 9.845 % OPT-01 (DE 0.036510) y 4.310 % candidato (DE 0.117108), reducción observada 56.22 %; NVIDIA 48/12 consultas por minuto, fallidas 0; seis geometrías 283×893. No se detuvo producción.
- **Evidencia:** `/tmp/bosh-qa21-benchmark.gDAsUAt2/benchmark.csv`, `.json` y `.logs/`; smoke `/tmp/bosh-qa21-smoke.kK53NdES/smoke.csv`.
- **Pendiente:** revisión manual de temperatura posterior al cambio en KDE/Xwayland, en sesión separada; no se abrió ventana sobre el escritorio activo. Licencia del código derivado sigue sin resolverse.
- **Clasificación:** técnicamente CONDITIONAL por revisión KDE posterior pendiente; distribución BLOCKED por derechos de redistribución no acreditados. Sin commit, staging ni publicación.

## QA-18 — Detector X11, comparación visual y medición — 2026-11-27

Registro histórico de QA-18. Las conclusiones de ese bloque sobre la paridad Intel y la diferencia de altura fueron corregidas por QA-19, documentado más abajo.

- [x] Causa raíz: Conky 1.25.2-pre crea la ventana `0x200001` con `WM_CLASS` y título, pero no publica `_NET_WM_PID`; en Xvfb no hay window manager ni `_NET_CLIENT_LIST`. La búsqueda exclusiva por PID devolvía cero. Conky registra el XID en stdout/stderr.
- [x] `tools/x11_window.py` extrae ese XID del log, comprueba que existe en el árbol de la conexión DISPLAY aislada, corrobora `_NET_WM_PID` si se publica, exige `IsViewable`, geometría positiva y estable, rechaza ambigüedad/desaparición y conserva errores Xlib. Espera acotada para log y resize inicial. El worker y la comparación visual usan el mismo detector.
- [x] Reproducción con Xvfb y Conky real: `xprop` confirmó `_NET_WM_PID: not found`; el checker rechazó la búsqueda por PID, pero validó el XID del log y devolvió ventana visible. Se aisló y corrigió además una carrera 5×5→tamaño final en visual compare.
- [x] Backend moderno usa `output_backend='x11'`, `own_window_color` y `text_alpha`; el helper conserva nombres legacy solo para builds antiguos. El Xvfb temporal normaliza `xinerama_head=0`; no toca configuración instalada.
- [x] Fixture visual OPT-01 actualizado para la estructura antigua: valores Intel/GPU/térmicos/red/SWAP sintéticos y rutas privadas; no lee `/run/bosh-conky` ni el estado de la red anfitriona. Se corrigió el quoting de `execgraph`.
- [x] QA-18 había interpretado la fila Intel de forma incorrecta; QA-19 demostró que OPT-01 alinea el porcentaje a la derecha y emite una barra adicional cuando hay sensor válido. Véase la causa corregida en la sección QA-19.
- [x] Smoke físico final PASS, exit 0: 3 s warmup + 5 s medida por variante, scopes separados, ventana estable; 4 consultas NVIDIA OPT-01 y 1 candidata por muestra, cero consultas fallidas. CPU: una muestra corta, no concluyente.
- [x] Comparación Xvfb QA-18 inicialmente dio AE=0, pero QA-19 identificó que la fixture había reducido la salida OPT-01 a una fila Intel. Esa evidencia no demuestra paridad Intel; la comparación corregida QA-19 está documentada abajo.
- [x] Benchmark físico completo PASS, exit 0: seis muestras válidas alternadas; 30 s warmup + 60 s medida cada una, scopes v2 independientes. OPT-01 CPU 10,313/10,075/10,094 % (mediana 10,094; DE 0,132); candidata 4,195/4,099/4,157 % (mediana 4,157; DE 0,048). NVIDIA 48 frente a 12 consultas por minuto, fallidas 0/0. RSS mediana: 223,522,816 B / 103,190,528 B. Producción no se detuvo.
- [x] El delta de altura medido en QA-18 se resolvió en QA-19: faltaba la fila de barra Intel del candidato. Tras corregir renderer y fixture, smoke y benchmark miden ambas variantes 283×893.
- [x] Cierre de verificación: `make test` 86/86 PASS (exit 0); Arch rootless 86/86 PASS; Fedora rootless 86/86 PASS; `make audit` PASS (ShellCheck, systemd unit, Bash/Python/Lua); `make doctor` PASS; `make benchmark` sintético PASS; ShellCheck explícito PASS; `git diff --check` PASS.
- [ ] Licencia de código derivado: continúa bloqueando publicación. No se infiere GPLv3 ni se asigna licencia a terceros.

Evidencia QA generada en directorios temporales privados fuera del repositorio. Referencia OPT-01 verificada antes del smoke y después del benchmark; no se editó. No quedan scopes/Xvfb del benchmark.

### Cierre histórico QA-18 (supersedido por QA-19)

- Suites: EndeavourOS local 86/86, Arch 86/86, Fedora 86/86; todas exit 0. Contenedores rootless, sin red y con montaje del repositorio de solo lectura. Imágenes: Arch `sha256:cdbce410d7a983653f0090437669cfc1c6bbac0b9b4d887a9c837772c638b9e2`; Fedora `sha256:6177ee793438dffef135def5f7b39f43d0380f4883d91e9d559f34a3bc23b860`.
- `make audit`, `make doctor`, `make benchmark` sintético y ShellCheck explícito: PASS, exit 0. Una invocación manual exploratoria de ShellCheck incluyó archivos no shell y devolvió 123; repetida con el conjunto exacto de scripts, pasó.
- `git diff --check`: PASS. Sin procesos Xvfb/scopes de prueba remanentes. La referencia persistente se mantuvo inalterada y su manifiesto verificó antes y después de las pruebas físicas.
- Hallazgos pendientes al cerrar QA-18: discrepancia de altura y permiso de redistribución. La discrepancia se resolvió en QA-19; la licencia continúa pendiente. La captura QA-18 ocultaba la barra Intel por una fixture incompleta.
- Smoke físico: PASS funcional (3 s + 5 s por variante, ventanas visibles, 4/1 consultas NVIDIA, 0 fallidas); CPU de muestra corta no concluyente.
- Benchmark físico: ejecutado con tres muestras alternadas de 60 s por variante; medianas CPU equivalentes a un núcleo 10,094 % OPT-01 y 4,157 % candidato; desviaciones estándar 0,132 y 0,048; NVIDIA 48 frente a 12 consultas/minuto, fallidas 0. La diferencia geométrica permanece como bloqueo de aceptación integral del diseño.
- Clasificación al cerrar QA-18: CONDITIONAL. Esta clasificación histórica queda reemplazada por la matriz QA-19.

Rama develop/v1.1.0. Base 96bffb439c0d6fd946add540c0aed834236d154b.

## QA-19 — fila Intel, paridad visual y regresión — 2026-11-27

- **Causa raíz demostrada:** el lector OPT-01 imprime el porcentaje con `${alignr}` y, si el dato Intel es válido, una segunda línea `${execbar 4,259 ...}`. El candidato omitía esa fila; 17 px corresponden a la línea/barra. Cuando Intel falta, OPT-01 imprime `N/D` y una línea espaciadora, comportamiento que el candidato ya conservaba.
- **Defecto de QA identificado:** la fixture visual reemplazaba el execpi Intel de OPT-01 por un `echo` de una sola línea, ocultando precisamente la barra. Se sustituyó por un script fixture privado de dos líneas; no accede a `/run/bosh-conky`.
- **Corrección:** la salida candidata alinea el porcentaje a la derecha y muestra una barra Lua de dimensiones equivalentes con valor válido; no se añade una fila artificial. Se mantiene solo el espaciador cuando el sensor no está disponible.
- **TDD:** las pruebas de salida válida y de fixture fallaron antes del cambio (fila de barra ausente/comando de fixture incorrecto), luego pasaron. Se añade cobertura Intel 0/100 y se mantienen pruebas de archivo ausente, vacío/obsoleto, no regular, symlink, NaN y fuera de rango.
- **Visual Xvfb corregido:** OPT-01 y candidato 283×927; AE=0, exit 0. Capturas idénticas bajo datos sintéticos. No es comprobación de KWin/Xwayland real.
- **Smoke físico:** PASS; 3 s + 5 s, geometría 283×893 en ambas; 4 frente a 1 consultas NVIDIA, fallidas 0.
- **Benchmark físico:** seis muestras alternadas, 30 s warmup + 60 s medida, exit 0. OPT-01 10,147/10,041/10,061 % (mediana 10,061; DE 0,056); candidato 4,167/4,240/4,354 % (mediana 4,240; DE 0,094). Consultas/min 48/12, fallidas 0/0. RSS panel mediana 209,666,048/103,124,992 B; procesos worker ~23 MB. La mejora pareada de CPU mediana es ~57,85 % en este host.
- **Regresión:** EndeavourOS/Arch/Fedora 87/87 pruebas PASS, exit 0. `make audit`, `make doctor`, `make benchmark` sintético, ShellCheck y `git diff --check` PASS. Arch/Fedora se probaron en contenedores rootless sin red y con repo de solo lectura.
- **Referencia:** SHA256SUMS 38/38 verificado antes del smoke y al terminar el benchmark; referencia sin modificaciones.
- **KDE real:** NOT RUN; no se lanzaron ventanas en el escritorio activo. Transparencia/KWin/Xwayland requiere revisión humana aislada.
- **Licencia:** DISTRIBUTION BLOCKED. QA-19 revisó revisión upstream Bitbucket v1.0.1; no hay LICENSE/COPYING en el árbol. README atribuye la adaptación a Haidir pero desconoce autor de la configuración de 2009. El código Conky/Lua local es derivado; no se declara GPLv3.
- Evidencia privada: smoke `/tmp/bosh-qa19-smoke-final.3959a7ix/smoke.csv`; capturas `/tmp/bosh-qa19-visual2.QiIf0Uj9/evidence/`; benchmark `/tmp/bosh-qa19-benchmark-final.YB9KNiMy/benchmark.csv` y `.json`, con logs asociados. No se incluyen en el repositorio.
- **Clasificación:** TECHNICALLY CONDITIONAL por validación KDE real pendiente; DISTRIBUTION BLOCKED por licencia; global CONDITIONAL/no publicar.

## Completado
- [x] Importación OPT-01 contrastada con referencia normalizada: 38 archivos y modos.
- [x] Unidad y recolector Intel incluidos como recursos opcionales, sin instalación.
- [x] Instalador/desinstalador, migración de autostart, manifiesto y rollback.
- [x] Guías de instalación, recuperación, arquitectura, seguridad, hardware, Intel, rendimiento y validación visual.
- [x] Cachés Python identificadas eliminadas y exclusiones incorporadas.
- [x] Timeout de detección de ruta cubierto por prueba de regresión.

## Verificación de estabilización
- [x] make test — PASS, 47 pruebas, exit 0
- [x] make audit — PASS Bash/Python/Lua; SKIP systemd por restricciones de sockets del sandbox
- [x] git diff --check — PASS
- [x] Sin cachés ni bytecode. Sin rutas HOME personales ni datos privados en cambios; rutas genéricas /run y temporales de herramientas son intencionales.

## Checklist de aceptación pendiente
- [ ] Validar visualmente OPT-01 en Xwayland aislado.
- [ ] Probar instalación y rollback en HOME temporal en Arch, EndeavourOS y Fedora KDE.
- [ ] Medir tres muestras alternadas OPT-01/candidato; 30 s de calentamiento + 60 s medidos en cgroup v2 exclusivo por muestra.
- [ ] Validar permisos DRM y unidad Intel en entorno de pruebas.
- [ ] Confirmar licencias y atribuciones antes de distribuir.

Las pruebas simuladas no representan consumo real. En esta sesión no se debe modificar producción, instalar servicios, usar privilegios ni crear commits.

## Fase release readiness
- [x] make test — PASS, 47 pruebas, 7.507 s (ejecución de readiness).
- [x] make audit — PASS Bash/Python/Lua; SKIP systemd por SO_PASSRIGHTS/SO_PASSCRED del sandbox.
- [x] make benchmark — PASS sintético, 5 consultas/ciclo OPT-01 frente a 1 candidata; no es consumo total.
- [x] Preparado docs/RELEASE-READINESS.md con checklist y pendientes explícitos.
- [x] make doctor — PASS Conky/Python; SKIP ShellCheck porque no está instalado.
- [x] Inventario de árbol y búsqueda de cachés/bytecode, rutas HOME personales, correos y tokens — sin hallazgos.
- [x] Confirmado que no hay workflow .github en el repositorio.
- [x] systemd-analyze verify — PASS fuera del sandbox, solo lectura, exit 0.
- [x] make doctor — PASS Conky 1.25.2-pre y Python 3.14.10; SKIP ShellCheck ausente.
- [x] NVIDIA consultado en modo lectura — FAIL de disponibilidad: driver no accesible (código 9), sin muestra física.
- [x] Solo Xwayland disponible entre los servidores enumerados; Xvfb/Xephyr/compositor aislable y contenedores/VM no disponibles.
- [ ] Validación visual aislada Xwayland, benchmark físico, host systemd/DRM, Fedora/Arch y licencias.

## QA fase 1-2
- [x] ShellCheck 0.11.0 disponible; auditoría limpia con -x. Solo advertencias informativas intencionales suprimidas con comentario. Integrado en make audit.
- [x] Podman rootless/overlay comprobado. Imágenes oficiales descargadas e identificadas por digest.
- [x] Arch rootless pasó audit y 47 pruebas con Xvfb, red off, UID 1000, bind de repo readonly.
- [ ] Fedora rootless y render visual pendientes.

## QA final release gate
- [x] ShellCheck 0.11.0 — PASS via shellcheck -x. Intentional Conky literals annotated. make audit now includes ShellCheck.
- [x] Podman rootless + overlay verified. Arch image digest sha256:bddb91b7a73f31ed6be307fc8ec75e5dd59ff8ccf6c5a1bbb8205f14702c6b4a. Fedora digest sha256:6440fc8f3481de718c4a4e1b5685d3d3b4b5407e0e89a26c3cab258b0d9c79dc.
- [x] Arch container: audit PASS, 47/47 tests PASS with Xvfb, network disabled, repo read-only, UID 1000.
- [ ] Fedora container: audit PASS, 46/47 tests. Console integration passes after DISPLAY propagation; one layout test remains failing due distribution Conky config differences. Investigate before announcing Fedora test support.
- [x] systemd-analyze verify: PASS on host, exit 0, read-only.
- [ ] Visual capture comparison pending; container Xvfb capability established, explicit OPT-01 vs candidate screenshots not yet generated.
- [ ] Physical benchmark blocked in Codex execution: nvidia-smi still fails to connect to host driver, cgroup is terminal scope. No production process altered.
- [ ] License review remains unresolved for legacy PNG assets. No license inferred or removed.
- [x] Root cause Fedora layout assertion: test expected config.output_backend=x11 although the candidate relies on default X11 selection. Removed that false assumption; retained width/update/layout checks. Also corrected invalid Conky keys to legacy-compatible xftalpha/own_window_colour while preserving values.
- [x] Fedora and Arch rootless containers both pass 47/47 after correction, with Xvfb, UID 1000, no network at test time, repository read-only.
- [x] 25 unreferenced distro images and preview removed from candidate and installer allowlist. Required distro-1a retained; license remains unverified and blocks release.
- [x] CI added with read-only contents permission, pinned checkout action SHA, pinned official image digests, audit/tests, no publishing.
- [ ] Physical GPU benchmark and screenshot comparison still pending. Xvfb/Conky tests validate parser/runtime but not side-by-side pixels.
- [x] Final local suite rerun after compatibility, installer-resource and CI changes — 47/47 PASS; make audit PASS except systemd sandbox SKIP; make doctor detects Conky/Python/ShellCheck; git diff --check PASS.
- [x] Synthetic benchmark rerun remains functional-only; no physical CPU claim.
- [x] Confirmed distro-1a.png was dead: draw_logo and lua_draw_hook_pre are absent from active configuration/module. Removed final image and installer entry; kept textual attribution.
- [x] Conky Arch/Fedora capability output lists X11 and ARGB visual; no native Wayland output backend is compiled. Added legacy-compatible out_to_x=true. This selects X11/Xwayland, not native Wayland.
- [x] Arch/Fedora suites after dead asset removal and explicit X11 setting: 47/47 each.
- [x] NVIDIA query PASS, GTX 1650 driver 620.73.04. Physical benchmark still not run because interactive systemd user cgroup owns the active session and current benchmark harness cannot safely create its own delegated leaf without administrator setup. No production Conky was stopped.
- [ ] Paired pixel screenshots and physical benchmark remain pending. Existing Xvfb console integration is not a screenshot comparison.
- [x] Búsqueda de copia local original en Documentos/Documents: no existe; no se halló evidencia GPLv3 adicional.
- [x] Añadidos tools/visual-compare.sh y tools/benchmark-real.sh; ambos pasan bash -n y ShellCheck.
- [ ] Visual script intentado. Xvfb falla al enlazar el socket Unix en sandbox porque /tmp/.X11-unix no es escribible por la sesión; no se cambió su propietario ni permisos.
- [ ] Benchmark script intentado. systemctl --user bus está bloqueado en sandbox; no se creó scope ni se ejecutó Conky.

## Cierre QA-10–QA-16 — 2026-11-27

Este bloque reemplaza los conteos anteriores de 47/57 pruebas y los estados de las herramientas QA.

- [x] QA-10: `relocate_config()` reescribe rutas absolutas y escapadas en copias temporales; después del backend se rechaza cualquier ruta ejecutable hacia el tema activo bajo XDG. Pruebas funcionales con espacios y ruta productiva simulada.
- [x] QA-11: el wrapper NVIDIA registra ID, timestamps monotónicos, código de salida y CPU. El worker cuenta consultas y CPU solo en `[start_ns, end_ns]`; llamadas que cruzan límites invalidan la muestra y fallos cuentan por separado. Startup, calentamiento y cierre quedan fuera.
- [x] QA-12: `benchmark_worker.py` invoca `x11_window.py` antes del calentamiento, tras calentamiento y tras medir. El probe exige PID coincidente, ventana X11 mapeada/viewable y geometría positiva. Pruebas mock para vista mapeada/no mapeada y proceso simulado/cgroup.
- [x] QA-13: fixture determinista compartido controla reloj, CPU, RAM, SWAP, GPU, sensores, red, almacenamiento y procesos en ambas copias. Se conserva la estructura de presentación; únicamente se inyectan fuentes/valores y objetos equivalentes. Prueba compara las dimensiones originales de barras y gráficos.
- [x] QA-14: ambos runners usan cookie X11 privada, `XAUTHORITY` modo 0600, runtime XDG modo 0700, Xvfb sin TCP y variables Wayland aisladas. El benchmark conserva el entorno real de `systemd-run` y aplica el entorno gráfico temporal solo al worker dentro del scope.
- [x] QA-15: backend moderno solo se declara compatible si Conky sale 0 y emite el marcador `backend-probe`; ausencia silenciosa es error. El probe usa una muestra por consola y comprueba que la clave moderna no sea rechazada. Pruebas de ejecutables mock con marcador y salida silenciosa.
- [x] QA-16: pruebas funcionales y simuladas incorporadas a `tests/test_qa_runtime.py`, `tests/test_release_tools.py`, `tests/test_install.py` y `tests/test_panel.py`.
- [x] Smoke-test implementado: `--smoke-test` ejecuta una muestra por variante, con 3 s de calentamiento y 5 s medidos. No ejecutado: no existe una referencia OPT-01 validada.
- [x] Referencia verificada sin modificar fuentes: copia temporal antigua y tema activo fallan el fingerprint de `bosh-to-the-basic.conf`. Esperado `4545a1a845edaebc4dfab3063e79ccc164abc7ecad7de015ccc97a454c0d114f`; ambos normalizados `ddcffddeb58af8440de3ecf76848fe92e6b7f3b0972b129a3e1deb0a5035a7b8`. Los runners rechazan esas entradas antes de Conky/Xvfb/systemd.
- [x] `make test`: 72/72 PASS local; 72/72 PASS Arch rootless; 72/72 PASS Fedora rootless.
- [x] Contenedores usados: `localhost/bosh-qa-arch:latest` digest `sha256:cdbce410d7a983653f0090437669cfc1c6bbac0b9b4d887a9c837772c638b9e2`; `localhost/bosh-qa-fedora:latest` digest `sha256:6177ee793438dffef135def5f7b39f43d0380f4883d91e9d559f34a3bc23b860`. Ambos rootless, UID 1000, sin red, repo read-only y `/tmp` efímero.
- [x] `make audit`: PASS ShellCheck/Bash/Python/Lua local; systemd SKIP por sockets del sandbox. Arch audit PASS incluida unidad systemd; Fedora audit PASS ShellCheck y Bash/Python/Lua, systemd SKIP porque `systemd-analyze` no está en la imagen.
- [x] `shellcheck -x tools/benchmark-real.sh tools/visual-compare.sh`: PASS, exit 0.
- [x] `git diff --check`: PASS. 79 rutas locales modificadas/nuevas revisadas: sin ruta literal personal, credenciales, bytecode, caché ni archivos temporales.
- [x] Estado Git al cierre: rama `develop/v1.1.0`, HEAD `96bffb439c0d6fd946add540c0aed834236d154b`; sin commits realizados.
- [ ] Comparación visual y benchmark real/smoke: no iniciados, bloqueados por fingerprint OPT-01 no coincidente. No se generaron capturas ni métricas físicas. Reanudar solo con una copia que valide los cinco fingerprints auditados.
- [ ] No se alteró la instalación activa; no se detuvo Conky ni se ejecutó una unidad de benchmark. Sin sudo, commits ni publicaciones.

## QA-17 — Huellas y referencia persistente

- [x] Corregido `verify_opt01_reference()`: distingue SHA-256 original de `bosh-to-the-basic.conf` (`4545a1a845edaebc4dfab3063e79ccc164abc7ecad7de015ccc97a454c0d114f`) y huella normalizada tras sustituir la raíz por `@CONKY_DIR@` (`ddcffddeb58af8440de3ecf76848fe92e6b7f3b0972b129a3e1deb0a5035a7b8`). La función acepta el original exacto o la variante normalizada autenticada; mantiene las otras cuatro huellas sin cambios. Procedencia documentada junto a las constantes del verificador.
- [x] Pruebas funcionales: aceptación de config original y normalizada; rechazo de config modificada y módulo Lua alterado.
- [x] Instalación activa verificada en modo lectura: 5/5 huellas. Referencia temporal también: 5/5; su config se verifica por la huella normalizada.
- [x] Los otros 33 archivos se compararon con `96bffb439c0d6fd946add540c0aed834236d154b`: contenido SHA-256 y permisos 0644/0755 coinciden 33/33. Árbol original: 38 archivos esperados (36 del commit base más dos módulos ya autenticados), cuatro subdirectorios, cero enlaces simbólicos y cero extras.
- [x] Copia privada persistente creada en `~/.local/share/bosh-opt01-audited/bosh-to-the-basic`, tras comprobar que no existía el destino. Manifiesto `SHA256SUMS` verifica 38/38 archivos; directorio padre 0700, raíz de tema 0700 y manifiesto 0600. Configuración equivalente normalizada; no se tocó `~/.config`.
- [x] Verificación final: `make test` PASS 74/74; `make audit` PASS ShellCheck/Bash/Python/Lua, systemd SKIP por restricción de sockets del sandbox; `git diff --check` PASS.
- [ ] Smoke-test no ejecutado según el alcance de QA-17. Benchmark completo y comparación visual tampoco ejecutados.

## Corrección de hallazgos QA-01–QA-09
- [x] Systemd verificado localmente: systemd 262.2; `systemd-run(1)` confirma que `--scope` es síncrono. El benchmark usa scopes nombrados sin `--wait` ni `--collect` y registra limpieza para salida, SIGINT y SIGTERM.
- [x] Backend Conky por capacidad: el helper prueba `output_backend` con una configuración de consola. El árbol distribuido selecciona explícitamente X11; el instalador genera `out_to_x=true` solo si Conky rechaza esa opción moderna. Cubiertos ambos casos por pruebas.
- [x] Benchmark: instancia Conky en primer plano, log stdout/stderr, valida PID activo y pertenencia al cgroup, mismo proceso para 30 s de calentamiento y 60 s medidos, reloj monotónico, CPU en porcentaje de un núcleo, RSS del panel y wrapper separados, coste CPU del wrapper NVIDIA y consultas contadas por PATH. No emite CSV final hasta seis muestras válidas alternadas.
- [x] Aislamiento: HOME y cuatro rutas XDG temporales, DISPLAY exclusivo de Xvfb, sin variables Wayland/DBus, sin TCP, rechazo de symlinks de entrada y directorios/logs privados nuevos.
- [x] Visual: captura por PID X11 mediante libX11, una ventana exacta y tamaño real; identifica imágenes vacías y estados compare 0/1/error; reporta límites de composición/transparencia de Xvfb.
- [x] Regresiones QA: `make test` — PASS, 57 pruebas; incluye pruebas específicas de herramientas, concurrencia de benchmark y Conky antiguo/moderno.
- [x] ShellCheck y sintaxis Bash de ambos scripts — PASS.
- [x] `make audit` — PASS Bash/Python/Lua/ShellCheck; SKIP explícito de `systemd-analyze` por sockets de credenciales restringidos en sandbox.
- [x] `make doctor` — PASS; Conky 1.25.2-pre con X11/Cairo/Lua y Python 3.14.10.
- [x] `make benchmark` — PASS sintético, no es medición física.
- [ ] Visual Xvfb — BLOCKED: el sandbox no puede enlazar `/tmp/.X11-unix` (propietario `nobody`); evidencia temporal se limpió tras capturar el error. No se modificó el socket.
- [ ] Benchmark físico — BLOCKED: `systemctl --user show-environment` responde `Operation not permitted` dentro del sandbox. No se creó unidad ni se midió GPU.
- [ ] Licencia del código derivado — BLOCKED: falta evidencia autoritativa; se conserva el bloqueo de publicación.
