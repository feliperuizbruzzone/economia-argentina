# AFIP Ganancias Sociedades Warnings By Period

Este documento consolida las advertencias y notas estructurales de los periodos
P0-P6 del capitulo `Impuesto a las Ganancias Sociedades`.

Regla general: las advertencias documentan discontinuidades o anomalías de
fuente. No autorizan imputaciones, neteos, empalmes sectoriales finos ni
reemplazo de valores observados.

## P0: XLS Directo Nuevo, Fiscal 2014-2022

Periodo: `P0_new_xls_detail`.

Estado de validacion:

- Inventario P0 actividad: 892 filas, 0 fallas, 8 advertencias.
- Ensamble P0 largo: 491.435 filas, 0 fallas, 0 advertencias.
- Inventario retrospectivo auxiliar: 112 filas, 0 fallas, 17 advertencias.
- Probe retrospectivo auxiliar: 112 filas, 0 advertencias.

Advertencias estructurales:

- Fiscal year 2014 incluye archivos con sufijo `_2-`; se verifico que son duplicados de contenido para cuadros `2.3.1.1.*` y se ignoran en la extraccion principal.
- Fiscal years 2014-2016 no traen los subcuadros recientes `2.3.1.1.5.1.1`, `2.3.1.1.5.1.2`, `2.3.1.1.5.1.3`, `2.3.1.1.5.1.4`, `2.3.1.1.5.2.1`, `2.3.1.1.5.3.1` y `2.3.1.1.5.3.2`.
- Fiscal year 2022, cuadro `2.3.1.1.5.2.1`, no trae fila `TOTAL`; comienza en la seccion `A`.
- Etiquetas compuestas con guion como `267-268.` se normalizan a `267;268` para mantener claves consistentes. Esto no es homologacion sectorial.

Advertencias por cuadro:

| Cuadro | Fiscal years / claves | Advertencia | Tratamiento |
|---|---|---|---|
| `2.3.1.1.2.2` | 2014-2015 | Faltan variables modernas de detalle de ventas, exportaciones y derechos de exportacion. | Source-missing; no imputar. |
| `2.3.1.1.2.2` | 2017: `TOTAL`, `N`, `773` | `ventas_netas + derechos_exportacion` difiere del total por anomalia de fuente; los componentes detallados si reconcilian. | Preservar valores fuente. |
| `2.3.1.1.2.4` | 2017: `TOTAL`, `N`, `773` | La identidad de resultado bruto hereda la diferencia de ventas 2017. | Preservar valores fuente. |
| `2.3.1.1.2.5` | 2015 | La columna rotulada como importe total de gastos operativos contiene casos; el importe total no esta observado en ese cuadro. | Extraer como `gastos_operativos_casos`. |
| `2.3.1.1.2.5` | 2014, 2016-2022 | `gastos_operativos_casos` no existe como columna fuente. | Source-missing. |
| `2.3.1.1.2.5` | 2022, `071;072` | El total de gastos operativos difiere del cuadro `2.3.1.1.2.4`, pero los componentes del propio cuadro reconcilian. | Conservar valor especifico del cuadro. |
| `2.3.1.1.2.7` | 2022 | Aparecen variables especificas de juegos de azar/apuestas no presentes en 2020-2021. | Conservar solo como observadas en 2022. |
| `2.3.1.1.2.7` | 2019, `352;353` vs `352` | Codigo compuesto distinto respecto de `2.3.1.1.1`; el valor compartido coincide. | Preservar ambos codigos. |
| `2.3.1.1.3` | 2014-2017 | No hay `quebranto_computable` ni `quebranto_computable_casos`. | Source-missing. |
| `2.3.1.1.5.1.*` | 2014-2016 | Subcuadros de disponibilidades, creditos, bienes de cambio y bienes de uso ausentes. | No imputar desde `5.1`. |
| `2.3.1.1.5.1.2` | 2020, `352;353` | Fila solo con presentaciones, sin valores de creditos. | Conservar fila y faltantes. |
| `2.3.1.1.5.1.2` | 2018, `267;268` | Componentes netos de previsiones no suman al total, pero el total coincide con `2.3.1.1.5.1`. | Preservar valores fuente. |
| `2.3.1.1.5.2.1` | 2014-2016 | Subcuadro de deudas ausente. | No imputar desde `5.2`. |
| `2.3.1.1.5.2.1` | 2022 | No hay fila `TOTAL`. | No crear total. |
| `2.3.1.1.5.3` | 2014-2016 | Patrimonio inicial/final separado en positivo y negativo; no hay total directo. | No calcular neto en extraccion. |
| `2.3.1.1.5.3` | 2016, `267;268` | Fila patrimonial solo con presentaciones; difiere de `2.3.1.1.1` (`23` vs `53`). | Preservar valores fuente. |
| `2.3.1.1.5.3.1` y `2.3.1.1.5.3.2` | 2014-2016 | Subcuadros de aumentos/disminuciones patrimoniales ausentes. | No imputar desde `5.3`. |
| `2.3.1.1.5.3.2` | 2020, `267;268` | Fila solo con presentaciones, sin valor de disminuciones. | Conservar fila de presentaciones. |

## P1: HTML Nuevo, Fiscal 2013

Periodo: `P1_new_html_detail`.

Estado:

- Inventario: 13 cuadros de actividad.
- Extraccion larga: 37.088 filas.
- Validacion: 0 fallas, 0 advertencias.

Notas estructurales:

- El ZIP 2014 esta en formato HTML exportado desde Excel, no XLS directo.
- Se prefiere el archivo/hoja secundaria con sufijo `_2` cuando contiene mayor detalle de actividad.
- Se excluyen secciones de `Estructura porcentual`.
- Mantiene clasificador nuevo y montos en millones de pesos corrientes.
- No se observan los subcuadros patrimoniales recientes `2.3.1.1.5.1.1` a `2.3.1.1.5.3.2`.

## P2: HTML Viejo En Millones, Fiscal 2012

Periodo: `P2_old_html_detail_millions`.

Estado:

- Inventario: 13 cuadros de actividad.
- Extraccion larga: 27.208 filas.
- Validacion: 0 fallas, 0 advertencias.

Notas estructurales:

- El ZIP 2013 esta en formato HTML exportado desde Excel.
- El detalle maximo de actividad esta en `Archivos/<table_id>_archivos/sheet002.htm`.
- Primer tramo incorporado con `classifier_period = old`.
- Montos en millones de pesos corrientes; comparables monetariamente con P0-P1 usando `value_pesos_current`.
- El parser recorta columnas vacias finales generadas por estilos o `colspan`.

## P3: HTML Viejo En Miles, Fiscal 2008-2011

Periodo: `P3_old_html_detail_thousands`.

Estado:

- Inventario: 49 pares publication year x cuadro.
- Extraccion larga: 97.775 filas.
- Validacion: 0 fallas, 10 advertencias.

Advertencias vigentes:

- Fiscal year 2008, cuadro `2.3.1.1.2.1`: el residual de costos aparece como `OTROS`; se conserva como `costos_otros`, no como `gastos_vinculados_al_costo`.
- Fiscal year 2008, cuadros `2.3.1.1.2.2`, `2.3.1.1.2.3` y `2.3.1.1.2.4`: el `source_table_id` conserva la numeracion original, aunque el contenido corresponde a familias que en anios posteriores aparecen desplazadas.
- Fiscal year 2008 no trae los cuadros `2.3.1.1.2.5`, `2.3.1.1.2.6` y `2.3.1.1.2.7`.
- Fiscal year 2008, cuadros `2.3.1.1.3` y `2.3.1.1.4`: solo se encontro `sheet001.htm`; no hay detalle de actividad a 3 digitos.
- Fiscal year 2010, cuadro `2.3.1.1.2.3`: solo se encontro `sheet001.htm`; no hay detalle de actividad a 3 digitos.

Notas:

- Los ZIP 2009-2012 estan en HTML exportado desde Excel.
- Se busca por sufijo de cuadro, no por carpeta raiz fija.
- Se prefiere `sheet002.htm` cuando existe.
- Los montos se leen en `miles_pesos_corrientes`; `value_pesos_current` multiplica por 1.000.

## P4: CAB/XLS Viejo En Miles, Fiscal 2002-2007

Periodo: `P4_old_cab_xls_detail_thousands`.

Estado:

- Inventario: 60 pares anio-cuadro.
- Extraccion larga: 132.088 filas.
- Variables canonicas observadas: 111.
- Validacion: 0 fallas, 25 advertencias.

Advertencias documentadas:

- Los XLS fuente estan dentro de `AFIP.CAB`; el pipeline extrae a carpetas temporales y requiere `cabextract`.
- En todos los cuadros P4 se usa la continuacion `_2.xls`, que contiene el maximo detalle de actividad disponible.
- El cuadro `2.3.1.1.2.1` usa componente `OTROS` dentro de costos; se conserva como `costos_otros` y `costos_otros_casos`.
- La numeracion P4 condensa resultados en menos cuadros que P0-P2:
  - `2.3.1.1.2.2`: resultado bruto, venta de acciones, deudores incobrables y otros gastos operativos.
  - `2.3.1.1.2.3`: inversiones permanentes, financieros, contratos derivados y otros ingresos/egresos.
  - `2.3.1.1.2.4`: extraordinarios, impuesto a las ganancias y resultado contable.
- Fiscal year 2007, actividad `142. Explotacion de minas y canteras n.c.p.`, en `2.3.1.1.2.1`, trae solo `presentaciones_total`; las demas variables estan en blanco y no se imputan.

## P5: CAB/XLS Numeracion Legacy, Fiscal 1999-2001

Periodo: `P5_old_cab_xls_detail_legacy_numbering`.

Estado:

- Inventario: 18 pares fiscal year x cuadro.
- Extraccion larga: 31.229 filas.
- Variables canonicas observadas: 114.
- Validacion: 0 fallas, 35 advertencias.

Regla de fuente canonica:

- Usar publication year 2002 como fuente canonica para fiscal years 1999-2001.
- En el CAB 2002, los sufijos `_2000`, `_2001` y `_2002` se mapean a fiscal years 1999, 2000 y 2001.
- Publicaciones 2000 y 2001 se tratan como duplicados anteriores para esta fase.

Advertencias:

- Fiscal years 1999-2000 usan esquema compacto de cuatro cuadros `3.3.1.1.1` a `3.3.1.1.4`.
- Fiscal year 2001 usa numeracion expandida `3.3.1.1.1`, `3.3.1.1.2.1` a `3.3.1.1.2.4`, `3.3.1.1.3`, `3.3.1.1.4`, `3.3.1.1.5.1`, `3.3.1.1.5.2` y `3.3.1.1.5.3`.
- `presentaciones_con_ganancia_neta_imponible` aparece en 1999-2000 donde luego se usa `presentaciones_con_impuesto_determinado`.
- `resultado_final_del_ejercicio` se mapea a variables canonicas de resultado contable.
- `quebranto` se mapea a variables canonicas de perdida de resultado impositivo.
- `costos_otros` se observa en fiscal 2001 y no debe forzarse hacia 1999-2000.
- Componentes de activo, pasivo y patrimonio estan disponibles en fiscal 2001, pero no en el balance agregado 1999-2000.
- `Actividades no bien especificadas 9/` se clasifica como `other_activity`, no como rama de 3 digitos.

## P6: XLS Directo Antiguo, Fiscal 1997-1998

Periodo: `P6_legacy_broad_activity`.

Estado:

- Inventario: 8 pares fiscal year x cuadro.
- Extraccion larga: 3.044 filas.
- Variables canonicas observadas: 36.
- Validacion: 0 fallas, 24 advertencias.

Advertencias:

- Fiscal year 1997 usa numeracion `4.4.*` y solo actividad amplia.
- Fiscal year 1998 usa numeracion `3.3.*` y continuaciones `_2.xls` con detalle de actividad a 3 digitos.
- Fiscal year 1997, cuadro `4.4.1.1.3`, contiene variables de ajustes fiscales no observadas en fiscal year 1998.
- P6 usa `presentaciones_con_ganancia_neta_imponible`; no debe unirse automaticamente con `presentaciones_con_impuesto_determinado`.
- `resultado final del ejercicio` se mapea a resultado contable canonico.
- `quebranto` se mapea a perdida de resultado impositivo canonico.
- Los balances son agregados; no hay componentes de activo, pasivo o patrimonio.

## Reglas Transversales

- Preservar `source_table_id`, `activity_code`, `activity_label_original` y `activity_section_original`.
- No imputar subcuadros ausentes desde cuadros agregados.
- No calcular netos, ratios, deflactaciones ni empalmes finos dentro de la extraccion.
- Usar `value_pesos_current` para comparabilidad monetaria de miles/millones.
- Usar `rama_comun_*` solo para comparabilidad amplia y `rama_detalle_homologada_*` para conservar detalle fuente por clasificador.
