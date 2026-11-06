# Glosario de dominio — FarmaExpress (Equipo 10)

Fuente: *AF3 NEW* (Unidad 3), versión actualizada. El código usa estos términos como lenguaje ubicuo (clases, métodos y mensajes de API).

| N.º | Término | Definición |
|---|---|---|
| 1 | **Producto** | Artículo que comercializa FarmaExpress, como un medicamento o producto de cuidado personal, cuyas existencias se controlan por sucursal y, cuando corresponde, por lote y fecha de caducidad. |
| 2 | **Sucursal** | Establecimiento de FarmaExpress en el que se registran ventas, existencias, movimientos de inventario y necesidades de reposición. |
| 3 | **Lote** | Conjunto de unidades de un producto identificado mediante un código común que permite distinguirlo de otros lotes y gestionar su caducidad o retiro. |
| 4 | **Fecha de caducidad** | Fecha registrada para un producto o lote que permite determinar su estado de caducidad. Desde esa fecha, el producto no puede venderse. |
| 5 | **Estado de caducidad** | Clasificación calculada a partir de los días restantes hasta la fecha de caducidad: normal, próximo a caducar, crítico o caducado. |
| 6 | **Producto próximo a caducar** | Producto al que le faltan entre 11 y 90 días, inclusive, para llegar a su fecha de caducidad. |
| 7 | **Producto crítico** | Producto no caducado al que le faltan 10 días o menos para llegar a su fecha de caducidad. Tiene prioridad de atención sobre un producto próximo a caducar. |
| 8 | **Producto caducado** | Producto cuya fecha de caducidad es igual o anterior a la fecha actual. Debe identificarse e impedirse su venta conforme a las reglas del sistema. |
| 9 | **Lote retirado** | Lote cuya comercialización debe detenerse debido a un retiro confirmado. El sistema debe identificarlo y bloquear su venta en las sucursales. |
| 10 | **Retiro de lote** | Proceso mediante el cual se registra que un lote debe dejar de comercializarse, se identifica dónde existen unidades afectadas y se documenta su separación y gestión. |
| 11 | **Bloqueo de venta** | Restricción del sistema que impide completar una venta de un producto caducado o perteneciente a un lote retirado. |
| 12 | **Existencia registrada** | Cantidad de unidades de un producto que figura en los registros del sistema para una sucursal y, cuando corresponda, para un lote específico. Puede diferir de la cantidad física. |
| 13 | **Existencia física** | Cantidad de unidades que realmente se encuentra en la sucursal al realizar un conteo. |
| 14 | **Diferencia de inventario** | Discrepancia entre la existencia física y la existencia registrada de un producto. Debe documentarse e investigarse. |
| 15 | **Movimiento de inventario** | Operación que modifica la cantidad registrada de un producto o que, conforme al procedimiento, debe generar una actualización de esa cantidad, como una entrada o una venta. |
| 16 | **Investigación de diferencia** | Revisión realizada para determinar por qué la existencia física no coincide con la registrada. Puede incluir la revisión de movimientos y la documentación de una causa identificada o pendiente de aclaración. |
| 17 | **Merma** | Pérdida de unidades o de valor de inventario. En el contexto de FarmaExpress, puede relacionarse con productos que se pierden o caducan. |
| 18 | **Ajuste de inventario** | Modificación autorizada de la cantidad registrada, sustentada en una revisión de inventario. Debe conservarse evidencia de los valores anterior y nuevo, el motivo, la fecha, el ejecutor y el autorizador. |
| 19 | **Venta** | Operación comercial en la que se registran los productos que el cliente desea adquirir y su estado de procesamiento. |
| 20 | **Venta en proceso** | Venta que se está registrando, pero que aún no ha concluido. Se pueden corregir datos de la operación o cancelarla antes de completarla. |
| 21 | **Venta cancelada** | Operación que no llegó a completarse porque fue abandonada o no pudo continuar. Debe distinguirse de una venta completada. |
| 22 | **Venta completada** | Operación que ha concluido. No puede eliminarse ni modificarse directamente en sus datos económicos. |
| 23 | **Corrección de dato descriptivo** | Cambio autorizado de un dato descriptivo de una venta ya completada que no altera sus productos, cantidades, precios ni pagos. Debe conservarse el dato original, el nuevo valor, el motivo y los responsables. |
| 24 | **Producto de venta libre** | Producto clasificado por FarmaExpress como vendible sin receta. |
| 25 | **Medicamento con receta simple** | Categoría de medicamento que requiere una receta y la revisión correspondiente por parte del responsable de farmacia. |
| 26 | **Medicamento controlado** | Categoría de medicamento sujeta a condiciones especiales de venta y documentación. Los requisitos concretos deben verificarse con las fuentes aplicables y no deben establecerse mediante límites numéricos inventados. |
| 27 | **Receta** | Documento presentado para acreditar la prescripción de un medicamento cuando corresponde. Su aceptación depende de la revisión y de los requisitos aplicables. |
| 28 | **Revisión de receta** | Comprobación que realiza el responsable de farmacia para determinar si la documentación presentada permite continuar con la venta del medicamento correspondiente. |
| 29 | **Registro de venta especial** | Conjunto de datos que documenta una venta de medicamento que requiere información adicional, como los datos de la receta, paciente y médico cuando correspondan, el resultado de la revisión y la identidad del responsable. |
| 30 | **Sustitución de medicamento** | Reemplazo del producto solicitado por una alternativa que debe ser evaluada y autorizada por el responsable de farmacia. Si no se acepta una alternativa, no se realiza la sustitución. |
| 31 | **Cajero** | Actor responsable de registrar las ventas, identificar si se requiere receta y solicitar la intervención del responsable de farmacia cuando corresponde. |
| 32 | **Responsable de farmacia** | Actor encargado de revisar recetas, autorizar sustituciones, evaluar y confirmar necesidades de reposición, enviar solicitudes a Compras, registrar retiros de lotes y autorizar ajustes de inventario. |
| 33 | **Almacén** | Área que identifica y reporta productos faltantes, que requieren reposición y caducados; realiza conteos, documenta diferencias, separa físicamente las unidades retiradas y ejecuta los ajustes autorizados. |
| 34 | **Compras** | Área responsable de gestionar el abastecimiento de productos a partir de las solicitudes recibidas. |
| 35 | **Necesidad de reposición** | Situación en la que se identifica que una sucursal requiere abastecerse de un producto. Se identifica de forma reactiva, se revisa y confirma antes de preparar la solicitud de compra. |
| 36 | **Solicitud de compra** | Petición que el responsable de farmacia envía a Compras después de revisar y confirmar la necesidad de reposición. Puede incluir sucursal, productos, cantidades, fecha y estado de seguimiento. |
| 37 | **Disponibilidad registrada por sucursal** | Cantidad de un producto que el sistema muestra para una sucursal determinada. Permite consultar otras sucursales, pero no garantiza que la cantidad física esté actualizada ni genera una reserva. |
| 38 | **Usuario autorizado** | Persona que dispone de permisos para consultar o ejecutar determinadas funciones del sistema conforme a su rol. |
| 39 | **Control de acceso por rol** | Mecanismo que limita las consultas y operaciones que un usuario puede realizar de acuerdo con sus responsabilidades. Es especialmente importante para los datos personales y los registros de ventas especiales. |
| 40 | **Trazabilidad** | Capacidad de reconstruir las acciones realizadas sobre una operación o registro mediante información como usuario, fecha, acción y datos afectados. |
| 41 | **Historial de cambios** | Registro cronológico de las modificaciones relevantes efectuadas en el sistema. Permite conocer los valores anteriores y nuevos y quién ejecutó o autorizó el cambio cuando corresponda. |
| 42 | **Evidencia** | Información que respalda una revisión o una operación, como datos del conteo, documentos disponibles o registros de ejecución. |
| 43 | **Unidades en tránsito** | Unidades de un producto que se encuentran en proceso de traslado o entrega y cuya ubicación o recepción aún debe aclararse. En un retiro de lote, deberán permanecer pendientes de resolución. |
| 44 | **Parámetro configurable** | Valor o condición del sistema que puede ajustarse de forma controlada. Los parámetros relacionados con requisitos especiales solo se configurarán después de su verificación y deberán conservar un historial de cambios. |
| 45 | **Reporte operativo** | Presentación organizada de información para apoyar la gestión, como productos próximos a caducar, lotes retirados, productos faltantes, diferencias de inventario, ajustes y solicitudes de compra. |
| 46 | **Indicador de éxito** | Medida utilizada para evaluar si el sistema contribuye a los objetivos del negocio, como reducir pérdidas por caducidad o el tiempo entre detectar una necesidad y enviar una solicitud de compra. |
| 47 | **Línea base** | Valor inicial de un indicador, medido antes de evaluar los resultados del sistema o al comienzo de su operación, que sirve como referencia para comparar cambios posteriores. |
| 48 | **Meta inicial propuesta** | Resultado cuantificable planteado para evaluar el proyecto. Las reducciones porcentuales propuestas en el BRD son objetivos de diseño y no resultados históricos comprobados de FarmaExpress. |
| 49 | **Existencias mínimas** | Nivel mínimo de inventario que podría utilizarse como referencia para identificar una necesidad de reposición. No existe actualmente un mecanismo formal implementado para gestionarlas. |
| 50 | **Estado de solicitud de compra** | Situación en la que se encuentra una solicitud de compra durante su seguimiento. El sistema permite consultar su estado, sin presuponer una integración automática con proveedores. |
| 51 | **Autorización de excepción** | Registro que representa una autorización excepcional relacionada con una operación que requiere aprobación. Fuera del alcance implementado: sus condiciones siguen pendientes de definición en el BRD. |
| 52 | **Registro centralizado de retiros** | Mecanismo común de consulta que permite a las sucursales identificar los lotes cuyo retiro ha sido confirmado y evitar su venta. |
| 53 | **Servicio de validación de venta** | Componente de dominio (`ServicioDeValidacionDeVenta`) que coordina la comprobación de las reglas necesarias para completar una venta, incluidas caducidad, retiro, disponibilidad y revisión de receta. |
