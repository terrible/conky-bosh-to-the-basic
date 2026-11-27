# Bosh To The Basic

[English](README.md)

**Un panel de sistema Conky de estilo clásico, adaptado a escritorios Linux modernos.**

El candidato de ingeniería v1.1.0 está congelado. Pasó las suites locales y en contenedores Arch/Fedora rootless, las pruebas aisladas Xvfb, un benchmark físico y una inspección visual reportada por el mantenedor en KDE Plasma 6.8.3 Wayland/Xwayland/KWin. La distribución pública sigue bloqueada por la licencia upstream sin resolver.

## Información del panel

- Reloj, fecha, uptime, CPU total y barras individuales para hasta cuatro núcleos.
- Memoria, SWAP opcional, almacenamiento raíz y procesos principales.
- Carga Intel y NVIDIA, memoria NVIDIA y temperaturas disponibles.
- Interfaz de red activa, dirección, totales de tráfico y gráficos separados de bajada y subida.
- Panel configurado a 273 px, con tipografía, espaciado y paleta azul/amarilla de OPT-01.

Las fuentes de hardware opcionales degradan a `N/D` o se omiten cuando OPT-01 así lo hacía. NVIDIA usa `nvidia-smi`; el recolector Intel es un recurso opcional y el instalador del tema no lo instala ni activa.

## Arquitectura

Conky renderiza la configuración X11 y los auxiliares Lua/Cairo para texto y gráficos. Python lee una única muestra acotada de hardware y genera las filas de GPU y temperaturas. Scripts Bash pequeños detectan red y distribución. El instalador Python de usuario administra el tema, la migración del autostart, respaldos privados y rollback; el desinstalador conserva las modificaciones posteriores del usuario. Ninguno instala paquetes del sistema ni requiere root.

## Compatibilidad comprobada

| Entorno | Evidencia | Límite |
|---|---|---|
| EndeavourOS anfitrión | 90 pruebas automatizadas; smoke Conky/Xvfb y benchmark físico aislados | Validación física en el equipo QA; no garantiza otros equipos |
| Arch Linux | 90 pruebas en contenedor rootless sin red | No es una prueba de escritorio KDE completo |
| Fedora | 90 pruebas en contenedor rootless sin red | No es una prueba de escritorio KDE completo |
| X11/Xvfb | Render aislado y comparación sintética; backend X11 explícito | Xvfb no incluye compositor |
| KDE Plasma 6.8.3 Wayland/Xwayland/KWin | Inspección QA-21.4 reportada por el mantenedor en salida separada: transparencia, posición, diseño, fuentes, colores, barra Intel, VRAM/carga/temperatura decimal NVIDIA y secciones del sistema correctas | La ventana temporal usó una clase distinta; no se validaron reglas KWin de la clase original/instalada |
| Wayland nativo | No es el backend de referencia | Mantener X11/Xwayland |

Conky necesita soporte Lua, Cairo y X11. El panel usa Noto Sans. Los sistemas objetivo son Arch Linux, EndeavourOS y Fedora KDE; los resultados en contenedores acreditan pruebas de software, no soporte de escritorio completo.

## Evidencia de rendimiento

En el anfitrión QA-21.3 con EndeavourOS (Intel Core i5-3330, GTX 1650), tres muestras alternadas de 60 segundos por variante dieron una mediana de CPU equivalente a un núcleo de **9,845 % en OPT-01** y **4,310 % en el candidato** (aproximadamente 56 % menos en esta ejecución). El sondeo NVIDIA fue de 48 frente a 12 consultas por minuto, sin fallos. Ambas ventanas midieron 283×893 en las ejecuciones físicas. Son datos de un equipo con Xvfb y cgroups aislados, no una garantía para otros sistemas. El método y las muestras están en el [informe de rendimiento](docs/PERFORMANCE.md); QA-19 se conserva allí como resultado histórico.

La comparación sintética Xvfb corregida midió 283×927 en ambas variantes, AE=0; el smoke/benchmark físico Xvfb midió 283×893 en ambas. Xvfb no valida la composición de KWin ni la transparencia real; QA-21.4 fue una inspección humana separada.

Conky emitió una advertencia de inicialización de fuentes en los logs. El mantenedor no observó defectos tipográficos en QA-21.4; se documenta la advertencia sin ocultarla.

## Evaluación del candidato

**No redistribuir ni instalar este candidato para uso general mientras siga pendiente la licencia.** Para QA autorizado del mantenedor en un HOME desechable, la interfaz implementada es:

```sh
./install.sh --dry-run
./install.sh
./install.sh --verify
./uninstall.sh --dry-run
./uninstall.sh
```

El instalador no descarga dependencias. Instala Conky y fuentes mediante el gestor de paquetes de la distribución solo dentro de un entorno de prueba separado. Consulta [instalación](docs/INSTALL.md), [recuperación](docs/RECOVERY.md) y [seguridad](SECURITY.md).

Para desarrollo: `make test`, `make audit`, `make doctor` y `make benchmark`. El objetivo benchmark es sintético y no mide CPU física del panel. GitHub Actions está preparado para pruebas y auditoría estática; no se afirma que haya una ejecución remota ni una publicación.

## Ecosistema Bosh Linux

Bosh To The Basic, Bosh Terminal y el futuro Bosh Desktop son proyectos independientes y modulares. Este repositorio contiene únicamente el panel Conky, su instalador, recursos y herramientas QA.

## Historia y créditos

El proyecto recupera una estética clásica de Conky y la adapta a un sistema Linux moderno. La línea visual se atribuye a **Hybrid Back To Basic**, de **Haidir (dirn)**, versión de referencia 1.0.1: [repositorio upstream Bitbucket](https://bitbucket.org/dirn-typo/back-to-basic) y [ficha GNOME-Look](https://www.gnome-look.org/p/1578329). El README upstream dice que se desconoce el autor de la configuración Conky anterior.

El árbol upstream 1.0.1 revisado en QA-19 no contiene `LICENSE`, `COPYING` ni aviso de copyright que establezca las condiciones de redistribución. La mención histórica a GPLv3 en un README de Bosh no prueba los términos del código derivado concreto. **No se asigna una licencia aquí; la redistribución pública está bloqueada hasta obtener evidencia y autorización.** Consulta el [inventario de licencias](docs/LICENSE-INVENTORY.md). El candidato no incluye wallpapers ni imágenes de vista previa de terceros.

Para cerrar el gate se necesita una licencia o permiso verificable que cubra los archivos derivados de v1.0.1, aclarar/obtener permiso respecto al conkyrc histórico cuyo autor se desconoce y demostrar la licencia o autorización de los cinco archivos OPT-01 importados. Después, el mantenedor debe escoger una licencia compatible para sus aportes y la distribución combinada.
