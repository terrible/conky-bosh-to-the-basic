# Release readiness · Bosh To The Basic v1.1.0

## Cierre definitivo QA-21.4 — 2026-11-27

**Ingeniería congelada y cerrada dentro del alcance validado. Distribución pública bloqueada por licencia.** Esta sección supersede los estados de validación pendientes en los registros QA históricos que siguen abajo.

| Área | Estado | Evidencia vigente |
|---|---|---|
| Pruebas | PASS | 90/90 en EndeavourOS, Arch rootless y Fedora rootless: 270 ejecuciones acumuladas de los 90 casos. |
| ShellCheck / `make audit` / `make doctor` / benchmark sintético | PASS | QA-21.3, exit 0; no repetidos en el cierre documental. |
| Smoke físico | PASS | QA-21.3, Xvfb aislado, 3+5 s, ventanas válidas, geometría 283×893, cero consultas NVIDIA fallidas. |
| Benchmark físico | PASS | QA-21.3: 3×60 s por variante, mediana CPU/núcleo 9.845 % OPT-01 / 4.310 % candidato, reducción 56.22 %; NVIDIA 48/12 consultas por minuto; cero fallidas. |
| Comparación Xvfb | PASS | Captura sintética igual AE=0; geometría física equivalente de 283×893. No simula composición KWin. |
| KDE Plasma real | PASS, reporte humano | QA-21.4, Plasma 6.8.3 Wayland/Xwayland/KWin; inspección temporal en HDMI-A-3, producción conservada en VGA-1. Clase de ventana distinta; reglas KWin de la clase original e instalación completa no cubiertas. |
| Advertencia de fuente | INFO | Conky reportó advertencia común de inicialización; el mantenedor no vio defecto tipográfico. Se conserva sin suprimir ni investigar más. |
| Seguridad / integridad OPT-01 | PASS | Evidencia QA-21.3 vigente; manifiesto de referencia 38/38 verificado en cierre. |
| Licencia/redistribución | BLOCKED | No se ha aportado evidencia autoritativa de licencia o autorización para redistribuir el código derivado. |
| Clasificación | **TECHNICAL PASS / DISTRIBUTION BLOCKED** | Candidato local preparado para decisión del mantenedor; **NO PUBLICAR** hasta resolver los derechos. |

Pruebas y cifras proceden de QA-21.3; no se repitieron para este cierre. La validación QA-21.4 se registra como reporte del mantenedor, no como captura inspeccionada independientemente por esta ejecución.

Para resolver el bloqueo de distribución falta un otorgamiento verificable que cubra los archivos derivados de Hybrid Back To Basic v1.0.1, aclarar u obtener permiso respecto al autor desconocido del conkyrc histórico, y acreditar los términos de los cinco archivos OPT-01 importados. La referencia histórica a GPLv3 no es evidencia suficiente. Véase [el inventario de licencias](LICENSE-INVENTORY.md); no se ha asignado una licencia al conjunto.

## Registro QA-21.3 — 2026-11-27 (superado en visual KDE por QA-21.4)

Esta sección es la evidencia vigente posterior a la corrección de temperatura NVIDIA decimal; los bloques QA-18/19 siguientes se conservan como historial.

| Área | Estado | Evidencia |
|---|---|---|
| Parser NVIDIA | PASS | `34.22` parsea como temperatura válida; `temperature-panel.py --all` mostró 34°C en GTX 1650 real; memoria/utilización válidas. |
| Umbrales/presentación | PASS | Comparación térmica sobre valor sin redondear (74.9 sin alerta, 75 advertencia, 85 alerta); redondeo visual OPT-01. |
| Consultas NVIDIA | PASS | Una consulta por snapshot; smoke 4/1 consultas por variante y 0 fallidas; benchmark 48/12 por minuto y 0 fallidas. |
| Pruebas locales | PASS | `make test` 90/90; `make audit`, `make doctor`, `make benchmark` sintético, ShellCheck y `git diff --check`, todos exit 0. |
| Arch / Fedora | PASS | 90/90 en cada contenedor rootless existente, repo read-only, sin red; exit 0. EndeavourOS local también 90/90. |
| Smoke físico aislado | PASS | 3 s calentamiento + 5 s medida; ventanas válidas, geometría 283×893, limpieza completada, referencia íntegra. |
| Benchmark físico | PASS | Tres muestras alternadas de 60 s por variante; CPU por núcleo mediana 9.845 % OPT-01 y 4.310 % candidato (56.22 % menos en esta ejecución), DE 0.036510/0.117108; geometría 283×893. |
| Comparación KDE posterior QA-21.3 | HISTÓRICO | Estaba pendiente al documentar QA-21.3; el mantenedor reportó su resolución en QA-21.4, con límite de clase temporal indicado arriba. |
| Licencia redistribución | BLOCKED | El permiso del código derivado continúa sin evidencia suficiente; no publicar ni atribuir licencia unilateralmente. |
| Git | PASS | Rama `develop/v1.1.0`, HEAD base `96bffb439c0d6fd946add540c0aed834236d154b`; sin staging/commit/publicación. |

Evidencia privada: benchmark `/tmp/bosh-qa21-benchmark.gDAsUAt2/benchmark.csv`, `.json` y `.logs/`; smoke `/tmp/bosh-qa21-smoke.kK53NdES/smoke.csv`. No se incorporaron esos archivos al repositorio. La clasificación técnica es **CONDITIONAL** hasta la revisión KDE posterior; distribución **BLOCKED** por licencia; global **CONDITIONAL — NO PUBLICAR**.

**Estado: CONDITIONAL, no listo para distribución.** Rama develop/v1.1.0, base 96bffb439c0d6fd946add540c0aed834236d154b. No se modificó producción ni se publicaron cambios.

## Verificación ejecutada

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Suite | PASS | make test, 57 pruebas, exit 0 |
| ShellCheck | PASS | ShellCheck 0.11.0 con -x sobre todos los scripts |
| Contenedor Arch | PASS | Imagen oficial fijada por digest; 47/47 pruebas y audit |
| Contenedor Fedora | PASS | Imagen oficial fijada por digest; 47/47 pruebas y audit |
| Sintaxis Bash/Python/Lua | PASS | Incluida en make audit |
| Unidad Intel con systemd-analyze | PASS | Verificación de solo lectura fuera del sandbox, exit 0 |
| ShellCheck | PASS | ShellCheck 0.11.0 limpio con -x |
| Benchmark sintético | PASS, solo funcional | 5 consultas NVIDIA/ciclo OPT-01 frente a 1 en candidato; CPU de hijos no representa CPU total |
| Backend X11 | PASS local / por capacidad para otras versiones | Conky local acepta output_backend=x11; el instalador usa out_to_x solo si el probe lo declara desconocido |
| Capturas pareadas Xvfb | PENDIENTE | Integración Conky comprobada, comparación pixel a pixel no ejecutada |
| Benchmark real | BLOCKED | Bus systemd de usuario denegado por sandbox; no se creó scope ni se ejecutó Conky |
| Herramienta visual | PASS sintaxis / BLOCKED ejecución sandbox | tools/visual-compare.sh pasa bash -n/ShellCheck; Xvfb no puede enlazar /tmp/.X11-unix |
| Herramienta benchmark | PASS sintaxis / BLOCKED ejecución sandbox | tools/benchmark-real.sh pasa bash -n/ShellCheck; systemctl --user bus denegado |
| Regresiones QA-01–QA-09 | PASS | make test: 57/57; incluye backend antiguo/moderno, aislamiento, cgroup, concurrencia, logs, ventana X11 y compare |
| ShellCheck herramientas | PASS | ShellCheck limpio sobre visual-compare.sh y benchmark-real.sh |
| systemd-run | PASS documental / BLOCKED ejecución | systemd 262.2; man confirma --scope síncrono. Bus de usuario denegado en sandbox |
| make doctor | PASS | Conky 1.25.2-pre con X11/Cairo/Lua; Python 3.14.10 |
| Validación de distribuciones | PASS virtual | EndeavourOS, Arch y Fedora pasan 47/47; no acredita KDE real dentro de contenedor |
| Revisión de imágenes | PASS | Imagen distro-1a era código muerto sin hook activo y se retiró, igual que otros PNG sin uso |
| Licencia del código base | BLOCKED | Falta evidencia autoritativa local del permiso exacto para la derivación |
| Benchmark físico | BLOCKED | Aún no hay comparativa equivalente aislada ni evidencia CPU/RAM agregada de tres muestras |
| Comparación visual | BLOCKED | Xvfb disponible y parser probado, pero no se han generado capturas pareadas |
| Instalador/desinstalador | PASS | Revisión independiente de solo lectura sin hallazgos P1/P2 confirmados |
| Contenedores/VM | PASS | Podman rootless, imágenes oficiales fijadas por digest |

## Aceptación antes de distribuir

- [x] Design Freeze declarado y pruebas de layout presentes.
- [x] Importación OPT-01 contrastada previamente, 38 archivos y modos.
- [x] Instalación y rollback cubiertos en HOME temporal.
- [x] Intel, NVIDIA y sensores ausentes cubiertos con fixtures simulados.
- [x] make test pasa localmente.
- [x] make audit pasa Bash, Python y Lua.
- [ ] Verificar unidad Intel en host de prueba con systemd y permisos DRM.
- [ ] Comparar capturas OPT-01/candidato en Xwayland aislado con resolución, DPI y fuentes iguales.
- [ ] Ejecutar tres muestras alternadas por variante, con 30 s de calentamiento y 60 s medidos por muestra.
- [ ] Probar instalación/desinstalación en Arch, EndeavourOS y Fedora KDE.
- [ ] Verificar copyright, licencia y redistribución de imágenes y recursos.
- [ ] Cerrar estos pendientes antes de cualquier release.

## Procedimientos

La guía visual está en VISUAL-VALIDATION.md. El protocolo de benchmark, en PERFORMANCE.md. Instalación y reversión, en INSTALL.md y RECOVERY.md. El servicio Intel, en INTEL-SERVICE.md.

CI local preparado en .github/workflows/ci.yml, matriz Arch/Fedora, permisos contents:read, checkout fijado al commit 11bd71901bbe5b1630ceea73d27597364c9af683, imágenes oficiales fijadas por digest y sin publicación automática. Containerfiles reproducibles en ci/containers. Las suites rootless pasaron 47/47. El workflow remoto no fue activado ni publicado.

La configuración distribuida selecciona explícitamente `output_backend = 'x11'` en Conky moderno. El instalador y las herramientas de validación consultan una prueba de capacidad y convierten a `out_to_x = true` solo para builds antiguos. El test de consola selecciona `output_backend = 'console'` para no contradecir el backend explícito.

## Riesgos abiertos

La unidad Intel no se validó por el sandbox. Las referencias 5,8462 %, 5,7609 % y 9,9697 % fueron informadas por el usuario, no reproducidas en esta fase. El benchmark simulado cuenta procesos y consultas, no consumo integral. Falta validación visual, Fedora/Arch y confirmación de licencias. La revisión de licencia bloquea distribución.

## Siguiente paso

Usar un host o VM desechable con KDE/Xwayland para inspección visual, validar el servicio sin habilitarlo en el sistema cotidiano, ejecutar el benchmark físico con cgroup dedicado y verificar atribuciones. Mantener el candidato local hasta cerrar esos puntos.

## Herramientas ejecutables de cierre

El sandbox rechazó el bind del socket local X11 de Xvfb y el bus de systemd de usuario. Desde Konsole, con la sesión normal intacta, ejecutar:

```sh
cd ~/Proyectos/conky-bosh-to-the-basic
tools/visual-compare.sh ~/.config/conky/bosh-to-the-basic bosh-to-the-basic "/tmp/bosh-visual-$(date +%Y%m%d-%H%M%S)"
tools/benchmark-real.sh ~/.config/conky/bosh-to-the-basic bosh-to-the-basic "/tmp/bosh-benchmark-$(date +%Y%m%d-%H%M%S).csv"
```

El visual compara copias temporales en Xvfb 1024x768 a 96 DPI, sustituye nombres de procesos por fixtures y simula la ruta de red. Produce opt01.png, candidate.png, difference.png y logs en la salida. Revisa transparencia y antialiasing manualmente. El script elimina solo su Xvfb y Conky temporales.

El benchmark requiere NVIDIA accesible y systemd de usuario con scopes/cgroups delegados. Alterna tres pares, 30 s de calentamiento y 60 s medidos en la misma instancia; verifica que el proceso permanezca en su scope exclusivo. Mide delta de cpu.stat, RSS por procesos, frecuencia de consultas y CPU añadida por el wrapper NVIDIA. Escribe CSV de muestras y resumen JSON solo tras seis muestras válidas. No detiene sesiones Conky preexistentes.

La búsqueda solicitada de copias locales del original no encontró las rutas Documentos/Documents. Por ello no se acredita GPLv3 y la licencia derivada permanece bloqueante. No se atribuye licencia a código de terceros.

## Correcciones de herramientas QA

El benchmark usa scopes systemd transitorios síncronos sin `--wait` ni `--collect`; el cleanup detiene únicamente el scope de la prueba ante salida o señales. Cada muestra conserva el mismo Conky en primer plano para calentamiento (30 s) y medición (60 s), comprueba que siga vivo y dentro del cgroup, descarta muestras con error de render y mide CPU del cgroup en delta monotónico. Reporta CPU equivalente a un núcleo, RSS separado del panel y worker, CPU del wrapper NVIDIA, cantidad de consultas y CSV por muestra más JSON de mediana/desviación.

La comparación visual fija métricas dinámicas en las copias temporales, captura la ventana identificada por PID en Xvfb, verifica geometría y archivo no vacío y distingue compare exit 0 (igual), 1 (diferencias), >1 (error). Xvfb no aporta compositor; transparencia y composición no validan Plasma/Wayland.

Resultados de esta sesión: `make test` PASS 57/57; `make audit` PASS ShellCheck/Bash/Python/Lua, SKIP systemd por sockets restringidos; `make doctor` PASS; `make benchmark` PASS sintético únicamente. Intento visual BLOCKED al enlazar el socket Unix de Xvfb por sandbox. El benchmark físico BLOCKED porque el bus `systemctl --user` devuelve `Operation not permitted`. No hay capturas ni métricas físicas nuevas.

## Preparación local para publicación

Clasificación obligatoria: CONDITIONAL. No crear tag ni publicar hasta cerrar visual, benchmark, plataformas y licencias.

## Corrección final de QA-10–QA-16 — 2026-11-27

Estado actualizado que sustituye los resultados anteriores de 57 pruebas: `make test` **PASS 72/72** local, Arch y Fedora. `make audit` pasa ShellCheck, Bash, Python y Lua local y en los contenedores. `systemd-analyze` local se clasifica **SKIP** por los sockets de credenciales del sandbox y en Fedora por herramienta ausente; Arch lo ejecuta y pasa. `git diff --check` se ejecuta en el cierre de esta fase.

Cierre verificado: `git diff --check` PASS; privacidad/artefactos PASS (sin rutas literales personales, credenciales, caché ni temporales entre los cambios). Rama `develop/v1.1.0`; HEAD base `96bffb439c0d6fd946add540c0aed834236d154b`; no se creó commit.

Cambios QA: rutas de configuración reescritas hacia copias privadas y verificación explícita contra el tema activo; eventos NVIDIA con ID/timestamps monotónicos/return code para medir únicamente consultas y CPU del wrapper durante la ventana; consultas fallidas separadas; validación de ventana Conky X11 visible en el worker; cookies Xauthority privadas y runtime/XDG aislados, sin contaminar el entorno de conexión de `systemd-run`; backend moderno exige salida positiva del marcador y no solo ausencia de avisos; fixture visual común que mantiene las secciones, fuentes, barras y gráficos del panel y verifica sus dimensiones. Smoke-test: una muestra por variante con 3 s de calentamiento y 5 s de medición.

Referencia OPT-01: **BLOCKED**. La referencia temporal antigua y la instalación activa no validan los cinco hashes. Ambas config Conky producen SHA-256 normalizado `ddcffddeb58af8440de3ecf76848fe92e6b7f3b0972b129a3e1deb0a5035a7b8`, frente al fingerprint documentado `4545a1a845edaebc4dfab3063e79ccc164abc7ecad7de015ccc97a454c0d114f`. Por seguridad, comparación visual, smoke-test y benchmark completo aún no se iniciaron; los runners verifican la referencia y fallan antes de ejecutar Conky. No se generan capturas ni afirmaciones de rendimiento hasta recuperar la referencia exacta.

| Comprobación | Estado | Evidencia |
|---|---|---|
| QA-10 rutas fuente→copias y detección del tema activo | PASS | Pruebas funcionales con rutas escapadas y ruta productiva simulada |
| QA-11 ventana NVIDIA, retornos fallidos y coste del wrapper | PASS | Casos de eventos simulados dentro/fuera de ventana y cruce rechazado |
| QA-12 ventana X11 visible del PID real | PASS | Mock IsViewable/no mapeada; worker consulta checker alrededor de la medición |
| QA-13 mismos valores sintéticos y dimensiones | PASS | Fixture compartido y comparación funcional de dimensiones/layout |
| QA-14 Xauthority/XDG y entorno del manager | PASS | Configuración aislada en runners y prueba argv/environment |
| QA-15 probe positivo de backend | PASS | Ejecutables mock: marcador aceptado, salida silenciosa rechazada |
| QA-16 regresiones funcionales | PASS | Suite 72/72 local, Arch y Fedora |
| Arch/Fedora test images | PASS | Arch `sha256:cdbce410d7a983653f0090437669cfc1c6bbac0b9b4d887a9c837772c638b9e2`; Fedora `sha256:6177ee793438dffef135def5f7b39f43d0380f4883d91e9d559f34a3bc23b860`; rootless, no network, repo read-only |
| Smoke/visual/benchmark físico | BLOCKED | Fuente OPT-01 disponible no coincide con los fingerprints auditados |

### Comandos para Konsole

Primero recuperar en `"$HOME/.local/share/bosh-opt01-audited/bosh-to-the-basic"` la referencia original de OPT-01 y verificar que los cinco archivos coincidan con `OPT01_FINGERPRINTS` en `tools/qa_runtime.py`. Las dos copias existentes no deben usarse: el script las rechazará. Después, ejecutar smoke-test y solo si finaliza correctamente, las validaciones completas:

```sh
cd "$HOME/Proyectos/conky-bosh-to-the-basic"
OPT01_REF="$HOME/.local/share/bosh-opt01-audited/bosh-to-the-basic"
CANDIDATE="$PWD/bosh-to-the-basic"
OUT="$(mktemp -d /tmp/bosh-v1.1.0-qa.XXXXXX)"
chmod 700 "$OUT"
tools/benchmark-real.sh --smoke-test "$OPT01_REF" "$CANDIDATE" "$OUT/smoke.csv"
```

Si smoke-test termina con código 0, ejecutar comparación visual y benchmark completo:

```sh
tools/visual-compare.sh "$OPT01_REF" "$CANDIDATE" "$OUT/visual"
tools/benchmark-real.sh "$OPT01_REF" "$CANDIDATE" "$OUT/benchmark.csv"
```

El visual conserva los logs y capturas en `OUT/visual`; Xvfb está autenticado, usa 1024×768 a 96 DPI, sin TCP ni compositor. Las métricas sintéticas son iguales entre variantes. Xvfb no valida transparencia/composición de Plasma Wayland. El benchmark completo alterna tres muestras por variante, cada una con 30 s de calentamiento y 60 s de medición en scope independiente; invalida salidas tempranas, errores de render o ventanas no visibles.

## QA-17 — Corrección de huellas OPT-01 — 2026-11-27

`verify_opt01_reference()` distingue explícitamente dos hashes de la configuración: el original auditado (`4545a1a845edaebc4dfab3063e79ccc164abc7ecad7de015ccc97a454c0d114f`) y el normalizado mediante reemplazo de la raíz de tema por `@CONKY_DIR@` (`ddcffddeb58af8440de3ecf76848fe92e6b7f3b0972b129a3e1deb0a5035a7b8`). La procedencia se conserva en comentarios de las constantes. Las otras cuatro huellas mantienen sus hashes originales. Ninguna verificación fue desactivada.

PASS: la instalación activa y la referencia temporal verifican 5/5. De los 38 archivos de OPT-01, los otros 33 coinciden con el commit base en contenido y permisos 0644/0755. El inventario no presenta symlinks ni extras. Se creó sin sobrescribir una copia privada persistente en `~/.local/share/bosh-opt01-audited/bosh-to-the-basic`; el árbol tiene modo 0700 y `SHA256SUMS` verifica 38/38 archivos. El manifest se almacena con modo 0600.

Pruebas tras QA-17: `make test` PASS 74/74; `make audit` PASS ShellCheck/Bash/Python/Lua, systemd SKIP debido a restricciones de sockets del sandbox; `git diff --check` PASS. Clasificación: sigue CONDITIONAL por licencias y validaciones visual/física pendientes. QA-17 no ejecutó smoke-test, benchmark completo ni comparación visual.

Comando único para el smoke-test desde Konsole:

```sh
cd "$HOME/Proyectos/conky-bosh-to-the-basic" && OUT="$(mktemp -d /tmp/bosh-opt01-smoke.XXXXXX)" && chmod 700 "$OUT" && tools/benchmark-real.sh --smoke-test "$HOME/.local/share/bosh-opt01-audited/bosh-to-the-basic" "$PWD/bosh-to-the-basic" "$OUT/smoke.csv"
```

Mensaje de commit propuesto:

`feat: prepare Bosh To The Basic v1.1.0`

Revisión y staging para ejecutar manualmente después de aprobar el diff:

```sh
git status --short
git diff --check
git diff
git add .gitignore AGENTS.md ARCHITECTURE.md CHANGELOG.md Makefile README.md ROADMAP.md SECURITY.md install.sh uninstall.sh bosh-to-the-basic docs installer resources tests tools
git diff --cached --check
git diff --cached
```

No se ejecutaron estos comandos. Antes de integrar, revisar conflictos contra main. No se consultó GitHub ni tags remotos en esta fase. Las notas de versión están resumidas en CHANGELOG.md. El inventario publicable es el conjunto versionado del proyecto, excluyendo caches, informes temporales y datos de laboratorio. Rollback de publicación: retirar la versión/tag siguiendo el procedimiento acordado con el mantenedor y publicar una corrección posterior, sin reescribir historial compartido.

## QA-18 — registro histórico (supersedido por QA-19) — 2026-11-27

Este es el resultado al cierre de QA-18. QA-19 corrigió posteriormente su fixture Intel, resolvió la diferencia geométrica y sustituyó las métricas; consúltese el bloque vigente al final del documento. Estado global histórico **CONDITIONAL; no publicar**.

| Área | Estado | Evidencia actual |
|---|---|---|
| Rama/base/producción | PASS | `develop/v1.1.0`, base `96bffb439c0d6fd946add540c0aed834236d154b`; producción no detenida ni modificada |
| Causa QA-18 | PASS | Conky 1.25.2-pre crea XID `0x200001` sin `_NET_WM_PID`; detector valida XID del log contra árbol, vista y geometría X11 |
| Backend/normalización | PASS | X11 explícito; claves modernas `text_alpha`/`own_window_color`; cabeza Xinerama 0 solo en copias Xvfb |
| Smoke | PASS | Una muestra por variante, 3+5 s, 4 vs 1 consultas NVIDIA, fallidas 0; no es una medición concluyente de CPU |
| Comparación visual Xvfb | PASS | OPT-01 y candidato 283×910; ImageMagick AE=0, capturas no vacías y logs sin errores Conky/Lua |
| Benchmark físico | PASS | 3×60 s por variante, alternado y con scopes independientes; CPU de un núcleo OPT-01 mediana 10,094 % (DE 0,132), candidato 4,157 % (DE 0,048); consultas/min 48 vs 12; fallidas 0 |
| Geometría con métricas reales | BLOCKED | CSV físico repite OPT-01 283×893 y candidato 283×876; causa de 17 px pendiente. No se acepta Design Freeze integral hasta aclararla |
| Warning font index 0 | SKIP upstream | Logs idénticos en ambas variantes; el código fuente upstream de Conky en commit `6caddca3` ordena `setup_fonts()` antes de `load_fonts()`, mientras main upstream ya carga antes. La fuente sí se ve en las capturas; no se suprimió el warning ni se parcheó Conky |
| Transparencia compositor | SKIP | Xvfb sin compositor informa que no hay visual ARGB; esta prueba no valida transparencia/composición de KDE Wayland/Xwayland |
| Arch/Fedora/local suite tras QA-18 | NOT RUN | Pendiente de ejecutar en el cierre de esta fase |
| Licencia del código derivado | BLOCKED | No existe evidencia suficiente de permiso de redistribución; no se atribuye GPLv3 unilateralmente |

Las capturas y logs de la comparación visual, smoke y benchmark se conservaron en directorios temporales privados fuera del repositorio. Los artefactos no se incorporan al repositorio. La referencia SHA256SUMS se verificó antes del smoke y después del benchmark. Las medianas actuales no se comparan con los datos históricos, obtenidos con distinto protocolo.

La revisión final y cualquier publicación quedan pendientes de resolver la diferencia física de altura, cerrar las pruebas posteriores a QA-18 y obtener permiso/licencia para el código derivado. Mensaje de commit propuesto: `fix: correct isolated X11 QA and restore OPT-01 parity`. No se creó commit ni publicación.

## Cierre de QA-18 — resultados finales

Este bloque sustituye los estados “NOT RUN” del bloque QA-18 anterior. Clasificación global: **CONDITIONAL — no publicar**.

| Validación | Estado | Resultado |
|---|---|---|
| Suite local EndeavourOS | PASS | `make test`: 86/86, exit 0 |
| Suite Arch rootless | PASS | 86/86, exit 0; imagen `sha256:cdbce410d7a983653f0090437669cfc1c6bbac0b9b4d887a9c837772c638b9e2`; red desactivada, repo read-only |
| Suite Fedora rootless | PASS | 86/86, exit 0; imagen `sha256:6177ee793438dffef135def5f7b39f43d0380f4883d91e9d559f34a3bc23b860`; red desactivada, repo read-only |
| `make audit` / ShellCheck | PASS | Exit 0; Bash, Python, Lua y unidad systemd verificados |
| `make doctor` | PASS | Exit 0; Conky y Python detectados |
| `make benchmark` | PASS | Sintético, referencia persistente; OPT-01 5 frente a candidato 1 consulta por ciclo. No es una medición de CPU física |
| Smoke físico | PASS | 3 s calentamiento + 5 s medición; XID visible, OPT-01 4 consultas y candidato 1, fallidas 0 |
| Comparación visual Xvfb | PASS | Ambas capturas 283×910, ImageMagick AE=0; datos sintéticos controlados |
| Benchmark físico | PASS | 3×60 s alternadas por variante; CPU un núcleo mediana 10,094 % / 4,157 %, DE 0,132 / 0,048; NVIDIA 48/12 consultas por minuto, 0 fallidas |
| Geometría física Design Freeze | BLOCKED | En las tres muestras: OPT-01 283×893, candidato 283×876. La causa del delta de 17 px no está demostrada |
| Xvfb compositor/transparencia KDE Wayland | SKIP | Xvfb sin compositor no valida la composición/transparencia de una sesión real KDE Wayland/Xwayland |
| Licencia redistribución código derivado | BLOCKED | Sin evidencia suficiente de licencia/permisos; no se infiere GPLv3 ni se concede licencia unilateralmente |
| `git diff --check` | PASS | Exit 0 |

La prueba sintética visual confirma paridad de los elementos que sus fixtures representan, pero no resuelve el delta de geometría medido en Conky físico. El benchmark físico es reproducible y pareado; sus resultados no se comparan con las cifras históricas, que usaron otro protocolo. La licencia y la geometría siguen siendo impedimentos materiales para publicar v1.1.0 como estable.

Las pruebas temporales se almacenaron fuera del repositorio en directorios privados bajo `/tmp`; no se incluyeron capturas/logs de laboratorio en el candidato. La referencia OPT-01 pasó verificación de manifiesto antes y después de las pruebas.

Mensaje de commit propuesto: `fix: correct isolated X11 QA and restore OPT-01 parity`

No se ejecutaron commits, staging, publicación, tags ni cambios remotos.

## QA-19 — Release Candidate final local

Este bloque es el estado vigente y reemplaza los pendientes de geometría de QA-18. El candidato conserva cambios locales en `develop/v1.1.0`; no se publicó.

| Área | Estado | Evidencia QA-19 |
|---|---|---|
| Referencia OPT-01 | PASS | Manifiesto 38/38 verificado antes del smoke y después del benchmark; árbol sin modificaciones |
| Causa 17 px / Design Freeze | PASS | OPT-01 emitía porcentaje Intel alineado y barra `execbar` solo con sensor válido; el candidato omitía esa fila. Corrección y fixture recuperan 283×893 en smoke y benchmark |
| Xvfb visual | PASS | 283×927 ambas, AE=0, sin errores de render; datos sintéticos. Xvfb no demuestra transparencia KWin |
| Smoke físico | PASS | 3 s warmup + 5 s medida, 283×893 ambas; NVIDIA 4/1 consultas y 0 fallidas |
| Benchmark físico | PASS | 3 muestras alternadas por variante, 30+60 s; OPT-01 mediana 10,061 % / DE 0,056, candidato 4,240 % / DE 0,094 CPU por núcleo; 48/12 consultas NVIDIA por minuto, fallidas 0 |
| Escenarios hardware | PASS | Suite funcional cubre Intel válido 0/100 y sensor inválido/ausente; NVIDIA disponible/ausente/timeout/campos inválidos; temperaturas y umbrales; red conectada/desconectada; swap condicional y CPUs variables. No es una captura por cada combinación |
| EndeavourOS | PASS | 87/87 pruebas, exit 0; host de QA |
| Arch | PASS | 87/87, exit 0; Podman rootless, sin red, repo read-only; imagen local digest `sha256:cdbce410d7a983653f0090437669cfc1c6bbac0b9b4d887a9c837772c638b9e2` |
| Fedora | PASS | 87/87, exit 0; Podman rootless, sin red, repo read-only; imagen local digest `sha256:6177ee793438dffef135def5f7b39f43d0380f4883d91e9d559f34a3bc23b860` |
| `make audit`, ShellCheck, `make doctor`, benchmark sintético | PASS | Exit 0; revisión estática y funciones auxiliares locales |
| Seguridad / instalador / rollback | PASS | Suites de regresión 87/87 incluyendo rutas temporales, backup, manifiesto, rollback y desinstalación; sin privilegios |
| KDE Plasma real / Xwayland / transparencia | NOT RUN | No se mostraron ventanas en escritorio activo. Hace falta validación humana en sesión aislada de KWin |
| CI remota | NOT RUN | Workflow y Containerfiles revisados; GitHub Actions no se activó ni ejecutó remotamente |
| Licencia / redistribución | BLOCKED | Upstream v1.0.1 no presenta LICENSE/COPYING; README atribuye a Haidir la adaptación, pero desconoce autor del conkyrc previo. Código de configuración/Lua derivado sin permiso acreditado |
| Git | PASS | Rama `develop/v1.1.0`, HEAD base `96bffb439c0d6fd946add540c0aed834236d154b`; sin commit, staging ni publicación |

El detalle de la investigación de licencia y fuentes primarias está en [LICENSE-INVENTORY.md](LICENSE-INVENTORY.md). La revisión consultó la [API del árbol upstream v1.0.1](https://api.bitbucket.org/2.0/repositories/dirn-typo/back-to-basic/src/1b8f3c11271d161db66118e5049bc1f08205a6bd/) y su [README upstream](https://api.bitbucket.org/2.0/repositories/dirn-typo/back-to-basic/src/1b8f3c11271d161db66118e5049bc1f08205a6bd/readme.md); no se pudo leer directamente la ficha GNOME-Look por un desafío antibot.

### Evidencia de rendimiento y visual

- CSV físico: `/tmp/bosh-qa19-benchmark-final.YB9KNiMy/benchmark.csv`
- Resumen JSON: `/tmp/bosh-qa19-benchmark-final.YB9KNiMy/benchmark.csv.json`
- Logs de muestras: `/tmp/bosh-qa19-benchmark-final.YB9KNiMy/benchmark.csv.logs/`
- Capturas `opt01.png`, `candidate.png`, `difference.png`, métricas y logs: `/tmp/bosh-qa19-visual2.QiIf0Uj9/evidence/`
- CSV smoke: `/tmp/bosh-qa19-smoke-final.3959a7ix/smoke.csv`

Los directorios de evidencia son temporales privados locales, no forman parte de los archivos publicables. RSS incluye contabilidad de páginas compartidas; no se interpreta como memoria exclusiva sin deduplicación. La mediana CPU mejoró alrededor de 57,85 % en este protocolo/host; no generalizar a otros equipos. Ver [PERFORMANCE.md](PERFORMANCE.md) para metodología y [VISUAL-VALIDATION.md](VISUAL-VALIDATION.md) para los límites de Xvfb.

### Clasificación y siguiente decisión

- **TECHNICALLY CONDITIONAL:** la paridad de contenido y geometría se corrigió y verificó con Xvfb y benchmark en EndeavourOS; falta comprobar la experiencia visual/transparencia en KDE Plasma/Xwayland real.
- **DISTRIBUTION BLOCKED:** no hay base suficiente para redistribuir el código derivado. No crear release pública hasta obtener autorización/licencia adecuada o una decisión legal/técnica posterior del mantenedor.
- **GLOBAL CONDITIONAL — NO PUBLICAR.** La validación KDE requiere procedimiento aislado con interacción del administrador; la redistribución exige resolver derechos del código heredado y del conkyrc base de autor desconocido.

No se ha generado una captura pública ni se ha iniciado GitHub Actions. No se hicieron cambios en el escritorio activo, Conky de producción, servicios ni referencia OPT-01.

### Paquete de revisión preparado (no ejecutar en esta fase)

- **Notas candidatas v1.1.0:** renderer modular con fila Intel OPT-01 restaurada; lectores consolidados; instalador/desinstalador reversible; servicio Intel opcional no instalado; batería automatizada y CI estática. Limitaciones: KDE/Xwayland real pendiente y distribución retenida por licencia.
- **Mensajes de commit sugeridos al mantenedor:** `feat: modularize Bosh To The Basic metrics`; `feat: add reversible user-scoped installation`; `test: add isolated QA and distro CI`; `docs: prepare v1.1.0 release candidate`. No se creó ninguno.
- **Staging propuesto para revisión futura:** inspeccionar `git status --short`, `git diff --check`, revisar `git diff` y archivos untracked; agrupar código y pruebas por los cambios listados, omitir `/tmp` y evidencia de hardware; verificar los staged diffs antes de crear commits. No se ejecutó `git add`.
- **Integración propuesta:** primero resolver licencia y KDE; después revisar conflictos de `develop/v1.1.0` contra `main`, probar una integración en copia temporal, y solo con autorización del mantenedor integrar, etiquetar y publicar. No ejecutar merge, tag ni release antes de esos gates.
- **Checklist de publicación actual:** licencia/permiso [ ] · evidencia KWin/Xwayland [ ] · review final del mantenedor [ ] · revisión de diff/staging [ ] · CI remota observada [ ] · notas y artefactos redistribuibles [ ]. Por tanto el candidato no es publicable aún.
