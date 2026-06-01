# AFIP P3 Warnings And Structural Notes

Alcance: `P3_old_html_detail_thousands`, publication years 2009-2012, fiscal years 2008-2011.

Estado de validacion:

- Inventario P3: 49 pares publication year x cuadro.
- Extraccion larga P3: 97.775 filas.
- Validacion P3: 0 fallas y 10 advertencias.
- Reporte: `data/output-data/validation_reports/ganancias_sociedades_p3_long_validation.md`.
- Detalle de conteos: `data/output-data/validation_reports/ganancias_sociedades_p3_long_counts.csv`.

## Advertencias Vigentes

- Fiscal year 2008, cuadro `2.3.1.1.2.1`: el componente residual de costos aparece como `OTROS`; se conserva como `costos_otros`, no como `gastos_vinculados_al_costo`.
- Fiscal year 2008, cuadros `2.3.1.1.2.2`, `2.3.1.1.2.3` y `2.3.1.1.2.4`: el `source_table_id` conserva la numeracion original, pero el contenido corresponde a familias que en anios posteriores aparecen desplazadas.
- Fiscal year 2008 no trae los cuadros `2.3.1.1.2.5`, `2.3.1.1.2.6` y `2.3.1.1.2.7`.
- Fiscal year 2008, cuadros `2.3.1.1.3` y `2.3.1.1.4`: solo se encontro `sheet001.htm`; no hay detalle de actividad a 3 digitos.
- Fiscal year 2010, cuadro `2.3.1.1.2.3`: solo se encontro `sheet001.htm`; no hay detalle de actividad a 3 digitos.

## Notas Estructurales

- Los ZIP 2009-2012 estan en formato HTML exportado desde Excel.
- Las rutas internas varian entre archivos: se busca el cuadro por sufijo, no por una carpeta raiz fija.
- Para cada cuadro se prefiere `sheet002.htm` cuando existe.
- El parser HTML usa `from_encoding="windows-1252"` y bytes originales para evitar mojibake en acentos y encabezados.
- La extraccion corrige automaticamente desalineaciones de una columna entre encabezado de actividad y comienzo efectivo de datos.
- Los montos se leen en `miles_pesos_corrientes`; `value_pesos_current` multiplica por 1.000.
- No se implemento homologacion de ramas economicas; se preservan `activity_code`, `activity_label_original` y `activity_section_original`.

## Criterio Metodologico

P3 debe analizarse como clasificador viejo y unidad original en miles de pesos corrientes. Es comparable con P2 en clasificador, pero requiere normalizacion de escala monetaria. Las diferencias de fiscal year 2008 deben tratarse como discontinuidades internas del periodo y no como faltantes imputables.
