Dividir modulos
sale_invoice_plan
sale_invoice_plan_line

Agregar parametro de validar automáticamente. Parametro en diarios de diario dummy. Agregar secuencia a rules, sugerir en wixard la primera. Llamar invoice plan y botones ejecutar plan o elegir plan. Invoice plan linea a otro modulo. Invoice plan, invoice plan linea e invoicen plan operations. Agregar change plan. Agregar plan por defecto.

Hacer un enfoque de split (diario/cia, fecha) a n facturas por porcentaje
Hacer split por porcentajes distintos en lineas?


Factor de redondeo es necesario

Rule por defecto en partner?

Analizar poner rule como m2o y no como wizard


TODO
Caso 1:
    OV - Cargar en venta, venta a 12 facturas (distinta fecha)

Caso 2:
    OV - Cargar una venta a facturar con 3 diarios distintos

Caso 3:
    OV - Cargar una venta a facturar con 2 companias distintas

Caso 4:
    FA - Cambiar tipo a una factura

Caso 5:
    FA - Cambiar la compania a una factura

Caso 6:
    FA - Mover un porcentaje a otra compania

Listo:
    Agregar tipo de comprobante
    Que no se supere el 100% ni puntual ni manera global


Al validar si el resultado es más de una factura, mostrar vista lista

Agregar campo reference a las operations

Agregar wizard para generar operaciones:
    Se selecciona un "operation rule" analogo a terminos de pagos, en realidad la misma clase heradada pero agregamos fechas de manera relativa

Agregar boton "recomputar"


En factura:
    que si hay "invoice operation" no mostrar "Validar"

