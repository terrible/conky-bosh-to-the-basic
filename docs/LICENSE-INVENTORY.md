# Inventario de licencias y recursos

| Recurso | Uso comprobado | Decisión | Evidencia/licencia |
|---|---|---|---|
| images/distro-1a.png | Antes lo cargaba draw_logo en Lua, pero la configuración no define lua_draw_hook_pre y el código actual no contiene draw_logo | Retirado como código muerto y sin licencia verificable | Sin referencias restantes en configuración, scripts o lista del instalador. |
| Otros 25 distro PNG | Sin referencias en configuración, Lua, scripts ni instalador | Retirados del árbol de trabajo por falta de uso/justificación | No se reescribió historial Git. |
| images/preview.png | Sin uso en configuración o instalador; README vigente no lo referencia | Retirado | Sin licencia verificable. |
| Configuración Conky y composición del panel Lua | Conservan estructura y presentación del tema Hybrid Back To Basic atribuido | Derivados; requieren confirmar y cumplir la licencia fuente | No hay LICENSE/COPYING local ni fuente primaria legible que pruebe términos exactos. |
| Cinco recursos/scripts OPT-01 auditados y sus adaptaciones | Procedencia de importación registrada; titular/licencia no acreditados aquí | Heredados o derivados pendientes de revisión de titularidad | Sin otorgamiento de licencia inferido. |
| Recolector/herramientas/instalador, pruebas, CI y documentación añadidos en v1.1.0 | Nuevos componentes del candidato, algunos integrados con el panel derivado | Código del candidato; licencia de distribución del conjunto no asignada | La autoría de archivos nuevos no licencia las partes heredadas ni resuelve la obra combinada. Confirmación del mantenedor pendiente. |

La imagen necesaria para el antiguo logo no bloquea el candidato porque la función que la usaba era código muerto. La atribución del código base permanece. Este inventario no concede derechos. No se infiere licencia por formato de archivo o ubicación.

## Evidencia primaria revisada en QA-19

Se revisó el repositorio Bitbucket de `dirn-typo/back-to-basic` en la revisión `1b8f3c11271d161db66118e5049bc1f08205a6bd` (mensaje `v1.0.1 updates`, 2024-06-23). La API primaria expone el [árbol de archivos de esa revisión](https://api.bitbucket.org/2.0/repositories/dirn-typo/back-to-basic/src/1b8f3c11271d161db66118e5049bc1f08205a6bd/) y su [README](https://api.bitbucket.org/2.0/repositories/dirn-typo/back-to-basic/src/1b8f3c11271d161db66118e5049bc1f08205a6bd/readme.md); el [commit v1.0.1](https://bitbucket.org/dirn-typo/back-to-basic/commits/1b8f3c11271d161db66118e5049bc1f08205a6bd) no publica un archivo de licencia.

El árbol revisado contiene `back-to-basic.conf`, `lua/back-to-basic.lua`, startup, instalador, README, imágenes y capturas; no contiene `LICENSE`, `COPYING` ni avisos equivalentes. El README atribuye la adaptación a Haidir (dirn), pero también dice que no conoce al autor del conkyrc anterior que obtuvo aproximadamente en 2009. Esto acredita procedencia y atribución declarada, no términos de licencia ni derecho de redistribución. La ficha GNOME-Look no se pudo verificar directamente durante esta revisión por una respuesta antibot; la mención histórica de Bosh a GPLv3 no acredita que los archivos derivados concretos estén cubiertos.

La comparación de archivos confirma que la configuración local Bosh cambia materialmente geometría, distribución y transparencia respecto del upstream; el Lua conserva estructura y funciones de hooks/Cairo con cambios de ruta. Por ello, la configuración y Lua son derivados directos, no una implementación independiente. La situación de derechos del conkyrc anterior tampoco está resuelta por la atribución de Haidir.

**Decisión QA-19:** mantener `DISTRIBUTION BLOCKED`. No añadir una licencia SPDX al conjunto ni declarar GPLv3 hasta que se acrediten términos aplicables y autorización para el código derivado. Próximos caminos: obtener documentación/permiso de titulares identificables y aclarar titularidad del conkyrc base con asesoría; o solicitar autorización del mantenedor para una futura implementación independiente de los componentes derivados. No se ha contactado a nadie ni iniciado una reescritura.

### Cierre del release freeze QA-21.4

La revisión disponible no aportó un documento de licencia aplicable a los archivos derivados de la versión 1.0.1 ni autorización de redistribución. Para levantar el bloqueo falta: (1) una copia verificable de `LICENSE`/`COPYING` u otro otorgamiento que cubra expresamente esa revisión y los archivos derivados, o permiso escrito del titular de Hybrid Back To Basic; (2) aclaración de titularidad/permiso del autor desconocido del conkyrc base incorporado históricamente; y (3) evidencia de licencia o autorización para los cinco archivos importados de OPT-01. Después, el mantenedor debe elegir una licencia compatible para los componentes propios y el agregado, respetando las condiciones upstream. La mención histórica a GPLv3 no satisface ninguno de estos requisitos. No se contactó a titulares, no se cambió el historial y no se asignó licencia unilateralmente.

## Búsqueda local de la fuente

Se buscaron README, LICENSE, COPYING y avisos en las rutas ~/Documentos/back-to-the-basic-original y ~/Documents/back-to-the-basic-original. Ninguno existe en el entorno actual. No hay copia local que acredite GPLv3.

La configuración Conky y la composición del panel Lua conservan estructura y presentación derivados del tema atribuido. Los cinco recursos/scripts importados desde OPT-01 y sus cambios también necesitan atribución/licencia demostrables; su procedencia funcional no acredita titularidad. Los módulos de métricas, lectores Intel, instalador, herramientas, pruebas, workflows y documentación se incorporaron durante el desarrollo v1.1.0, pero su autoría no concede derechos sobre las partes heredadas ni asigna unilateralmente GPLv3 al conjunto. Mantener bloqueada la publicación hasta obtener evidencia del permiso para distribuir los componentes derivados y confirmar una licencia compatible para el agregado.

No quedan PNG en el candidato. distro-1a.png no estaba activa: draw_logo no se define en el módulo actual y la configuración no activa lua_draw_hook_pre. El instalador ya no la incluye.
