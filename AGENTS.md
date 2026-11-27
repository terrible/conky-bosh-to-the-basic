# Reglas de Bosh To The Basic

## Diseño y rendimiento

- Mantener el Design Freeze. Para v1.1.0, la referencia visual y funcional es OPT-01. Conservar geometría, fuentes, paleta, orden, textos, gráficos, alineación, umbrales y cadencias. Presentar cualquier cambio de diseño por separado para aprobación.
- Conservar el comportamiento de NVIDIA de OPT-01. OPT-02 fue rechazada por aumentar el consumo de CPU un 73,06 % respecto de OPT-01. Medir cambios de rendimiento contra la referencia bajo condiciones comparables.
- Mantener como objetivos Arch Linux, EndeavourOS y Fedora KDE. Distinguir las pruebas con datos sintéticos de la validación en un escritorio real.

## Instalación, privacidad y pruebas

- Consultar la instalación funcional en `~/.config/conky/bosh-to-the-basic/` solo para lectura. Trabajar sobre el repositorio. Probar instalación, inicio automático y recuperación con HOME, CONKY_TARGET y CONKY_AUTOSTART temporales.
- Trabajar sin sudo y sin modificar servicios del sistema. Los lectores deben tolerar fuentes de métricas opcionales ausentes.
- Importar únicamente archivos regulares revisados por nombre y contenido. Excluir enlaces a contenido externo, respaldos, cachés, archivos compilados, fondos personales, rutas de usuario e información privada. Usar datos sintéticos en las pruebas.
- Separar importación y refactorización para poder verificar paridad y revertir cada cambio. Para modificar comportamiento, escribir una prueba que falle por el motivo esperado, aplicar el cambio mínimo y volver a ejecutar las pruebas antes de refactorizar.
- Asignar un único responsable de escritura por archivo. Integrar y medir en serie cuando las tareas compartan contratos, destino de instalación o recursos de medición.

## Trabajo en v1.1.0

- Usar exclusivamente la rama `develop/v1.1.0`. Verificar rama y estado antes de editar. Preservar los cambios ajenos.
- Presentar el plan técnico antes de la refactorización. En este encargo están prohibidos commits, push, merge y releases.

## Verificación y documentación

- Ejecutar pruebas locales y registrar PASS/FAIL/SKIP en docs/DEVELOPMENT-STATUS.md.
- Las pruebas simuladas no sustituyen validación de escritorio ni benchmark real.
- Excluir bytecode y cachés Python. Limpiar solo artefactos generados por estas pruebas.
