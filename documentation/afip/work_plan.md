# AFIP Work Plan

Este documento sistematiza el plan de trabajo posterior al inventario estructural preliminar.
No contiene codigo de extraccion ni define decisiones metodologicas finales.

## Estado De Partida

- Fuente: AFIP/ARCA, anuario de estadisticas tributarias.
- Periodo objetivo: 1998-2023.
- Capitulo objetivo actual: `Impuesto a las Ganancias Sociedades`.
- Cobertura fiscal observada del capitulo: fiscal years 1997-2022.
- Salida canonica definida: base de datos en formato largo.
- Criterio de desagregacion: conservar el maximo nivel disponible por periodo.
- Datos crudos locales: `data/input-data/raw/afip-estadisticas-tributarias/`.
- Archivos crudos: 26 ZIP anuales.
- Validacion basica: los ZIP fueron probados con `unzip -tq` sin errores detectados.
- Mapeo estructural: `documentation/afip/structural_mapping.yml`.
- Inventario preliminar: `documentation/afip/archive_inventory.md`.
- Comparabilidad del capitulo: `documentation/afip/variable_comparability.md`.
- Diseno ETL modular: `documentation/afip/etl_design.md`.
- Advertencias y notas estructurales P0-P6: `documentation/afip/warnings_by_period.md`.
- Homologacion de ramas: `documentation/afip/branch_harmonization.md`.

## Epocas Operativas

| Epoca | Anios | Formato operativo | Implicacion para pipeline |
|---|---:|---|---|
| `legacy_direct_xls_install_layout` | 1998, 1999, 2001 | XLS directo con artefactos de instalador | Leer XLS directos e ignorar instaladores salvo validacion posterior. |
| `cab_embedded_xls` | 2000, 2002-2008 | XLS dentro de `AFIP.CAB` | Agregar paso previo de inventario/extraccion CAB. |
| `excel_html_export` | 2009-2014 | HTML exportado desde Excel | Usar parser especifico para HTML, no lector XLS. |
| `modern_direct_xls_transition` | 2015-2020 | XLS directo con rutas variables | Reusar parser XLS con normalizacion de rutas por anio. |
| `modern_direct_xls_current` | 2021-2023 | XLS directo moderno | Usar como punto de partida del parser canonico. |

## Secuencia Recomendada

1. Formalizar inventario canonico del capitulo Ganancias Sociedades como CSV en `data/intermediate-data/`.
2. Implementar funciones auxiliares pequenas y probadas: primero deteccion de encabezado y comienzo de datos.
3. Implementar parser base en formato largo para publication years 2021-2023, fiscal years 2020-2022.
4. Extender el parser XLS a publication years 2015-2020, fiscal years 2014-2019. Estado actual: completado dentro de P0; las advertencias por cuadro estan documentadas.
5. Incorporar publication year 2014, fiscal year 2013, HTML con clasificador nuevo. Estado: completado.
6. Incorporar publication year 2013, fiscal year 2012, HTML viejo en millones. Estado: completado.
7. Incorporar publication years 2009-2012, fiscal years 2008-2011, HTML viejo en miles y hojas secundarias. Estado: completado.
8. Incorporar publication years 2003-2008, fiscal years 2002-2007, CAB/XLS con codigos `2.3.*`. Estado: completado.
9. Incorporar publication years 2000-2002, fiscal years 1999-2001, codigos `3.3.*` y duplicados. Estado: completado.
10. Incorporar publication years 1998-1999, fiscal years 1997-1998, actividad amplia/detalle mixto. Estado: completado.
11. Construir CSV largo final para analisis. Estado: completado con version fechada sin homologar.
12. Agregar homologacion de ramas economicas amplia preservando detalle fuente. Estado: completado con version fechada homologada.

## Decisiones Que Deben Cerrarse Antes De Extraer

- Inventario canonico de todos los cuadros/tablas del capitulo Ganancias Sociedades.
- Regla para resolver duplicados de fiscal years embebidos en ZIPs 2001-2002.
- Variables derivadas definitivas.
- Identificadores unicos por fila.
- Reglas de comparabilidad entre epocas.
- Tratamiento de cambios de clasificador, redefiniciones y faltantes.
- Homologacion fina de actividades de 3 digitos entre clasificador viejo y nuevo. La homologacion amplia ya fue implementada y conserva etiquetas y codigos originales.

## Regla De Trabajo

No implementar extraccion sustantiva antes de decidir el universo de cuadros y variables.
El universo de cuadros es Ganancias Sociedades, pero antes de extraer valores debe existir un inventario canonico de tablas, continuaciones y hojas secundarias.
El primer parser comenzo por 2021-2023 y ya se extendio a publication years 2015-2023 / fiscal years 2014-2022. La extension posterior debe seguir hacia atras por periodos de homogeneidad interna.
Cada funcion nueva debe tener docstring y una prueba/probe contra al menos un archivo concreto antes de ampliar cobertura.

## Estado De Fase 3 Retrospectiva P0

Fase completada para publication years 2015-2023 / fiscal years 2014-2022.

Comandos incorporados al flujo reproducible:

```bash
python3 command-files/processing-command-files/46_build_ganancias_sociedades_p0_backward_inventory.py
python3 command-files/processing-command-files/47_validate_ganancias_sociedades_p0_backward_inventory.py
python3 command-files/processing-command-files/48_probe_ganancias_sociedades_p0_backward_detectors.py
```

Resultados actuales:

- Inventario P0 de actividad: 892 filas, 0 fallas, 8 advertencias estructurales.
- Inventario retrospectivo auxiliar: 112 filas, 0 fallas, 17 advertencias.
- Prueba de detectores retrospectiva: 112 filas, 0 advertencias luego de adaptar detectores.
- P0 principal: 20 tablas extraidas, 491.435 filas largas ensambladas para fiscal years 2014-2022.
- Validacion consolidada P0: 0 fallas y 0 advertencias.
- Todas las advertencias por cuadro estan documentadas en `documentation/afip/warnings_by_period.md`.

Estado posterior: el CSV completo de analisis desde P0+P1+P2+P3+P4+P5+P6 validados ya fue generado, primero sin homologar y luego con una homologacion amplia de ramas.

## Estado De Fase 4 P1

Fase completada para publication year 2014 / fiscal year 2013.

Comandos incorporados al flujo reproducible:

```bash
python3 command-files/processing-command-files/49_build_ganancias_sociedades_p1_inventory.py
python3 command-files/processing-command-files/50_extract_ganancias_sociedades_p1_long.py
python3 command-files/processing-command-files/51_validate_ganancias_sociedades_p1_long.py
```

Resultados actuales:

- Inventario P1: 13 cuadros de actividad, todos con detalle de actividad observado en archivos/hojas secundarias `_2`.
- Extraccion P1: 37.088 filas largas.
- Variables canonicas observadas: 127.
- Validacion P1: 0 fallas y 0 advertencias.
- Reporte: `data/output-data/validation_reports/ganancias_sociedades_p1_long_validation.md`.
- Notas estructurales: `documentation/afip/warnings_by_period.md`.

Estado posterior: P2 ya fue incorporado; el siguiente paso operativo vigente es P3.

## Estado De Fase 5 P2

Fase P2 completada para publication year 2013 / fiscal year 2012.

Comandos incorporados al flujo reproducible:

```bash
python3 command-files/processing-command-files/52_build_ganancias_sociedades_p2_inventory.py
python3 command-files/processing-command-files/53_extract_ganancias_sociedades_p2_long.py
python3 command-files/processing-command-files/54_validate_ganancias_sociedades_p2_long.py
```

Resultados actuales:

- Inventario P2: 13 cuadros de actividad, todos con detalle observado en `sheet002.htm`.
- Extraccion P2: 27.208 filas largas.
- Variables canonicas observadas: 127.
- Validacion P2: 0 fallas y 0 advertencias.
- Reporte: `data/output-data/validation_reports/ganancias_sociedades_p2_long_validation.md`.
- Notas estructurales: `documentation/afip/warnings_by_period.md`.
- `classifier_period = old`; unidad monetaria original en millones de pesos corrientes.

Estado posterior: P3, P4, P5 y P6 ya fueron incorporados; el siguiente paso operativo vigente es generar la base cruda de analisis.

## Estado De Fase 5 P3

Fase P3 completada para publication years 2009-2012 / fiscal years 2008-2011.

Comandos incorporados al flujo reproducible:

```bash
python3 command-files/processing-command-files/55_build_ganancias_sociedades_p3_inventory.py
python3 command-files/processing-command-files/56_extract_ganancias_sociedades_p3_long.py
python3 command-files/processing-command-files/57_validate_ganancias_sociedades_p3_long.py
```

Resultados actuales:

- Inventario P3: 49 pares anio-cuadro.
- Extraccion P3: 97.775 filas largas.
- Variables canonicas observadas: 129.
- Validacion P3: 0 fallas y 10 advertencias estructurales.
- Reporte: `data/output-data/validation_reports/ganancias_sociedades_p3_long_validation.md`.
- Advertencias: `documentation/afip/warnings_by_period.md`.
- `classifier_period = old`; unidad monetaria original en miles de pesos corrientes.

Estado posterior: P4, P5 y P6 ya fueron incorporados; el siguiente paso operativo vigente es generar la base cruda de analisis.

## Estado De Fase 6 P4

Fase P4 completada para publication years 2003-2008 / fiscal years 2002-2007.

Comandos incorporados al flujo reproducible:

```bash
python3 command-files/processing-command-files/58_build_ganancias_sociedades_p4_inventory.py
python3 command-files/processing-command-files/59_extract_ganancias_sociedades_p4_long.py
python3 command-files/processing-command-files/60_validate_ganancias_sociedades_p4_long.py
```

Resultados actuales:

- Inventario P4: 60 pares anio-cuadro, todos XLS dentro de `AFIP.CAB`.
- Extraccion P4: 132.088 filas largas.
- Variables canonicas observadas: 111.
- Validacion P4: 0 fallas y 25 advertencias documentadas.
- Reporte: `data/output-data/validation_reports/ganancias_sociedades_p4_long_validation.md`.
- Advertencias: `documentation/afip/warnings_by_period.md`.
- `classifier_period = old`; unidad monetaria original en miles de pesos corrientes.
- Se usa `_2.xls` como regla de maximo detalle de actividad.

Estado posterior: P5 y P6 ya fueron incorporados; el siguiente paso operativo vigente es generar la base cruda de analisis.

## Estado De Fase 7 P5

Fase P5 completada para publication year 2002 / fiscal years 1999-2001.

Comandos incorporados al flujo reproducible:

```bash
python3 command-files/processing-command-files/61_build_ganancias_sociedades_p5_inventory.py
python3 command-files/processing-command-files/62_extract_ganancias_sociedades_p5_long.py
python3 command-files/processing-command-files/63_validate_ganancias_sociedades_p5_long.py
```

Resultados actuales:

- Inventario P5: 18 pares anio-cuadro, todos XLS dentro de `AFIP.CAB`.
- Extraccion P5: 31.229 filas largas.
- Variables canonicas observadas: 114.
- Validacion P5: 0 fallas y 35 advertencias documentadas.
- Reporte: `data/output-data/validation_reports/ganancias_sociedades_p5_long_validation.md`.
- Advertencias: `documentation/afip/warnings_by_period.md`.
- `classifier_period = old`; unidad monetaria original en miles de pesos corrientes.
- Se usa publication year 2002 como fuente canonica para fiscal years 1999-2001 y se descartan publicaciones anteriores duplicadas.
- Fiscal years 1999-2000 tienen esquema compacto de cuatro cuadros; fiscal year 2001 tiene numeracion antigua expandida.

Estado posterior: P6 ya fue incorporado; el siguiente paso operativo vigente es generar la base cruda de analisis.

## Estado De Fase 8 P6

Fase P6 completada para publication years 1998-1999 / fiscal years 1997-1998.

Comandos incorporados al flujo reproducible:

```bash
python3 command-files/processing-command-files/64_build_ganancias_sociedades_p6_inventory.py
python3 command-files/processing-command-files/65_extract_ganancias_sociedades_p6_long.py
python3 command-files/processing-command-files/66_validate_ganancias_sociedades_p6_long.py
```

Resultados actuales:

- Inventario P6: 8 pares anio-cuadro, todos XLS directos.
- Extraccion P6: 3.044 filas largas.
- Variables canonicas observadas: 36.
- Validacion P6: 0 fallas y 24 advertencias documentadas.
- Reporte: `data/output-data/validation_reports/ganancias_sociedades_p6_long_validation.md`.
- Advertencias: `documentation/afip/warnings_by_period.md`.
- `classifier_period = old`; unidad monetaria original en miles de pesos corrientes.
- Fiscal year 1997 usa numeracion `4.4.*` y solo actividad amplia.
- Fiscal year 1998 usa numeracion `3.3.*` y tiene detalle 3 digitos en archivos `_2.xls`.

Estado posterior: se genero el panel tidy homologado en `data/analysis-data/`
y se validaron los diccionarios de trazabilidad y la homologacion de ramas.

## Estado De Fase 9 Salidas De Analisis Y Homologacion

Fase completada para fiscal years 1997-2022.

Comandos incorporados al flujo reproducible:

```bash
python3 command-files/processing-command-files/67_build_ganancias_sociedades_tidy_homologado.py
python3 command-files/processing-command-files/68_validate_ganancias_sociedades_tidy_outputs.py
```

Resultados actuales:

- Panel tidy homologado: `data/analysis-data/2026-07-10_afip_ganancias_sociedades_tidy_homologado.csv`.
- El panel tiene 819.867 filas, cobertura fiscal 1997-2022 y pesa 36.749.414 bytes sin comprimir.
- Diccionario de fuente: `data/intermediate-data/afip-estadisticas-tributarias/2026-07-10_afip_ganancias_sociedades_source_dictionary.csv`.
- Diccionario de actividad: `data/intermediate-data/afip-estadisticas-tributarias/2026-07-10_afip_ganancias_sociedades_activity_dictionary.csv`.
- Diccionario de variable: `data/intermediate-data/afip-estadisticas-tributarias/2026-07-10_afip_ganancias_sociedades_variable_dictionary.csv`.
- Diccionario de homologacion: `data/intermediate-data/afip-estadisticas-tributarias/2026-07-10_afip_ganancias_sociedades_ramas_homologacion_diccionario.csv`.
- Validacion final: 0 fallas y 0 advertencias.
- La homologacion agrega `rama_comun_codigo` para comparabilidad amplia y `rama_detalle_homologada_codigo` para conservar detalle fuente por clasificador; etiquetas, rutas largas y nombres de variables viven en diccionarios.

Siguiente paso metodologico: decidir si se construira una correspondencia fina de actividades a 3 digitos entre clasificador viejo y nuevo o si el analisis se hara sobre ramas comunes amplias.
