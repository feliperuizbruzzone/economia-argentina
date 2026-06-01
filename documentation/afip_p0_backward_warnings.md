# AFIP P0 Warnings

Este documento registra las advertencias vigentes del periodo
`P0_new_xls_detail` para `Impuesto a las Ganancias Sociedades`.

Alcance actual:

- Publication years: 2015-2023.
- Fiscal years: 2014-2022.
- Formato: XLS directo.
- Clasificador: nuevo, con secciones y actividad a 3 digitos cuando la fuente la informa.
- Estado: extraccion, ensamble y validacion P0 completos.

Artefactos principales:

- Inventario P0: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory.csv`.
- CSV largo P0: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0.csv`.
- Validacion consolidada: `data/output-data/validation_reports/ganancias_sociedades_p0_long_validation.md`.
- Inventario retrospectivo auxiliar: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_p0_backward_inventory.csv`.
- Probe retrospectivo auxiliar: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_p0_backward_detector_probe.csv`.

## Resumen De Estado

| Checkpoint | Filas | Fallas | Advertencias |
|---|---:|---:|---:|
| Inventario P0 actividad | 892 | 0 | 8 |
| Ensamble P0 largo | 491435 | 0 | 0 |
| Inventario retrospectivo auxiliar | 112 | 0 | 17 |
| Probe detectores retrospectivo | 112 | 0 | 0 |

El archivo consolidado P0 valido contiene 20 cuadros de actividad
`2.3.1.1.*` y fiscal years 2014-2022. La validacion final del panel largo no
registra fallas ni advertencias porque las discontinuidades de fuente fueron
capturadas en validadores por cuadro.

## Advertencias Estructurales

1. Fiscal year 2014 incluye 13 archivos con sufijo `_2-`; se verifico que son duplicados de contenido de los archivos base para los cuadros `2.3.1.1.*`. Se ignoran en la extraccion principal.
2. Fiscal years 2014-2016 no traen los subcuadros detallados recientes `2.3.1.1.5.1.1`, `2.3.1.1.5.1.2`, `2.3.1.1.5.1.3`, `2.3.1.1.5.1.4`, `2.3.1.1.5.2.1`, `2.3.1.1.5.3.1` y `2.3.1.1.5.3.2`.
3. Fiscal year 2022, cuadro `2.3.1.1.5.2.1`, no trae fila `TOTAL`; comienza en la seccion `A`.
4. Etiquetas compuestas con guion como `267-268.` se normalizan a `267;268` para mantener claves consistentes. Esto no es homologacion sectorial.

## Advertencias Por Cuadro

| Cuadro | Fiscal years / claves | Advertencia | Tratamiento |
|---|---|---|---|
| `2.3.1.1.2.2` ventas detalladas | 2014-2015 | Faltan variables modernas de detalle de ventas, exportaciones y derechos de exportacion. | Se registran como variables source-missing; no se imputan desde agregados. |
| `2.3.1.1.2.2` ventas detalladas | 2017: `TOTAL`, `N`, `773` | `ventas_netas + derechos_exportacion` difiere del total por una anomalia de fuente; los componentes detallados si reconcilian. | Advertencia; se preservan valores fuente. |
| `2.3.1.1.2.4` resultado bruto | 2017: `TOTAL`, `N`, `773` | La identidad de resultado bruto hereda la misma diferencia de ventas 2017. | Advertencia; se preservan valores fuente. |
| `2.3.1.1.2.5` gastos operativos | 2015 | La columna rotulada como importe total de gastos operativos contiene casos; el importe total no esta observado en ese cuadro. | Se extrae como `gastos_operativos_casos`; no se imputa el monto desde componentes ni desde `2.3.1.1.2.4`. |
| `2.3.1.1.2.5` gastos operativos | 2014, 2016-2022 | `gastos_operativos_casos` no existe como columna fuente. | Variable source-missing por anio. |
| `2.3.1.1.2.5` gastos operativos | 2022, `071;072` | El total de gastos operativos difiere del cuadro `2.3.1.1.2.4`, pero los componentes del propio `2.3.1.1.2.5` reconcilian. | Advertencia; se conserva el valor especifico del cuadro. |
| `2.3.1.1.2.7` resultado contable | 2022 | Aparecen variables especificas de juegos de azar/apuestas no presentes en 2020-2021. | Se conservan como variables observadas solo en 2022. |
| `2.3.1.1.2.7` resultado contable | 2019, `352;353` vs `352` | El cuadro `2.3.1.1.2.7` usa `352;353`, mientras `2.3.1.1.1` usa `352`; el valor compartido coincide. | Se preservan ambos codigos; homologacion pendiente. |
| `2.3.1.1.3` resultado impositivo | 2014-2017 | No hay `quebranto_computable` ni `quebranto_computable_casos`. | Variables source-missing; no se derivan. |
| `2.3.1.1.5.1.1` disponibilidades | 2014-2016 | Subcuadro fuente ausente. | Cobertura 2017-2022; no se imputa desde `5.1`. |
| `2.3.1.1.5.1.2` creditos | 2014-2016 | Subcuadro fuente ausente. | Cobertura 2017-2022; no se imputa desde `5.1`. |
| `2.3.1.1.5.1.2` creditos | 2020, `352;353` | Fila solo con presentaciones, sin valores de creditos. | Advertencia; se conserva fila de presentaciones y faltantes de valor. |
| `2.3.1.1.5.1.2` creditos | 2018, `267;268` | Los componentes netos de previsiones no suman al total, pero el total coincide con `2.3.1.1.5.1`. | Advertencia; se preservan valores fuente. |
| `2.3.1.1.5.1.3` bienes de cambio | 2014-2016 | Subcuadro fuente ausente. | Cobertura 2017-2022; no se imputa desde `5.1`. |
| `2.3.1.1.5.1.4` bienes de uso | 2014-2016 | Subcuadro fuente ausente. | Cobertura 2017-2022; no se imputa desde `5.1`. |
| `2.3.1.1.5.2.1` deudas | 2014-2016 | Subcuadro fuente ausente. | Cobertura 2017-2022; no se imputa desde `5.2`. |
| `2.3.1.1.5.2.1` deudas | 2022 | No hay fila `TOTAL`. | Advertencia; no se crea total. |
| `2.3.1.1.5.3` patrimonio neto | 2014-2016 | Patrimonio inicial y final vienen separados en positivo/negativo; no hay total directo inicio/cierre. | Se preservan variables `*_positivo` y `*_negativo`; no se calcula neto en extraccion. |
| `2.3.1.1.5.3` patrimonio neto | 2014-2016 | No hay casos para aumentos/disminuciones ni resultado final contable beneficio/perdida. | Variables source-missing. |
| `2.3.1.1.5.3` patrimonio neto | 2016, `267;268` | Fila solo con presentaciones en el cuadro patrimonial; presentaciones difieren de `2.3.1.1.1` (`23` vs `53`). | Advertencia de cruce; se conservan valores fuente. |
| `2.3.1.1.5.3` patrimonio neto | 2017-2018 | No hay resultado final contable beneficio/perdida. | Variables source-missing. |
| `2.3.1.1.5.3` patrimonio neto | 2017-2022 | Ya no existen variables de patrimonio inicial/final positivo/negativo. | Variables tempranas source-missing en anios recientes. |
| `2.3.1.1.5.3.1` aumentos patrimonio | 2014-2016 | Subcuadro fuente ausente. | Cobertura 2017-2022; no se imputa desde `5.3`. |
| `2.3.1.1.5.3.2` disminuciones patrimonio | 2014-2016 | Subcuadro fuente ausente. | Cobertura 2017-2022; no se imputa desde `5.3`. |
| `2.3.1.1.5.3.2` disminuciones patrimonio | 2020, `267;268` | Fila solo con presentaciones, sin valor de disminuciones. | Advertencia; se conserva fila de presentaciones. |

## Reglas Metodologicas Vigentes

- Las advertencias no autorizan imputaciones.
- Si un valor esta en un cuadro agregado pero no en el subcuadro, se conserva como observado solo en el cuadro agregado.
- Si un componente no reconcilia con el total por anomalia puntual de fuente, se preservan ambos valores y se documenta la discrepancia.
- Las variables derivadas, neteos de positivo/negativo, ratios y empalmes quedan para una fase posterior.
- La homologacion de ramas economicas queda pendiente. No colapsar ni reemplazar `activity_code`, `activity_label_original` o `activity_section_original`.
