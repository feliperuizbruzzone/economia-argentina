# AFIP Variable Comparability

Este documento resume la comparabilidad preliminar de variables de interes para el bloque
`Impuesto a las Ganancias Sociedades`.

Alcance de esta version:

- No implementa extraccion.
- Se basa en inspeccion local de titulos, encabezados y filas iniciales de cuadros.
- Usa `publication_year` para el anio del ZIP y `fiscal_year` para el anio declarado en el cuadro.
- Para Ganancias Sociedades, el anio fiscal observado esta rezagado respecto del ZIP: por ejemplo, el ZIP 2023 contiene el cuadro de fiscal year 2022.
- La estrategia definida es conservar el maximo nivel de desagregacion disponible y producir una base en formato largo.

## Esquema Largo Objetivo

La unidad de fila propuesta para la base cruda larga es una celda estadistica normalizada:

```text
fiscal_year x source_table_id x dimension_type x dimension_value x variable_name
```

Campos minimos recomendados:

- `publication_year`
- `fiscal_year`
- `archive_filename`
- `period_id`
- `source_table_id`
- `source_table_path`
- `source_table_title`
- `table_family`
- `universe`
- `dimension_type`
- `dimension_value`
- `activity_level`
- `activity_code`
- `activity_label_original`
- `activity_section_original`
- `classifier_period`
- `variable_name`
- `value`
- `unit_original`
- `value_pesos_current`
- `source_note`

## Periodos Analiticos Observados

| Periodo analitico | ZIPs principales | Fiscal years | Clasificador observado | Formato | Unidad monetaria observada |
|---|---:|---:|---|---|---|
| `P0_new_xls_detail` | 2015-2023 | 2014-2022 | Clasificador nuevo, seccion y detalle 3 digitos | XLS directo | Millones de pesos corrientes |
| `P1_new_html_detail` | 2014 | 2013 | Clasificador nuevo, seccion y detalle 3 digitos | HTML exportado desde Excel | Millones de pesos corrientes |
| `P2_old_html_detail_millions` | 2013 | 2012 | Clasificador viejo, seccion y detalle 3 digitos en hoja secundaria | HTML exportado desde Excel | Millones de pesos corrientes |
| `P3_old_html_detail_thousands` | 2009-2012 | 2008-2011 | Clasificador viejo, seccion y detalle 3 digitos en `sheet002.htm` | HTML exportado desde Excel | Miles de pesos corrientes |
| `P4_old_cab_xls_detail_thousands` | 2003-2008 | 2002-2007 | Clasificador viejo, seccion y detalle 3 digitos en continuaciones `_2` | XLS dentro de CAB | Miles de pesos corrientes |
| `P5_old_cab_xls_detail_legacy_numbering` | 2002 canonico | 1999-2001 | Clasificador viejo, seccion y detalle 3 digitos en continuaciones `_2` | XLS dentro de CAB | Miles de pesos corrientes |
| `P6_legacy_broad_activity` | 1998-1999 | 1997-1998 | Fiscal 1997 actividad amplia; fiscal 1998 detalle 3 digitos en `_2` | XLS directo | Miles de pesos corrientes |

## Quiebres Principales

| Quiebre | Ubicacion | Efecto |
|---|---|---|
| Rezago fiscal | Todo Ganancias Sociedades | `publication_year` no equivale a `fiscal_year`; usar ambos identificadores. |
| Numeracion de cuadros | 1998: `4.4.*`; 1999-2002: `3.3.*`; desde 2003: `2.3.*` | Los cuadros equivalentes cambian de codigo aunque mantengan contenido similar. |
| Contenedor/formato | XLS directo, CAB, HTML, XLS directo | Afecta parser, no necesariamente concepto economico. |
| Unidad monetaria | Hasta fiscal 2011: miles; desde fiscal 2012: millones | Requiere normalizar a una unidad comun antes de comparar montos. |
| Clasificador sectorial | Fiscal 2013 en adelante cambia la estructura de actividades | No comparar sectores directamente sin tabla de correspondencia. |
| Nivel de detalle sectorial | Fiscal 1997 no muestra detalle 3 digitos; fiscal 1998 lo ubica en continuaciones `_2`; 2008-2012 lo ubican en hojas HTML secundarias | Para maxima desagregacion hay que leer continuaciones y hojas secundarias, no solo el cuadro visible inicial. |
| Conteo condicional | Hasta fiscal 2000 aparece `con ganancia neta imponible`; desde fiscal 2001 aparece `con impuesto determinado` | No unir esos conteos como una misma variable sin decision metodologica. |
| Desagregacion contable | Desde fiscal 2002 se expanden componentes de resultados, activo, pasivo y patrimonio | Los agregados principales son mas comparables que los componentes finos. |

## Tabla De Comparabilidad Por Variable

| Variable canonica propuesta | Observabilidad | Periodos disponibles | Comparabilidad | Ajuste requerido |
|---|---|---|---|---|
| `publication_year` | Directa desde ZIP | 1998-2023 | Directa | Ninguno. |
| `fiscal_year` | Directa desde titulo del cuadro | 1997-2022 para Ganancias Sociedades | Directa | Extraer desde titulo; no inferir solo desde nombre ZIP. |
| `actividad_label` | Directa | Todos los fiscal years inspeccionados | Parcial | Normalizar texto y separar seccion/subactividad. |
| `actividad_section` | Directa o derivable desde label | Todos | Comparable solo dentro de clasificador | Construir correspondencia entre clasificador viejo y nuevo. |
| `actividad_3digitos` | Directa cuando existe | 1998-2022 observados; no continua en fiscal 1997 | No continua para toda la serie | Usar maximo disponible y agregar a seccion para vistas homologadas. |
| `presentaciones_total` | Directa | Todos | Alta | Validar duplicados de anios embebidos en ZIPs 2001-2002. |
| `presentaciones_con_ventas` | Directa | Todos | Alta | Normalizar encabezados. |
| `presentaciones_con_ganancia_o_impuesto` | Directa, pero cambia concepto | Todos, con quiebre conceptual | Baja como serie unica | Separar en `presentaciones_con_ganancia_neta_imponible` y `presentaciones_con_impuesto_determinado`. |
| `ventas_netasy_locaciones` | Directa | Todos | Alta a nivel total; parcial por sector | Normalizar miles/millones; armonizar clasificador para sectores. |
| `ganancia_neta_imponible` | Directa | Todos | Media-alta | Normalizar unidad; documentar cambios legales antes de interpretar tasas o rentabilidad. |
| `impuesto_determinado` | Directa | Todos | Media | Normalizar unidad; no interpretar como rentabilidad sin considerar cambios normativos. |
| `costos_total` | Directa o reconstruible desde estado de resultados | Todos | Media | En periodos viejos aparece mas agregado; en nuevos hay mayor desagregacion. |
| `resultado_bruto_utilidad` | Directa | Todos | Media | Mantener signo/origen; los cuadros separan utilidad y perdida. |
| `resultado_bruto_perdida` | Directa | Todos | Media | Mantener separado o derivar neto con regla explicita. |
| `resultado_bruto_neto` | Derivada | Todos si se reconstruye | Media | Calcular utilidad menos perdida; documentar regla. |
| `resultado_contable_utilidad` | Directa | Todos, con nombres antiguos como resultado final del ejercicio | Media | Armonizar nombres: resultado final/resultado contable. |
| `resultado_contable_perdida` | Directa | Todos, con nombres antiguos como resultado final del ejercicio | Media | Armonizar nombres y signo. |
| `resultado_contable_neto` | Derivada | Todos si se reconstruye | Media | Calcular utilidad menos perdida; validar contra cuadros de resultado. |
| `resultado_impositivo_utilidad` | Directa | Todos | Media | Normalizar nombres y signo. |
| `resultado_impositivo_perdida` | Directa | Todos | Media | Normalizar nombres y signo. |
| `resultado_impositivo_neto` | Derivada | Todos si se reconstruye | Media | Calcular utilidad menos perdida; documentar tratamiento de quebrantos. |
| `activo_total` | Directa | Todos | Alta a nivel total; parcial por sector | Normalizar unidad; armonizar clasificador. |
| `pasivo_total` | Directa | Todos | Alta a nivel total; parcial por sector | Normalizar unidad; armonizar clasificador. |
| `patrimonio_neto_inicio` | Directa o separada en positivo/negativo | Conceptual en todos; en P0 fiscal 2014-2016 no hay total directo | Media | No netear positivo/negativo sin regla documentada. |
| `patrimonio_neto_cierre` | Directa o separada en positivo/negativo | Conceptual en todos; en P0 fiscal 2014-2016 no hay total directo | Media | No netear positivo/negativo sin regla documentada. |
| `componentes_activo` | Directa solo desde mayor desagregacion | Principalmente fiscal 2002-2022 | Parcial | No forzar hacia atras sin agregacion. |
| `componentes_pasivo` | Directa solo desde mayor desagregacion | Principalmente fiscal 2002-2022 | Parcial | No forzar hacia atras sin agregacion. |
| `componentes_patrimonio` | Directa solo desde mayor desagregacion | Principalmente fiscal 2002-2022 | Parcial | No forzar hacia atras sin agregacion. |
| `mes_cierre` | Directa | Principalmente fiscal 2002-2022 | Parcial | No usar como identificador comun de toda la serie. |
| `tramo_ventas` | Directa | Observada en periodos antiguos y modernos | Parcial | Validar rangos; pueden cambiar cortes y moneda nominal. |
| `tramo_ganancia_neta_imponible` | Directa | Observada en periodos antiguos y modernos | Parcial | Validar rangos; no comparar cortes nominales sin ajuste. |
| `margen_ganancia_imponible_sobre_ventas` | Derivada | Todos si hay ventas positivas | Media | `ganancia_neta_imponible / ventas`; sector requiere armonizacion. |
| `tasa_impuesto_sobre_ganancia` | Derivada | Todos si hay ganancia positiva | Baja-media | `impuesto_determinado / ganancia_neta_imponible`; interpretar con cambios legales. |
| `roa_contable` | Derivada | Todos si se reconstruye resultado contable neto | Media | `resultado_contable_neto / activo_total`; requiere regla de resultado neto. |
| `roe_contable` | Derivada | Todos si se reconstruye resultado contable neto | Media | `resultado_contable_neto / patrimonio_neto`; revisar patrimonio negativo/cero. |

## Variables Disponibles En Toda La Serie De Sociedades

Con cobertura conceptual completa, aunque no siempre con igual formato:

- `fiscal_year`
- `actividad_label`
- `presentaciones_total`
- `presentaciones_con_ventas`
- `ventas_netasy_locaciones`
- `ganancia_neta_imponible`
- `impuesto_determinado`
- `costos_total`
- `resultado_bruto`
- `resultado_contable` o `resultado_final_del_ejercicio`
- `resultado_impositivo`
- `activo_total`
- `pasivo_total`
- `patrimonio_neto_inicio` o sus componentes positivo/negativo segun periodo.
- `patrimonio_neto_cierre` o sus componentes positivo/negativo segun periodo.

## Variables Solo Parciales

- `actividad_3digitos`: cubre desde fiscal 1998 en los archivos observados, pero no fiscal 1997.
- `mes_cierre`: aparece desde la etapa moderna del bloque `2.3.*`.
- Componentes finos de activo, pasivo, patrimonio, gastos operativos, resultados financieros y extraordinarios: mas consistentes desde fiscal 2002.
- Tramos nominales de ventas o ganancia: existen en varias epocas, pero requieren validar cortes.

## Comparabilidad Por Periodo Y Variable

| Familia de variables | P0 fiscal 2014-2022 | P1 fiscal 2013 | P2 fiscal 2012 | P3 fiscal 2008-2011 | P4 fiscal 2002-2007 | P5 fiscal 1999-2001 | P6 fiscal 1997-1998 | Discontinuidad principal |
|---|---|---|---|---|---|---|---|---|
| Actividad a seccion | Si | Si | Si | Si | Si | Si | Si | Clasificador viejo/nuevo. |
| Actividad a 3 digitos | Si | Si | Si | Si, en `sheet002.htm` | Si, en `_2` | Si, en `_2` | Parcial: fiscal 1998 si, fiscal 1997 no | Maximo detalle no cubre toda la serie. |
| Presentaciones totales | Si | Si | Si | Si | Si | Si | Si | Duplicados de fiscal years en 2001-2002. |
| Presentaciones con ventas | Si | Si | Si | Si | Si | Si | Si | Encabezados con variantes menores. |
| Presentaciones con impuesto determinado | Si | Si | Si | Si | Si | Parcial | No | Antes aparece `con ganancia neta imponible`. |
| Ventas netas y locaciones | Si | Si | Si | Si | Si | Si | Si | Miles a millones entre fiscal 2011 y 2012. |
| Ganancia neta imponible | Si | Si | Si | Si | Si | Si | Si | Cambios legales no resueltos. |
| Impuesto determinado | Si | Si | Si | Si | Si | Si | Si | Cambios legales no resueltos. |
| Costos y resultado bruto | Si | Si | Si | Si | Si | Si | Si | Componentes no siempre comparables. |
| Resultado contable/final | Si | Si | Si | Si | Si | Si | Si | Nombre cambia: resultado final vs contable. |
| Resultado impositivo | Si | Si | Si | Si | Si | Si | Si | Separar utilidad/perdida/quebranto. |
| Activo total | Si | Si | Si | Si | Si | Si | Si | Unidad y clasificador. |
| Pasivo total | Si | Si | Si | Si | Si | Si | Si | Unidad y clasificador. |
| Patrimonio neto inicio/cierre | Parcial: 2014-2016 separado en positivo/negativo; 2017-2022 total directo | Si | Si | Si | Si | Si | Si | No netear positivo/negativo sin regla explicita. |
| Componentes de activo/pasivo/patrimonio | Si | Si | Si | Si | Si | Parcial | No/Parcial | No forzar hacia atras. |
| Mes de cierre | Si | Si | Si | Si | Si | No | No | Dimension parcial. |
| Tramos de ventas | Si | Si | Si | Si | Si | Si | Si | Cortes nominales requieren validacion. |
| Tramos de ganancia neta imponible | Si | Si | Si | Si | Si | Si | Si | Cortes nominales requieren validacion. |

Notas P4:

- P4 conserva actividad a 3 digitos en `_2.xls`, con clasificador viejo y unidad `miles_pesos_corrientes`.
- El componente de costos `OTROS` se preserva como `costos_otros`; no debe tratarse automaticamente como equivalente perfecto de `gastos_vinculados_al_costo`.
- Las variables de resultado estan disponibles, pero en P4 aparecen en una numeracion mas condensada que P0-P2. El pipeline mapea esa numeracion a nombres canonicos, conservando `source_table_id` y `source_note`.
- En fiscal 2007, actividad `142`, cuadro `2.3.1.1.2.1`, hay valores fuente en blanco para las variables de costos/ventas excepto `presentaciones_total`; esos faltantes no fueron imputados.

## Punto De Partida Recomendado

Para programar el pipeline, comenzar con los ZIP 2021-2023:

- Son XLS directos.
- Tienen estructura de carpetas mas regular.
- Cubren fiscal years 2020-2022.
- Usan clasificador nuevo y detalle 3 digitos.

Estado actual: ese parser base ya fue extendido a publication years 2015-2023 / fiscal years 2014-2022, manteniendo el mismo esquema largo. El bloque HTML con clasificador nuevo (`P1_new_html_detail`, fiscal year 2013), el bloque HTML con clasificador viejo en millones (`P2_old_html_detail_millions`, fiscal year 2012), el bloque HTML con clasificador viejo en miles (`P3_old_html_detail_thousands`, fiscal years 2008-2011), el bloque CAB/XLS con clasificador viejo en miles (`P4_old_cab_xls_detail_thousands`, fiscal years 2002-2007), el bloque CAB/XLS con numeracion antigua `3.3.*` (`P5_old_cab_xls_detail_legacy_numbering`, fiscal years 1999-2001) y el bloque XLS directo antiguo (`P6_legacy_broad_activity`, fiscal years 1997-1998) tambien fueron incorporados y validados.

Para el primer panel analitico ampliado, extender luego a 2015-2023:

- Mantiene XLS directo.
- Mantiene clasificador nuevo.
- Cubre fiscal years 2014-2022.
- La extension 2015-2020 ya fue completada; las advertencias completas estan en `documentation/afip/warnings_by_period.md`.
- Fiscal years 2014-2022 ya estan incorporados al P0 principal y validados en el ensamble.
- Fiscal years 2014-2018 conservan discontinuidades internas documentadas, especialmente ventas detalladas tempranas, quebranto computable, subcuadros patrimoniales ausentes y patrimonio positivo/negativo en 2014-2016.
- La homologacion amplia de ramas economicas ya fue implementada en `data/analysis-data/2026-05-31_afip_ganancias_sociedades_tidy_homologado.csv.gz`. Conserva codigos originales en el panel y etiquetas originales en el diccionario de actividad; agrega rama comun amplia y no equipara directamente codigos de 3 digitos entre clasificadores.

La extraccion hacia atras del capitulo Ganancias Sociedades esta cubierta para fiscal years 1997-2022. La siguiente tarea es construir la base de analisis y luego homologar ramas economicas.

Estado actualizado: la base de analisis y la primera homologacion amplia de
ramas ya estan construidas y validadas. La tarea pendiente es solo la
homologacion fina de actividades de 3 digitos entre clasificadores, si el
analisis necesita mas desagregacion que la rama comun amplia.

## Plan De Construccion Hacia Atras

1. `P0_new_xls_detail`, fiscal 2014-2022: parser XLS base implementado, ensamblado y validado.
2. `P1_new_html_detail`, fiscal 2013: parser HTML con clasificador nuevo implementado y validado.
3. `P2_old_html_detail_millions`, fiscal 2012: parser HTML con clasificador viejo en millones implementado y validado.
4. `P3_old_html_detail_thousands`, fiscal 2008-2011: parser HTML con clasificador viejo en miles implementado y validado.
5. `P4_old_cab_xls_detail_thousands`, fiscal 2002-2007: parser CAB/XLS con codigos `2.3.*` implementado y validado.
6. `P5_old_cab_xls_detail_legacy_numbering`, fiscal 1999-2001: parser CAB/XLS con codigos `3.3.*` implementado y validado; duplicados resueltos con publication year 2002 como fuente canonica.
7. `P6_legacy_broad_activity`, fiscal 1997-1998: parser XLS directo antiguo implementado y validado; fiscal 1997 amplio, fiscal 1998 con detalle 3 digitos en `_2`.
