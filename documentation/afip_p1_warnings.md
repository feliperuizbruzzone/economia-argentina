# AFIP P1 Warnings And Structural Notes

Alcance: `P1_new_html_detail`, publication year 2014, fiscal year 2013.

Estado de validacion:

- Inventario P1: 13 cuadros de actividad.
- Extraccion larga P1: 37.088 filas.
- Validacion P1: 0 fallas y 0 advertencias.
- Reporte: `data/output-data/validation_reports/ganancias_sociedades_p1_long_validation.md`.
- Detalle de conteos: `data/output-data/validation_reports/ganancias_sociedades_p1_long_counts.csv`.

## Advertencias Vigentes

No hay advertencias vigentes emitidas por la validacion P1.

## Notas Estructurales

- El ZIP 2014 esta en formato HTML exportado desde Excel, no en XLS directo.
- Para cada cuadro disponible se prefirio la hoja/archivo secundario con sufijo `_2`, porque contiene el maximo detalle de actividad observado.
- La extraccion corta antes de las secciones de `Estructura porcentual`; esas filas no forman parte de la base larga de valores absolutos.
- P1 conserva el clasificador nuevo y montos en millones de pesos corrientes, por lo que es el puente inmediato hacia atras del P0.
- P1 contiene 13 cuadros `2.3.1.1.*` de actividad. No se observaron en este ZIP los subcuadros detallados modernos `2.3.1.1.5.1.1`, `2.3.1.1.5.1.2`, `2.3.1.1.5.1.3`, `2.3.1.1.5.1.4`, `2.3.1.1.5.2.1`, `2.3.1.1.5.3.1` y `2.3.1.1.5.3.2`.
- No se implemento homologacion de ramas economicas; se preservan `activity_code`, `activity_label_original` y `activity_section_original`.

## Criterio Metodologico

P1 debe analizarse como clasificador nuevo y formato HTML. Es comparable con P0 para los cuadros y variables observados en ambos periodos, luego de respetar la diferencia de cobertura de cuadros y de mantener la unidad monetaria canonica en `value_pesos_current`.
