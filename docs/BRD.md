# BRD — FarmaExpress (Equipo 10)

> Integrantes: Emiliano Salas Padrón (2157333), Jesús Adrián De la Cruz Domínguez (2156493), Joel Guadalupe Taméz Olmos (2158224). Curso: Componentes de Lógica de Negocio. Versión refinada para el PIA.

**BUSINESS REQUIREMENT DOCUMENT  **

**BRD —  FarmaExpress**

**Documento de Requerimientos de Negocio**

**Unidad 2: Análisis de Requerimientos de Negocio**

**1. Contexto del negocio**

FarmaExpress es una farmacia con varias sucursales que comercializa medicamentos y productos de cuidado personal. La operación requiere controlar las existencias por producto, sucursal, lote y fecha de caducidad, cuando corresponda.

Durante la venta, el cajero registra los productos y verifica si requieren receta. Cuando es necesaria una revisión especial, interviene el responsable de farmacia. Para la reposición, Almacén identifica productos faltantes, con existencias bajas o caducados; el responsable de farmacia revisa la información y envía solicitudes a Compras.

Actualmente, la reposición es reactiva y no existe un mecanismo formal de existencias mínimas implementado. La consulta de existencias de otras sucursales suele realizarse por llamadas o mensajes. Además, los registros de ciertas ventas se conservan en formatos físicos, lo que dificulta su consulta histórica.

**2. Problema de negocio**

Los principales problemas identificados son:

- Detección tardía de productos próximos a caducar.

- Riesgo de que un producto caducado o perteneciente a un lote retirado permanezca disponible para la venta.

- Visibilidad limitada de las existencias registradas en otras sucursales.

- Reposición reactiva y demora entre la identificación de una necesidad y la solicitud de compra.

- Investigación manual de diferencias entre existencias físicas y registradas.

- Consulta lenta de registros físicos relacionados con medicamentos de requisitos especiales.

- Necesidad de conservar evidencia sobre correcciones y ajustes de inventario.

**3. Objetivo del negocio**

Mejorar el control de existencias y la trazabilidad de las operaciones de FarmaExpress mediante un sistema que facilite la detección de productos próximos a caducar, la gestión de lotes retirados, la consulta de existencias por sucursal, la documentación de diferencias de inventario y el seguimiento de solicitudes de compra.

El sistema también deberá facilitar la consulta autorizada de registros de ventas especiales y conservar un historial verificable de las acciones realizadas.

**4. Stakeholders y  responsabilidades**

| Stakeholder | Responsabilidades |
| --- | --- |
| Cliente | Solicita productos y proporciona la documentación necesaria cuando corresponda. |
| Cajero | Registra las ventas, identifica si un producto requiere receta y solicita la intervención del responsable cuando es necesario. |
| Responsable de farmacia | Revisa recetas, autoriza sustituciones, evalúa necesidades de reposición, envía solicitudes a Compras, registra retiros de lotes y autoriza ajustes de inventario. |
| Almacén | Identifica productos faltantes, próximos a caducar o caducados; realiza conteos, documenta diferencias, separa físicamente los lotes retirados y ejecuta ajustes autorizados. |
| Compras | Gestiona el abastecimiento a partir de las solicitudes recibidas. |

**5. Alcance del sistema**

**5.1 Incluido en el alcance**

- Registrar y consultar productos, sucursales, lotes y fechas de caducidad.

- Clasificar productos por proximidad de caducidad.

- Identificar productos caducados para impedir su venta conforme a las reglas del sistema.

- Registrar retiros de lotes y bloquear su venta en las sucursales.

- Consultar las existencias registradas de otras sucursales para usuarios autorizados.

- Documentar productos faltantes y necesidades de reposición.

- Registrar y consultar solicitudes de compra.

- Apoyar la revisión de recetas y la autorización de sustituciones por el responsable de farmacia.

- Digitalizar los datos necesarios de ventas de medicamentos que requieran registros especiales, con acceso restringido.

- Documentar e investigar diferencias de inventario.

- Controlar la autorización y ejecución de ajustes de inventario.

- Mantener un historial de cambios relevantes.

- Generar reportes operativos y medir indicadores de éxito.

**5.2 Fuera del  alcance   inicial**

- Reservar productos en otras sucursales.

- Gestionar transferencias de inventario entre sucursales.

- Implementar automáticamente niveles mínimos de existencias como si ya fueran una regla operativa vigente.

- Automatizar pedidos a proveedores sin definir una integración específica.

- Permitir devoluciones ordinarias o cancelar y modificar libremente una venta después de completarla.

- Establecer límites legales numéricos para medicamentos controlados sin una fuente verificada.

- Sustituir la evaluación profesional del responsable de farmacia.

**6. Reglas de negocio**

**RN-01. Clasificación por caducidad**

La clasificación se calculará a partir de la fecha de caducidad registrada y la fecha actual.

| Estado | Regla |
| --- | --- |
| Normal | Faltan más de 90 días para caducar. |
| Próximo a caducar | Faltan entre 11 y 90 días, inclusive. |
| Crítico | Faltan 10 días o menos y el producto aún no ha caducado (días restantes ≥ 1). |
| Caducado | La fecha actual es igual o posterior a la fecha de caducidad. |

La clasificación crítica tendrá prioridad sobre la de próximo a caducar. Un producto caducado no deberá venderse; no puede venderse desde el mismo día de la fecha de caducidad.

**RN-02. Retiro de lotes**

Cuando el responsable de farmacia registre un retiro confirmado, el sistema deberá marcar el lote como retirado y bloquear su venta en todas las sucursales. Almacén será responsable de localizar y separar físicamente las unidades afectadas y registrar las cantidades identificadas y retiradas.

Las unidades en tránsito quedarán pendientes de resolución y no podrán ponerse a la venta hasta que se aclare su situación. Cada actividad relevante deberá quedar registrada con fecha, usuario y estado.

**RN-03. Consulta entre sucursales**

Los usuarios autorizados podrán consultar las existencias registradas de un producto en otras sucursales. La consulta será informativa: no reservará unidades ni generará transferencias.

**RN-04. Reposición reactiva**

La identificación de necesidades de reposición continuará siendo reactiva en el alcance inicial. Almacén reportará las necesidades; el responsable de farmacia las revisará y enviará solicitudes a Compras. El sistema documentará y permitirá consultar las solicitudes, sin asumir que se realizan pedidos automáticos.

**RN-05. Revisión de recetas**

Las ventas que requieran revisión no podrán completarse hasta que el responsable de farmacia haya revisado la documentación y registrado el resultado correspondiente. Una receta incompleta, vencida o no aceptada según el procedimiento aplicable impedirá completar la venta del medicamento correspondiente.

**RN-06. Sustitución de medicamentos**

La sustitución solo podrá ser autorizada por el responsable de farmacia. El sistema deberá registrar el producto solicitado, la alternativa, el motivo y el responsable que autorizó la decisión. Si no se acepta ninguna alternativa, no se realizará la sustitución.

**RN-07. Correcciones de ventas**

Antes de completar el pago, el cajero podrá corregir los datos de la operación o cancelarla. Una venta completada no podrá eliminarse ni modificarse directamente en sus productos, cantidades, precios o pagos.

Se permitirá solicitar una corrección de datos descriptivos que no alteren la operación económica, previa autorización del responsable de farmacia. La corrección deberá conservar el dato original, el dato corregido, el motivo, la fecha, el ejecutor y el autorizador.

**RN-08. Investigación de diferencias de inventario**

Toda diferencia entre la cantidad física y la registrada deberá documentarse y revisarse. Se registrarán producto, sucursal, lote cuando corresponda, cantidades, fecha y responsable del conteo.

La investigación incluirá la revisión de movimientos pertinentes y la documentación de la causa identificada o del estado pendiente de aclaración. Las diferencias recurrentes o relacionadas con productos caducados, retirados o de especial control tendrán prioridad.

**RN-09. Ajustes de inventario**

Un ajuste deberá estar respaldado por un registro de diferencia y una autorización. Almacén podrá realizar el conteo y ejecutar el ajuste aprobado, pero no podrá autorizar su propia corrección. El responsable de farmacia autorizará el ajuste cuando la evidencia sea suficiente.

Si la causa no está clara o se requiere una investigación adicional, el ajuste permanecerá pendiente. El historial deberá conservar la cantidad anterior, la nueva cantidad, el motivo, la evidencia disponible, el ejecutor, el autorizador y la fecha.

**RN-10. Medicamentos controlados**

Los límites y condiciones específicos solo se configurarán después de verificar los requisitos aplicables mediante fuentes oficiales o documentación competente. El sistema no utilizará límites numéricos inventados.

El acceso a la información de pacientes, médicos y recetas estará restringido según el rol. Las consultas y modificaciones relevantes deberán quedar registradas.

**7. Necesidades de negocio**

| ID | Necesidad |
| --- | --- |
| NB-01 | Identificar productos próximos a caducar, críticos y caducados. |
| NB-02 | Registrar retiros de lotes y bloquear su venta en todas las sucursales. |
| NB-03 | Consultar las existencias registradas en otras sucursales. |
| NB-04 | Identificar y reportar productos faltantes o que requieren reposición. |
| NB-05 | Coordinar las actividades de Almacén, responsable de farmacia y Compras. |
| NB-06 | Controlar las ventas que requieren revisión de recetas o autorización especial. |
| NB-07 | Consultar registros digitales de ventas especiales según permisos. |
| NB-08 | Investigar y documentar diferencias de inventario. |
| NB-09 | Autorizar, ejecutar y auditar ajustes de inventario. |
| NB-10 | Reducir el tiempo entre la identificación de una necesidad y el envío de una solicitud de compra. |
| NB-11 | Conservar trazabilidad de correcciones y acciones relevantes. |
| NB-12 | Medir la efectividad del sistema mediante indicadores definidos. |

**8.  Requerimientos   funcionales**

| ID | Requerimiento |
| --- | --- |
| RF-01 | El sistema deberá calcular el estado de caducidad a partir de la fecha registrada. |
| RF-02 | El sistema deberá identificar los productos caducados y evitar que se completen ventas con ellos. |
| RF-03 | El sistema deberá permitir registrar un retiro de lote confirmado. |
| RF-04 | El sistema deberá bloquear la venta de un lote retirado en todas las sucursales. |
| RF-05 | El sistema deberá registrar las cantidades identificadas y retiradas durante la ejecución del retiro. |
| RF-06 | El sistema deberá permitir consultar existencias registradas por producto y sucursal a usuarios autorizados. |
| RF-07 | El sistema deberá permitir registrar necesidades de reposición y solicitudes de compra. |
| RF-08 | El sistema deberá registrar el resultado de la revisión de recetas y la identidad del responsable. |
| RF-09 | El sistema deberá registrar los datos de ventas especiales que correspondan a la categoría del medicamento y al procedimiento configurado. |
| RF-10 | El sistema deberá restringir el acceso a los registros que contengan datos personales o información de recetas. |
| RF-11 | El sistema deberá permitir registrar diferencias entre existencias físicas y registradas. |
| RF-12 | El sistema deberá permitir documentar la investigación de diferencias y su causa o estado pendiente. |
| RF-13 | El sistema deberá permitir autorizar y ejecutar ajustes de inventario, conservando el historial. |
| RF-14 | El sistema deberá permitir correcciones autorizadas de datos descriptivos sin modificar directamente los datos económicos de una venta completada. |
| RF-15 | El sistema deberá generar reportes por sucursal, producto, lote, periodo y estado cuando esos filtros sean aplicables. |
| RF-16 | El sistema deberá conservar la identidad del usuario, fecha y detalle de las modificaciones relevantes. |
| RF-17 | El sistema deberá registrar los estados y fechas de seguimiento de las solicitudes de compra. |
| RF-18 | El sistema deberá permitir configurar los parámetros operativos validados para medicamentos de requisitos especiales, sin incorporar valores legales no verificados. |

**9.  Requerimientos  no  funcionales**

- **RNF-01. Control de acceso:** los usuarios solo podrán consultar o modificar información acorde con sus permisos.

- **RNF-02. Trazabilidad:** las acciones relevantes deberán conservar usuario, fecha, acción y datos afectados.

- **RNF-03. Integridad:** las cantidades, lotes y fechas deberán validarse para reducir registros inconsistentes.

- **RNF-04. Confidencialidad:** los datos de pacientes, médicos y recetas deberán protegerse mediante acceso restringido.

- **RNF-05. Disponibilidad de información:** las consultas entre sucursales deberán mostrar las existencias registradas disponibles en el sistema.

- **RNF-06. Auditabilidad:** los registros de ventas especiales, retiros y ajustes deberán poder consultarse por usuarios autorizados.

- **RNF-07. Configurabilidad:** los parámetros operativos que requieran validación deberán poder actualizarse de forma controlada y con historial.

- **RNF-08. Usabilidad:** los estados de caducidad, los lotes retirados y las diferencias pendientes deberán distinguirse claramente en las consultas y reportes.

**10. Datos  principales  del  sistema**

- **Producto:** identificador, nombre y categoría.

- **Sucursal:** identificador y datos de identificación de la ubicación.

- **Lote:** identificador, producto asociado, fecha de caducidad y estado.

- **Existencia:** producto, sucursal, lote cuando corresponda y cantidad registrada.

- **Venta:** folio, fecha, sucursal, cajero, productos y estado de la operación.

- **Registro de venta especial:** folio relacionado, datos requeridos de la receta, paciente y médico cuando correspondan, resultado de revisión y responsable.

- **Retiro de lote:** producto, lote, fecha, sucursales afectadas, cantidades y estado de ejecución.

- **Diferencia de inventario:** cantidad registrada, cantidad física, causa o estado pendiente y responsable.

- **Ajuste de inventario:** valores anterior y nuevo, motivo, evidencia, ejecutor y autorizador.

- **Solicitud de compra:** sucursal, productos, cantidades solicitadas, fecha, responsable solicitante y estado.

Los campos personales y de receta se recopilarán únicamente cuando correspondan al procedimiento aplicable. Su acceso y conservación deberán respetar los requisitos pertinentes.

**11. Indicadores de éxito**

Se proponen los siguientes indicadores para evaluar el sistema. Los porcentajes son metas iniciales de diseño, no datos históricos ni resultados comprobados de FarmaExpress.

| Indicador | Forma de medición | Meta inicial propuesta |
| --- | --- | --- |
| Pérdidas por caducidad | Valor o cantidad de pérdidas por caducidad comparados con la línea base. | Reducir 20 % al sexto mes. |
| Compras evitables por existencias en otras sucursales | Compras identificadas como evitables porque existía disponibilidad registrada en otra sucursal. | Reducir 15 % al sexto mes. |
| Tiempo de reposición inicial | Tiempo entre la detección documentada de una necesidad y el envío de la solicitud a Compras. | Reducir 25 % al sexto mes. |
| Integridad de registros especiales | Porcentaje de registros que contienen todos los campos aplicables. | Alcanzar 95 %. |
| Gestión de lotes retirados | Porcentaje de retiros registrados cuyo bloqueo y ejecución por sucursal están documentados. | Alcanzar 100 % de trazabilidad. |
| Clasificación de caducidad | Porcentaje de productos con fecha válida clasificados correctamente por el sistema. | Alcanzar 100 % de clasificación automática de los registros completos. |

Durante los primeros 30 días de operación se recopilará la línea base de los indicadores que dependan de resultados operativos. La evaluación comparativa se realizará al sexto mes. La meta de trazabilidad de retiros se refiere a los eventos registrados y no garantiza por sí sola que todas las unidades físicas hayan sido localizadas; esa confirmación requiere la ejecución y documentación por sucursal.

**12.  Supuestos  y  restricciones**

- Las existencias mostradas representan las cantidades registradas y no garantizan que el conteo físico esté actualizado.

- La consulta entre sucursales no implica reserva ni transferencia.

- La reposición continúa siendo reactiva en el alcance inicial.

- Los lotes y las fechas de caducidad deberán registrarse correctamente para que las reglas funcionen.

- La información de ventas especiales tendrá permisos específicos.

- La revisión profesional seguirá siendo responsabilidad del responsable de farmacia.

- Los límites legales específicos no se incorporarán hasta contar con requisitos verificados.

- El bloqueo de lotes retirados será una función del sistema; la separación física y la confirmación de cantidades dependerán de Almacén.

- Los objetivos porcentuales son metas de diseño que deberán evaluarse contra una línea base.

- Los requisitos de conservación de registros y datos personales deberán respetar la normativa aplicable.

**13.  Trazabilidad  de  decisiones**

| Decisión | Resultado incorporado |
| --- | --- |
| 1. Plazos de caducidad | Normal: más de 90 días; próximo: 11–90 días; crítico: 1–10 días; caducado: fecha actual igual o posterior a la de caducidad. |
| 2. Retiro de lotes | Registro centralizado, bloqueo de venta, ejecución física por Almacén y trazabilidad por sucursal. |
| 3. Registros de ventas especiales | Campos digitales definidos, acceso por rol e historial de acciones. |
| 4. Correcciones de ventas | Correcciones previas al cierre; después, solo correcciones descriptivas autorizadas sin alterar los datos económicos. |
| 5. Investigación de diferencias | Todas las diferencias se documentan; las de causa incierta, recurrentes o de especial control requieren investigación adicional. |
| 6. Ajustes de inventario | Almacén registra y ejecuta; el responsable de farmacia autoriza; queda historial completo. |
| 7. Medicamentos controlados | No se inventan límites numéricos; se incorporan solo después de verificar los requisitos aplicables. |
| 8. Indicadores de éxito | Se definen fórmulas, metas iniciales y línea base para la evaluación al sexto mes. |

**14. Conclusión**

El BRD actualizado define las necesidades de negocio, las reglas operativas y los requerimientos funcionales y no funcionales para mejorar el control de inventario, la gestión de caducidad y retiros, la consulta entre sucursales y la trazabilidad de las operaciones.

Las decisiones incorporadas permiten continuar con las historias de usuario, los criterios de aceptación, los diagramas BPMN y el modelo de dominio sin introducir reservas o transferencias entre sucursales ni asumir que la farmacia ya cuenta con automatización de existencias mínimas.

