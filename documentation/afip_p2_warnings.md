# AFIP P2 Warnings And Structural Notes

Alcance: `P2_old_html_detail_millions`, publication year 2013, fiscal year 2012.

Estado de validacion:

- Inventario P2: 13 cuadros de actividad.
- Extraccion larga P2: 27.208 filas.
- Validacion P2: 0 fallas y 0 advertencias.
- Reporte: `data/output-data/validation_reports/ganancias_sociedades_p2_long_validation.md`.
- Detalle de conteos: `data/output-data/validation_reports/ganancias_sociedades_p2_long_counts.csv`.

## Advertencias Vigentes

No hay advertencias vigentes emitidas por la validacion P2.

## Notas Estructurales

- El ZIP 2013 esta en formato HTML exportado desde Excel.
- El detalle maximo de actividad esta en `Archivos/<table_id>_archivos/sheet002.htm`.
- P2 es el primer tramo incorporado con `classifier_period = old`.
- Los montos siguen en millones de pesos corrientes, por lo que la unidad monetaria es comparable con P0 y P1 luego de usar `value_pesos_current`.
- La extraccion corta antes de secciones de `Estructura porcentual`; esas filas no forman parte de la base larga de valores absolutos.
- El parser HTML recorta columnas vacias finales generadas por estilos o `colspan` de Excel para evitar detectar variables estadisticas falsas.
- No se implemento homologacion de ramas economicas; se preservan `activity_code`, `activity_label_original` y `activity_section_original`.

## Criterio Metodologico

P2 debe analizarse como clasificador viejo y formato HTML en millones. Es
comparable con P3 por clasificador, pero no por unidad monetaria original:
P3 pasa a miles de pesos corrientes. Es comparable con P0-P1 en montos
normalizados, pero no en actividad economica sin una tabla posterior de
homologacion sectorial.
