# Contexto Del Proyecto

Este archivo es la fuente de verdad operativa para trabajar desde cero en este directorio.
Antes de cambiar codigo, datos o estructura, revisar estas reglas, el estado actual y las decisiones pendientes.

## 1. Alcance General Del Proyecto

Este directorio no queda limitado a una unica fuente o tarea. La sistematizacion
de AFIP/ARCA es una de las lineas de trabajo del proyecto `economia-argentina`;
en este mismo marco podran agregarse luego otras fuentes, series o modulos de
analisis. Cada linea debe conservar su propia documentacion, scripts,
validaciones y decisiones metodologicas para evitar mezclar supuestos entre
fuentes.

Regla operativa: cuando una tarea sea especifica de AFIP, usar prefijos,
archivos y documentacion `afip_*`. Nuevas fuentes o modulos deben crear sus
propios artefactos equivalentes, sin reutilizar nombres de salida que puedan
confundir origen, unidad de observacion o metodologia.

## 2. Objetivo AFIP/ARCA

Construir un flujo reproducible bajo Project TIER 4.0 para sistematizar series estadisticas economicas de empresas en Argentina.

El objetivo analitico es construir variables economicas a nivel de rama o subrama economica, cuando la estructura de los datos lo permita, para analizar rentabilidad y desempeno economico en perspectiva historica.
El producto buscado es una serie consistente para el periodo 1998-2023.

Decision actual del investigador:

- Capitulo objetivo: `Impuesto a las Ganancias Sociedades`.
- Cobertura sustantiva: toda la serie disponible para ese capitulo.
- Cobertura fiscal observada para Ganancias Sociedades: fiscal years 1997-2022.
- Estrategia de desagregacion: conservar el maximo nivel disponible por periodo.
- Formato de la base canonica: largo.
- Direccion de construccion: comenzar en el ultimo fiscal year disponible y avanzar hacia atras por periodos homogeneos.

La base final no debe reducir de entrada a una unica unidad sectorial comun. Debe preservar la desagregacion original disponible y agregar campos que permitan homologar despues: `classifier_period`, `activity_level`, `activity_code`, `activity_label_original`, `activity_section_original`, `dimension_type`, `source_table_id`, `variable_name`, `value`, `unit_original` y `value_pesos_current`.

## 3. Fuente De Datos AFIP/ARCA

La fuente de datos es AFIP, de aqui en adelante el nombre operativo del proyecto para la institucion publicadora.
La pagina oficial consultada actualmente aparece bajo el sitio de ARCA, pero conserva el contenido del anuario de estadisticas tributarias y enlaces por anio en dominio AFIP.

Fuente inicial:

```text
https://www.afip.gob.ar/institucional/estudios/anuario-estadisticas-tributarias/
```

Cobertura objetivo:

```text
1998-2023
```

Caracteristicas conocidas de la fuente:

- Archivos anuales publicados como comprimidos de distinto tipo.
- Contenido economico en archivos XLS.
- Datos construidos a partir de reportes contables de empresas.
- Estructura heterogenea entre anios, ramas, subramas, hojas, encabezados o formatos.
- La serie local descargada contiene 26 ZIP anuales, uno por anio entre 1998 y 2023.
- Los ZIP crudos estan en `data/input-data/raw/afip-estadisticas-tributarias/`.
- Los ZIP se validaron con `unzip -tq` sin errores detectados.

Inventario estructural preliminar:

- `documentation/afip/archive_inventory.md`
- `documentation/afip/structural_mapping.yml`

Epocas estructurales propuestas:

- 1998, 1999, 2001: XLS directo con artefactos de instalador.
- 2000, 2002-2008: XLS dentro de `AFIP.CAB`.
- 2009-2014: HTML exportado desde Excel.
- 2015-2020: retorno a XLS directo con transiciones de nombres/carpetas.
- 2021-2023: XLS directo moderno.

El pipeline debe respetar estas epocas. No asumir una unica estructura de archivo ni un unico parser para todo el periodo.

## 4. Organizacion TIER

El repositorio separa comandos, datos, documentacion y resultados:

- `command-files/`: todo codigo ejecutable del proyecto.
- `command-files/config/project_config.py`: rutas y constantes centrales del proyecto.
- `data/input-data/`: datos originales, tratados como solo lectura despues de su descarga o incorporacion.
- `data/intermediate-data/`: salidas transitorias que pueden regenerarse.
- `data/intermediate-data/afip-estadisticas-tributarias/`: salidas intermedias regenerables de la fuente AFIP/ARCA. Mantener esta separacion porque el proyecto tambien incorporara otras fuentes.
- `data/analysis-data/`: datos finales para analisis.
- `data/output-data/`: resultados derivados.
- `documentation/`: documentacion metodologica y operativa.
- `tests/`: pruebas y validaciones.

Criterio vigente para `documentation/`: los documentos especificos de una
fuente deben vivir en `documentation/<fuente>/`. Dentro de esa subcarpeta se
elimina el prefijo redundante del nombre de archivo; por ejemplo, los antiguos
`afip_*.md` fueron movidos a `documentation/afip/` como `work_plan.md`,
`etl_design.md`, `variable_comparability.md`, etc. Las advertencias de periodos
homogeneos de una misma fuente deben consolidarse en un unico archivo por
fuente, actualmente `documentation/afip/warnings_by_period.md`, salvo que haya
una razon metodologica fuerte para mantenerlas separadas.

## 5. Entorno Tecnico

- Sistema operativo de trabajo: Linux.
- Pipeline ETL: Python.
- Analisis estadistico: R.
- Formato de salida final: CSV.
- Dependencia externa para P4/P5 CAB: `cabextract` disponible en el sistema.

Los scripts Python deben quedar bajo `command-files/processing-command-files/`.
Los scripts R deben quedar bajo `command-files/analysis-command-files/`, salvo que se defina una subestructura mas especifica.

## 6. Datos De Entrada

Los archivos fuente originales deben mantenerse sin edicion manual. Los datos originales deben guardarse en `data/input-data/raw/`, salvo que por tamano, privacidad o licencia deban documentarse y reconstruirse desde una fuente externa.

Para esta fuente, los comprimidos originales descargados desde AFIP/ARCA estan en:

```text
data/input-data/raw/afip-estadisticas-tributarias/
```

La extraccion de XLS, CAB o HTML debe ser reproducible y no debe reemplazar los originales.
Los ZIP de AFIP no estan ignorados por `.gitignore`, por decision explicita del investigador, para permitir respaldo local en GitHub.

## 7. Comandos

Los scripts deben ejecutarse desde la raiz del repositorio. Los scripts de procesamiento deben usar prefijos numericos para fijar el orden de ejecucion.

Ejemplo:

```bash
python3 command-files/processing-command-files/00_prepare_directories.py
```

El flujo minimo actual se ejecuta con:

```bash
python3 command-files/run_all.py
```

## 8. Configuracion

Las rutas, periodos, nombres esperados y constantes compartidas deben definirse en `command-files/config/project_config.py`. No duplicar constantes entre scripts.

## 9. Artefactos Esperados

La salida canonica actual de datos de analisis se guarda como CSV tidy
comprimido y fechado:

```text
data/analysis-data/2026-05-31_afip_ganancias_sociedades_tidy_homologado.csv.gz
```

Los diccionarios de trazabilidad asociados se generan como archivos
intermedios regenerables en `data/intermediate-data/afip-estadisticas-tributarias/`.

## 10. Estado Actual

El directorio contiene el andamiaje TIER inicial y los datos crudos AFIP:

- Existen 26 ZIP crudos en `data/input-data/raw/afip-estadisticas-tributarias/`.
- La estructura de esos ZIP ya fue inventariada de forma preliminar.
- Se implemento el inventario P0 moderno y extractores/validadores para las 20 tablas de actividad `2.3.1.1.*` del periodo P0 principal.
- Se completo P0 para publication years 2015-2023 / fiscal years 2014-2022.
- Se ensamblo `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0.csv` con 491.435 filas largas y 20 cuadros fuente.
- La validacion consolidada P0 (`45_validate_ganancias_sociedades_p0_long.py`) termino con 0 fallas y 0 advertencias.
- El inventario retrospectivo P0 tiene 112 filas, 0 fallas y 17 advertencias estructurales documentadas.
- La prueba retrospectiva de detectores P0 cubrio 112 archivos/cuadros y actualmente no registra advertencias duras despues de adaptar los detectores.
- Las advertencias vigentes por cuadro estan documentadas en `documentation/afip/warnings_by_period.md`.
- Se completo P1 para publication year 2014 / fiscal year 2013.
- Se genero `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p1.csv` con 13 cuadros de actividad HTML.
- Se genero `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p1.csv` con 37.088 filas largas y 127 variables.
- La validacion P1 (`51_validate_ganancias_sociedades_p1_long.py`) termino con 0 fallas y 0 advertencias.
- Las notas estructurales P1 estan documentadas en `documentation/afip/warnings_by_period.md`.
- Se completo P2 para publication year 2013 / fiscal year 2012.
- Se genero `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p2.csv` con 13 cuadros de actividad HTML.
- Se genero `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p2.csv` con 27.208 filas largas y 127 variables.
- La validacion P2 (`54_validate_ganancias_sociedades_p2_long.py`) termino con 0 fallas y 0 advertencias.
- Las notas estructurales P2 estan documentadas en `documentation/afip/warnings_by_period.md`.
- Se completo P3 para publication years 2009-2012 / fiscal years 2008-2011.
- Se genero `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p3.csv` con 49 pares anio-cuadro HTML.
- Se genero `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p3.csv` con 97.775 filas largas y 129 variables.
- La validacion P3 (`57_validate_ganancias_sociedades_p3_long.py`) termino con 0 fallas y 10 advertencias estructurales.
- Las advertencias P3 estan documentadas en `documentation/afip/warnings_by_period.md`.
- Se completo P4 para publication years 2003-2008 / fiscal years 2002-2007.
- Se genero `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p4.csv` con 60 pares anio-cuadro XLS dentro de `AFIP.CAB`.
- Se genero `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p4.csv` con 132.088 filas largas y 111 variables.
- La validacion P4 (`60_validate_ganancias_sociedades_p4_long.py`) termino con 0 fallas y 25 advertencias documentadas.
- Las advertencias P4 estan documentadas en `documentation/afip/warnings_by_period.md`.
- Se completo P5 para publication year 2002 / fiscal years 1999-2001, con 31.229 filas largas y validacion de 0 fallas.
- Se completo P6 para publication years 1998-1999 / fiscal years 1997-1998, con 3.044 filas largas y validacion de 0 fallas.
- Se reemplazaron los CSV completos de analisis por `data/analysis-data/2026-05-31_afip_ganancias_sociedades_tidy_homologado.csv.gz`, con 819.867 filas y 11.758.387 bytes.
- Se genero el diccionario de fuente `data/intermediate-data/afip-estadisticas-tributarias/2026-05-31_afip_ganancias_sociedades_source_dictionary.csv` con 320 entradas.
- Se genero el diccionario de actividad `data/intermediate-data/afip-estadisticas-tributarias/2026-05-31_afip_ganancias_sociedades_activity_dictionary.csv` con 569 entradas.
- Se genero el diccionario de homologacion `data/intermediate-data/afip-estadisticas-tributarias/2026-05-31_afip_ganancias_sociedades_ramas_homologacion_diccionario.csv` con 569 entradas.
- La validacion final vigente (`68_validate_ganancias_sociedades_tidy_outputs.py`) termino con 0 fallas y 0 advertencias.
- Existe un `.git` vacio/invalido de solo lectura; no debe tratarse como repositorio activo.
- El repositorio Git operativo usa metadata separada en `.git-local`, con remoto `https://github.com/feliperuizbruzzone/economia-argentina.git`.
- `.gitignore` permite versionar los ZIP de AFIP y el panel final `.csv.gz`; ignora CSV sin comprimir regenerables, intermedios y reportes.

## 11. Decisiones Pendientes

No implementar sin decision explicita del investigador:

- Diccionario definitivo de variables derivadas de rentabilidad y desempeno.
- Reglas de empalme, deflactacion, estacionalidad, cambio de base o cambio de clasificacion sectorial.
- Criterios para reconciliar estructuras heterogeneas de XLS entre anios.
- Tratamiento definitivo de faltantes, outliers, confidencialidad o datos suprimidos.
- Criterios para excluir, imputar o transformar observaciones.
- Homologacion fina de ramas a 3 digitos entre clasificador viejo y nuevo. La version actual solo agrega rama comun amplia de serie completa y preserva el detalle fuente namespaced.

Decisiones ya tomadas:

- El universo empirico inicial es el capitulo `Impuesto a las Ganancias Sociedades`.
- La salida canonica debe ser formato largo.
- El pipeline debe preservar el maximo nivel de desagregacion observable por periodo.
- La unidad fisica de fila de la base larga debe ser una celda estadistica normalizada: `fiscal_year x source_table_id x dimension_type x dimension_value x variable_name`, con metadatos de actividad, universo, unidad y fuente.
- La homologacion de ramas no reemplaza las columnas fuente. Agrega `rama_comun_*` para comparabilidad amplia 1997-2022 y `rama_detalle_homologada_*` para conservar el maximo detalle observado por clasificador.

## 12. Comparabilidad Para Ganancias Sociedades

La tabla de comparabilidad detallada vive en:

```text
documentation/afip/variable_comparability.md
```

El diseno modular del ETL vive en:

```text
documentation/afip/etl_design.md
```

El plan y diccionario metodologico de homologacion de ramas vive en:

```text
documentation/afip/branch_harmonization.md
```

Resumen operativo por periodo homogeneo:

| Periodo | Publication years | Fiscal years | Formato | Clasificador / detalle | Unidad montos | Nota de discontinuidad |
|---|---:|---:|---|---|---|---|
| `P0_new_xls_detail` | 2015-2023 | 2014-2022 | XLS directo | Clasificador nuevo; seccion y 3 digitos | Millones | Mejor base inicial. |
| `P1_new_html_detail` | 2014 | 2013 | HTML Excel | Clasificador nuevo; detalle en archivo/hoja secundaria | Millones | Parser HTML; primer anio con clasificador nuevo observado. |
| `P2_old_html_detail_millions` | 2013 | 2012 | HTML Excel | Clasificador viejo; detalle en hoja secundaria | Millones | Quiebre de unidad respecto de fiscal 2011. |
| `P3_old_html_detail_thousands` | 2009-2012 | 2008-2011 | HTML Excel | Clasificador viejo; detalle en `sheet002.htm` | Miles | Parser HTML; no usar solo `sheet001.htm` si se busca maxima desagregacion. |
| `P4_old_cab_xls_detail_thousands` | 2003-2008 | 2002-2007 | XLS dentro de CAB | Clasificador viejo; detalle en continuaciones `_2` | Miles | Numeracion `2.3.*`; resultados condensados y componente `OTROS` en costos. |
| `P5_old_cab_xls_detail_legacy_numbering` | 2002 canonico | 1999-2001 | XLS dentro de CAB | Clasificador viejo; detalle en continuaciones `_2` para fiscal 1999-2001 | Miles | Numeracion `3.3.*`; duplicados resueltos con publication year 2002. |
| `P6_legacy_broad_activity` | 1998-1999 | 1997-1998 | XLS directo | Fiscal 1997 amplio; fiscal 1998 con detalle 3 digitos en `_2` | Miles | Numeracion `4.4.*` en 1997 y `3.3.*` en 1998; detalle sectorial mixto. |

Tabla de variables de interes:

| Familia de variables | P0 | P1 | P2 | P3 | P4 | P5 | P6 | Nota |
|---|---|---|---|---|---|---|---|---|
| `activity_section` | Si | Si | Si | Si | Si | Si | Si | No comparar secciones viejo/nuevo sin correspondencia. |
| `activity_3digit` | Si | Si | Si | Si | Si | Si | Parcial | Fiscal 1998 si trae `_2` con 3 digitos; fiscal 1997 no. |
| `presentaciones_total` | Si | Si | Si | Si | Si | Si | Si | Alta comparabilidad. |
| `presentaciones_con_ventas` | Si | Si | Si | Si | Si | Si | Si | Alta comparabilidad. |
| `presentaciones_con_impuesto_determinado` | Si | Si | Si | Si | Si | Parcial | No | Antes aparece conteo `con ganancia neta imponible`; mantener variable separada. |
| `ventas_netasy_locaciones` | Si | Si | Si | Si | Si | Si | Si | Normalizar miles/millones. |
| `ganancia_neta_imponible` | Si | Si | Si | Si | Si | Si | Si | Comparable con cautela legal/metodologica. |
| `impuesto_determinado` | Si | Si | Si | Si | Si | Si | Si | Comparable como monto fiscal; normalizar unidad. |
| `costos_total` | Si | Si | Si | Si | Si | Si | Si | Detalle de componentes cambia por periodo. |
| `resultado_bruto` | Si | Si | Si | Si | Si | Si | Si | Utilidad y perdida deben conservarse; neto es derivado. |
| `resultado_contable` | Si | Si | Si | Si | Si | Si | Si | En periodos viejos puede llamarse resultado final del ejercicio. |
| `resultado_impositivo` | Si | Si | Si | Si | Si | Si | Si | Mantener utilidad/perdida/quebranto como variables separadas. |
| `activo_total` | Si | Si | Si | Si | Si | Si | Si | Alta comparabilidad tras normalizar unidad. |
| `pasivo_total` | Si | Si | Si | Si | Si | Si | Si | Alta comparabilidad tras normalizar unidad. |
| `patrimonio_neto_inicio_cierre` | Si | Si | Si | Si | Si | Si | Si | Revisar signos y patrimonios negativos/cero. |
| `componentes_activo_pasivo_patrimonio` | Si | Si | Si | Si | Si | Parcial | No/Parcial | No forzar hacia atras sin agregacion. |
| `mes_cierre` | Si | Si | Si | Si | Si | No | No | Usar como dimension parcial, no comun a toda la serie. |
| `tramos_ventas` | Si | Si | Si | Si | Si | Si | Si | Validar cortes nominales por anio. |
| `tramos_ganancia_neta_imponible` | Si | Si | Si | Si | Si | Si | Si | Validar cortes nominales por anio. |

## 13. Plan De Trabajo Sistematizado

El trabajo debe avanzar por fases, construyendo una serie larga homologable desde el ultimo fiscal year disponible hacia atras.

### Fase 0: base reproducible

Estado: completada.

- Andamiaje TIER creado.
- Configuracion central en `command-files/config/project_config.py`.
- 26 ZIP crudos descargados y validados.
- Mapeo estructural preliminar documentado.

### Fase 1: inventario canonico del capitulo Ganancias Sociedades

Objetivo: convertir el mapeo preliminar en un inventario tabular estable solo para `Impuesto a las Ganancias Sociedades`.

Producto esperado:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory.csv
```

Campos minimos:

- `publication_year`
- `fiscal_year`
- `archive_filename`
- `period_id`
- `source_table_id`
- `source_table_title`
- `source_table_path`
- `chapter_code_original`
- `table_family`
- `dimension_type`
- `universe`
- `format`
- `unit_original`
- `has_activity_section`
- `has_activity_3digit`
- `is_continuation`
- `notes`

### Fase 2: parser base hacia atras, P0

Objetivo original: implementar primero funciones auxiliares pequenas y probadas para `P0_new_xls_detail`, publication years 2021-2023 y fiscal years 2020-2022.

Estado actual: P0 principal ya fue ampliado y completado para publication years 2015-2023 / fiscal years 2014-2022. P1 HTML tambien fue completado para publication year 2014 / fiscal year 2013. P2 HTML viejo en millones fue completado para publication year 2013 / fiscal year 2012. P3 HTML viejo en miles fue completado para publication years 2009-2012 / fiscal years 2008-2011.

Las notas de extractos piloto que siguen documentan el desarrollo incremental; el estado operativo vigente del P0 completo esta en "Estado Actual" y en `documentation/afip/warnings_by_period.md`.

Criterio:

- XLS directo.
- Clasificador nuevo.
- Detalle de actividad a seccion y 3 digitos.
- Tablas `2.3.*`.
- Salida larga.
- Deteccion automatica de filas de encabezado y comienzo de datos; no usar numeros de fila hard-codeados en extractores.

Producto esperado:

```text
data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0.csv
```

Primera funcion implementada/probada:

- `detect_xls_table_bounds(rows)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Probe concreto: `python3 command-files/processing-command-files/01_probe_ganancias_sociedades_bounds.py`.
- Ejemplo usado: ZIP 2023, tabla `2.3.1.1.1.xls`.

Primer inventario implementado:

- Funcion: `inventory_p0_modern_xls(raw_archive_dir)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Script: `python3 command-files/processing-command-files/02_build_ganancias_sociedades_inventory.py`.
- Alcance actual: publication years 2015-2023, fiscal years 2014-2022, tablas `2.3.*`.
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory.csv`.
- Estado: generado y validado con 892 filas para el inventario de actividad P0; 0 fallas y 8 advertencias estructurales.

Primera validacion formal implementada:

- Script: `python3 command-files/processing-command-files/03_validate_ganancias_sociedades_p0_activity_inventory.py`.
- Alcance: tablas `2.3.1.1.*`, dimension `actividad_economica`, publication years 2015-2023.
- Resultado actual: 892 filas validadas, fiscal years 2014-2022, 0 errores y 8 advertencias estructurales.
- Advertencias conocidas: fiscal year 2014 trae continuaciones `_2-`; fiscal years 2014-2016 no traen varios subcuadros patrimoniales recientes; fiscal year 2022, tabla `2.3.1.1.5.2.1`, no trae fila `TOTAL`. No imputar totales ni subcuadros ausentes.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_activity_inventory_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_activity_inventory_validation.csv`

Primer extracto largo piloto implementado:

- Funcion: `extract_p0_23111_activity_summary(raw_archive_dir, inventory_rows)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Script: `python3 command-files/processing-command-files/04_extract_ganancias_sociedades_p0_2_3_1_1_1.py`.
- Alcance: tabla `2.3.1.1.1`, publication years 2021-2023, fiscal years 2020-2022.
- Variables extraidas:
  - `presentaciones_total`
  - `presentaciones_con_ventas`
  - `presentaciones_con_impuesto_determinado`
  - `ventas_bienes_servicios_locaciones_netas`
  - `ganancia_neta_imponible`
  - `impuesto_determinado`
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_1.csv`.
- Resultado actual: 4.344 filas largas, con 724 filas por variable.
- Validacion: `python3 command-files/processing-command-files/05_validate_ganancias_sociedades_p0_2_3_1_1_1.py`, 0 errores y 0 advertencias.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_1_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_1_validation_counts.csv`

Segundo extracto largo piloto implementado:

- Funcion: `extract_p0_231121_activity_costs(raw_archive_dir, inventory_rows)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Script: `python3 command-files/processing-command-files/06_extract_ganancias_sociedades_p0_2_3_1_1_2_1.py`.
- Alcance: tabla `2.3.1.1.2.1`, publication years 2021-2023, fiscal years 2020-2022.
- Variables extraidas:
  - `presentaciones_total`
  - `presentaciones_con_ventas`
  - `ventas_bienes_servicios_locaciones_netas`
  - `costos_total_casos`
  - `costos_total`
  - `compras_netas_casos`
  - `compras_netas`
  - `gastos_produccion_casos`
  - `gastos_produccion`
  - `gastos_vinculados_al_costo_casos`
  - `gastos_vinculados_al_costo`
  - `existencia_inicial_casos`
  - `existencia_inicial`
  - `existencia_final_casos`
  - `existencia_final`
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_2_1.csv`.
- Resultado actual: 10.860 filas largas, con 724 filas por variable.
- Validacion: `python3 command-files/processing-command-files/07_validate_ganancias_sociedades_p0_2_3_1_1_2_1.py`, 0 errores y 0 advertencias.
- Checkpoint cruzado: 2.172 filas solapadas con `2.3.1.1.1` comparadas sin discrepancias para `presentaciones_total`, `presentaciones_con_ventas` y `ventas_bienes_servicios_locaciones_netas`.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_2_1_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_2_1_validation_counts.csv`

Tercer extracto largo piloto implementado:

- Funcion: `extract_p0_231122_activity_sales_detail(raw_archive_dir, inventory_rows)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Script: `python3 command-files/processing-command-files/08_extract_ganancias_sociedades_p0_2_3_1_1_2_2.py`.
- Alcance: tabla `2.3.1.1.2.2`, publication years 2021-2023, fiscal years 2020-2022.
- Variables extraidas:
  - `presentaciones_total`
  - `presentaciones_con_ventas`
  - `ventas_bienes_servicios_locaciones_netas`
  - `ventas_gravadas_mercado_local_sujetos_vinculados_casos`
  - `ventas_gravadas_mercado_local_sujetos_vinculados`
  - `ventas_exentas_mercado_local_casos`
  - `ventas_exentas_mercado_local`
  - `exportaciones_baja_nula_imposicion_sin_detraer_derechos_casos`
  - `exportaciones_baja_nula_imposicion_sin_detraer_derechos`
  - `exportaciones_exentas_casos`
  - `exportaciones_exentas`
  - `otras_ventas_gravadas_mercado_local_casos`
  - `otras_ventas_gravadas_mercado_local`
  - `exportaciones_vinculados_sin_detraer_derechos_excluye_baja_nula_casos`
  - `exportaciones_vinculados_sin_detraer_derechos_excluye_baja_nula`
  - `otras_exportaciones_sin_detraer_derechos_casos`
  - `otras_exportaciones_sin_detraer_derechos`
  - `total_ventas_servicios_locaciones_ejercicio_casos`
  - `total_ventas_servicios_locaciones_ejercicio`
  - `derechos_exportacion_casos`
  - `derechos_exportacion`
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_2_2.csv`.
- Resultado actual: 15.204 filas largas, con 724 filas por variable.
- Validacion: `python3 command-files/processing-command-files/09_validate_ganancias_sociedades_p0_2_3_1_1_2_2.py`, 0 errores y 0 advertencias.
- Checkpoints cruzados:
  - 2.172 filas solapadas con `2.3.1.1.1`, sin discrepancias relevantes usando tolerancia decimal para montos.
  - 2.172 filas solapadas con `2.3.1.1.2.1`, sin discrepancias relevantes usando tolerancia decimal para montos.
  - Identidades internas sin fallas: `ventas_bienes_servicios_locaciones_netas + derechos_exportacion = total_ventas_servicios_locaciones_ejercicio`; los componentes detallados de ventas suman al total de ventas del ejercicio.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_2_2_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_2_2_validation_counts.csv`

Cuarto extracto largo piloto implementado:

- Funcion: `extract_p0_231123_activity_cost_linked_expenses(raw_archive_dir, inventory_rows)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Script: `python3 command-files/processing-command-files/10_extract_ganancias_sociedades_p0_2_3_1_1_2_3.py`.
- Alcance: tabla `2.3.1.1.2.3`, publication years 2021-2023, fiscal years 2020-2022.
- Variables extraidas:
  - `presentaciones_total`
  - `gastos_vinculados_al_costo`
  - `depreciacion_bienes_uso_casos`
  - `depreciacion_bienes_uso`
  - `honorarios_retribuciones_servicios_casos`
  - `honorarios_retribuciones_servicios`
  - `otros_gastos_vinculados_al_costo_casos`
  - `otros_gastos_vinculados_al_costo`
  - `sueldos_aguinaldos_gratificaciones_contribuciones_social_casos`
  - `sueldos_aguinaldos_gratificaciones_contribuciones_social`
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_2_3.csv`.
- Resultado actual: 7.240 filas largas, con 724 filas por variable.
- Validacion: `python3 command-files/processing-command-files/11_validate_ganancias_sociedades_p0_2_3_1_1_2_3.py`, 0 errores y 0 advertencias.
- Checkpoints:
  - 1.448 filas solapadas con `2.3.1.1.2.1`, sin discrepancias para `presentaciones_total` y `gastos_vinculados_al_costo`.
  - Identidad interna sin fallas: la suma de componentes de gastos vinculados al costo coincide con `gastos_vinculados_al_costo`.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_2_3_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_2_3_validation_counts.csv`

Quinto extracto largo piloto implementado:

- Funcion: `extract_p0_231124_activity_gross_result(raw_archive_dir, inventory_rows)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Script: `python3 command-files/processing-command-files/12_extract_ganancias_sociedades_p0_2_3_1_1_2_4.py`.
- Alcance: tabla `2.3.1.1.2.4`, publication years 2021-2023, fiscal years 2020-2022.
- Variables extraidas:
  - `presentaciones_total`
  - `resultado_bruto_utilidad_casos`
  - `resultado_bruto_utilidad`
  - `resultado_bruto_perdida_casos`
  - `resultado_bruto_perdida`
  - `resultado_venta_acciones_utilidad_casos`
  - `resultado_venta_acciones_utilidad`
  - `resultado_venta_acciones_perdida_casos`
  - `resultado_venta_acciones_perdida`
  - `cargo_deudores_incobrables_casos`
  - `cargo_deudores_incobrables`
  - `gastos_operativos_casos`
  - `gastos_operativos`
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_2_4.csv`.
- Resultado actual: 9.412 filas largas, con 724 filas por variable.
- Validacion: `python3 command-files/processing-command-files/13_validate_ganancias_sociedades_p0_2_3_1_1_2_4.py`, 0 errores y 0 advertencias.
- Checkpoints:
  - 724 filas solapadas con `2.3.1.1.2.1`, sin discrepancias para `presentaciones_total`.
  - Identidad cruzada sin fallas: `resultado_bruto_utilidad - resultado_bruto_perdida = ventas_bienes_servicios_locaciones_netas - costos_total`.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_2_4_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_2_4_validation_counts.csv`

Sexto extracto largo piloto implementado:

- Funcion: `extract_p0_231125_activity_operating_expenses(raw_archive_dir, inventory_rows)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Script: `python3 command-files/processing-command-files/14_extract_ganancias_sociedades_p0_2_3_1_1_2_5.py`.
- Alcance: tabla `2.3.1.1.2.5`, publication years 2021-2023, fiscal years 2020-2022.
- Variables extraidas:
  - `presentaciones_total`
  - `gastos_operativos`
  - `depreciacion_bienes_uso_casos`
  - `depreciacion_bienes_uso`
  - `gastos_representacion_casos`
  - `gastos_representacion`
  - `honorarios_directores_casos`
  - `honorarios_directores`
  - `honorarios_retribuciones_servicios_casos`
  - `honorarios_retribuciones_servicios`
  - `otros_gastos_operativos_casos`
  - `otros_gastos_operativos`
  - `sueldos_aguinaldos_gratificaciones_contribuciones_social_casos`
  - `sueldos_aguinaldos_gratificaciones_contribuciones_social`
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_2_5.csv`.
- Resultado actual: 10.136 filas largas, con 724 filas por variable.
- Validacion: `python3 command-files/processing-command-files/15_validate_ganancias_sociedades_p0_2_3_1_1_2_5.py`, 0 errores y 1 advertencia.
- Checkpoints:
  - 1.448 filas solapadas con `2.3.1.1.2.4`.
  - Identidad interna sin fallas: la suma de los seis componentes de gastos operativos coincide con `gastos_operativos`.
  - Advertencia de fuente: fiscal year 2022, actividad `071;072`, `gastos_operativos` difiere entre `2.3.1.1.2.5` (`61551.43299154999`) y `2.3.1.1.2.4` (`59553.57273721999`). Se conserva el valor especifico de cada tabla; no imputar ni sobrescribir.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_2_5_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_2_5_validation_counts.csv`

Septimo extracto largo piloto implementado:

- Funcion: `extract_p0_231126_activity_other_results(raw_archive_dir, inventory_rows)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Script: `python3 command-files/processing-command-files/16_extract_ganancias_sociedades_p0_2_3_1_1_2_6.py`.
- Alcance: tabla `2.3.1.1.2.6`, publication years 2021-2023, fiscal years 2020-2022.
- Variables extraidas:
  - `presentaciones_total`
  - `resultado_inversiones_permanentes_utilidad_casos`
  - `resultado_inversiones_permanentes_utilidad`
  - `resultado_inversiones_permanentes_quebranto_casos`
  - `resultado_inversiones_permanentes_quebranto`
  - `resultados_financieros_utilidad_casos`
  - `resultados_financieros_utilidad`
  - `resultados_financieros_quebranto_casos`
  - `resultados_financieros_quebranto`
  - `resultados_contratos_derivados_utilidad_casos`
  - `resultados_contratos_derivados_utilidad`
  - `resultados_contratos_derivados_quebranto_casos`
  - `resultados_contratos_derivados_quebranto`
  - `otros_ingresos_egresos_utilidad_casos`
  - `otros_ingresos_egresos_utilidad`
  - `otros_ingresos_egresos_quebranto_casos`
  - `otros_ingresos_egresos_quebranto`
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_2_6.csv`.
- Resultado actual: 12.308 filas largas, con 724 filas por variable.
- Validacion: `python3 command-files/processing-command-files/17_validate_ganancias_sociedades_p0_2_3_1_1_2_6.py`, 0 errores y 0 advertencias.
- Checkpoints:
  - 724 filas solapadas con `2.3.1.1.1`, sin discrepancias para `presentaciones_total`.
  - Cobertura completa por variable, fiscal year y conjunto de actividades; no se aplico identidad contable porque esta tabla no trae un total cerrado observable en las tablas ya extraidas.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_2_6_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_2_6_validation_counts.csv`

Octavo extracto largo piloto implementado:

- Funcion: `extract_p0_231127_activity_accounting_result(raw_archive_dir, inventory_rows)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Script: `python3 command-files/processing-command-files/18_extract_ganancias_sociedades_p0_2_3_1_1_2_7.py`.
- Alcance: tabla `2.3.1.1.2.7`, publication years 2021-2023, fiscal years 2020-2022.
- Variables extraidas:
  - `presentaciones_total`
  - `resultados_extraordinarios_utilidad_casos`
  - `resultados_extraordinarios_utilidad`
  - `resultados_extraordinarios_quebranto_casos`
  - `resultados_extraordinarios_quebranto`
  - `impuesto_ganancias_casos`
  - `impuesto_ganancias`
  - `resultado_contable_utilidad_casos`
  - `resultado_contable_utilidad`
  - `resultado_contable_perdida_casos`
  - `resultado_contable_perdida`
  - `resultado_final_contable_juegos_azar_apuestas_casos` solo fiscal year 2022.
  - `resultado_final_contable_juegos_azar_apuestas` solo fiscal year 2022.
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_2_7.csv`.
- Resultado actual: 8.448 filas largas. Las variables comunes tienen 724 filas cada una; las dos variables de juegos de azar/apuestas tienen 242 filas cada una y solo existen en fiscal year 2022.
- Validacion: `python3 command-files/processing-command-files/19_validate_ganancias_sociedades_p0_2_3_1_1_2_7.py`, 0 errores y 1 advertencia.
- Checkpoints:
  - 724 filas solapadas con `2.3.1.1.1`, sin discrepancias para `presentaciones_total`.
  - La validacion acepta las columnas de juegos de azar/apuestas como discontinuidad estructural interna de P0 en fiscal year 2022, no como faltante de 2020-2021.
  - No se aplico identidad contable cerrada para `resultado_contable` porque requiere decisiones metodologicas sobre los componentes y el tratamiento de juegos de azar/apuestas.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_2_7_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_2_7_validation_counts.csv`

Noveno extracto largo piloto implementado:

- Funcion: `extract_p0_23113_activity_tax_result(raw_archive_dir, inventory_rows)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Script: `python3 command-files/processing-command-files/20_extract_ganancias_sociedades_p0_2_3_1_1_3.py`.
- Alcance: tabla `2.3.1.1.3`, publication years 2021-2023, fiscal years 2020-2022.
- Variables extraidas:
  - `presentaciones_total`
  - `importes_aumentan_utilidad_o_disminuyen_perdida_casos`
  - `importes_aumentan_utilidad_o_disminuyen_perdida`
  - `importes_disminuyen_utilidad_o_aumentan_perdida_casos`
  - `importes_disminuyen_utilidad_o_aumentan_perdida`
  - `resultado_impositivo_utilidad_casos`
  - `resultado_impositivo_utilidad`
  - `resultado_impositivo_perdida_casos`
  - `resultado_impositivo_perdida`
  - `quebranto_computable_casos`
  - `quebranto_computable`
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_3.csv`.
- Resultado actual: 7.964 filas largas, con 724 filas por variable.
- Validacion: `python3 command-files/processing-command-files/21_validate_ganancias_sociedades_p0_2_3_1_1_3.py`, 0 errores y 1 advertencia.
- Checkpoints:
  - 724 filas solapadas con `2.3.1.1.1`, sin discrepancias para `presentaciones_total`.
  - Advertencia de fuente: fiscal year 2020 tiene encabezado incompleto para `resultado_impositivo_perdida`; la extraccion mapea esas columnas por bloque semantico y evidencia de columnas adyacentes.
  - No se aplico identidad contable contra `ganancia_neta_imponible` porque requiere definir metodologicamente como tratar `resultado_impositivo`, `perdida` y `quebranto_computable`.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_3_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_3_validation_counts.csv`

Decimo extracto largo piloto implementado:

- Funcion: `extract_p0_23114_activity_tax_determination(raw_archive_dir, inventory_rows)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Script: `python3 command-files/processing-command-files/22_extract_ganancias_sociedades_p0_2_3_1_1_4.py`.
- Alcance: tabla `2.3.1.1.4`, publication years 2021-2023, fiscal years 2020-2022.
- Variables extraidas:
  - `presentaciones_total`
  - `resultado_neto_utilidad_casos`
  - `resultado_neto_utilidad`
  - `resultado_neto_perdida_casos`
  - `resultado_neto_perdida`
  - `resultado_atribuible_socios_utilidad_casos`
  - `resultado_atribuible_socios_utilidad`
  - `resultado_atribuible_socios_perdida_casos`
  - `resultado_atribuible_socios_perdida`
  - `resultado_neto_final_utilidad_casos`
  - `resultado_neto_final_utilidad`
  - `resultado_neto_final_perdida_casos`
  - `resultado_neto_final_perdida`
  - `impuesto_determinado_casos`
  - `impuesto_determinado`
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_4.csv`.
- Resultado actual: 10.860 filas largas, con 724 filas por variable.
- Validacion: `python3 command-files/processing-command-files/23_validate_ganancias_sociedades_p0_2_3_1_1_4.py`, 0 errores y 0 advertencias.
- Checkpoints:
  - 2.172 filas solapadas con `2.3.1.1.1`, sin discrepancias para `presentaciones_total`, `resultado_neto_final_utilidad` contra `ganancia_neta_imponible`, e `impuesto_determinado`.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_4_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_4_validation_counts.csv`

Undecimo extracto largo piloto implementado:

- Funcion: `extract_p0_231151_activity_assets(raw_archive_dir, inventory_rows)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Script: `python3 command-files/processing-command-files/24_extract_ganancias_sociedades_p0_2_3_1_1_5_1.py`.
- Alcance: tabla `2.3.1.1.5.1`, publication years 2021-2023, fiscal years 2020-2022.
- Variables extraidas:
  - `presentaciones_total`
  - `activo_total_casos`
  - `activo_total`
  - `activo_disponibilidades_casos`
  - `activo_disponibilidades`
  - `activo_creditos_casos`
  - `activo_creditos`
  - `activo_bienes_cambio_casos`
  - `activo_bienes_cambio`
  - `activo_inversiones_casos`
  - `activo_inversiones`
  - `activo_bienes_uso_casos`
  - `activo_bienes_uso`
  - `activo_bienes_intangibles_casos`
  - `activo_bienes_intangibles`
  - `activo_obras_construccion_casos`
  - `activo_obras_construccion`
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_5_1.csv`.
- Resultado actual: 12.308 filas largas, con 724 filas por variable.
- Validacion: `python3 command-files/processing-command-files/25_validate_ganancias_sociedades_p0_2_3_1_1_5_1.py`, 0 errores y 0 advertencias.
- Checkpoints:
  - 724 filas solapadas con `2.3.1.1.1`, sin discrepancias para `presentaciones_total`.
  - Identidad interna sin fallas: disponibilidades, creditos, bienes de cambio, inversiones, bienes de uso, bienes intangibles y obras en construccion suman `activo_total`.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_5_1_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_5_1_validation_counts.csv`

Duodecimo extracto largo piloto implementado:

- Funcion: `extract_p0_2311511_activity_cash_assets(raw_archive_dir, inventory_rows)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Script: `python3 command-files/processing-command-files/26_extract_ganancias_sociedades_p0_2_3_1_1_5_1_1.py`.
- Alcance: tabla `2.3.1.1.5.1.1`, publication years 2021-2023, fiscal years 2020-2022.
- Variables extraidas:
  - `presentaciones_total`
  - `activo_disponibilidades_casos`
  - `activo_disponibilidades`
  - `activo_cheques_cartera_casos`
  - `activo_cheques_cartera`
  - `activo_efectivo_moneda_nacional_casos`
  - `activo_efectivo_moneda_nacional`
  - `activo_total_bancos_casos`
  - `activo_total_bancos`
  - `activo_efectivo_moneda_extranjera_casos`
  - `activo_efectivo_moneda_extranjera`
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_5_1_1.csv`.
- Resultado actual: 7.964 filas largas, con 724 filas por variable.
- Validacion: `python3 command-files/processing-command-files/27_validate_ganancias_sociedades_p0_2_3_1_1_5_1_1.py`, 0 errores y 0 advertencias.
- Checkpoints:
  - 1.448 filas solapadas con `2.3.1.1.5.1`, sin discrepancias para `presentaciones_total` y `activo_disponibilidades`.
  - Identidad interna sin fallas: cheques en cartera, efectivo moneda nacional, total bancos y efectivo moneda extranjera suman `activo_disponibilidades`.
  - El detector prioriza `TOTAL BANCOS` antes que `DISPONIBILIDADES TOTAL` para resolver el solapamiento semantico de encabezados sin usar posiciones fijas.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_5_1_1_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_5_1_1_validation_counts.csv`

Decimotercer extracto largo piloto implementado:

- Funcion: `extract_p0_2311512_activity_credit_assets(raw_archive_dir, inventory_rows)` en `command-files/processing-command-files/afip_ganancias_sociedades.py`.
- Script: `python3 command-files/processing-command-files/28_extract_ganancias_sociedades_p0_2_3_1_1_5_1_2.py`.
- Alcance: tabla `2.3.1.1.5.1.2`, publication years 2021-2023, fiscal years 2020-2022.
- Variables extraidas:
  - `presentaciones_total`
  - `activo_creditos_casos`
  - `activo_creditos`
  - `activo_creditos_previsiones_casos`
  - `activo_creditos_previsiones`
  - `activo_creditos_deudores_ventas_servicios_casos`
  - `activo_creditos_deudores_ventas_servicios`
  - `activo_creditos_soc_controlada_controlante_vinculada_casos`
  - `activo_creditos_soc_controlada_controlante_vinculada`
  - `activo_creditos_cuentas_particulares_socios_casos`
  - `activo_creditos_cuentas_particulares_socios`
  - `activo_creditos_otros_casos`
  - `activo_creditos_otros`
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0_2_3_1_1_5_1_2.csv`.
- Resultado actual: 9.400 filas largas. Las variables de creditos tienen 723 filas; `presentaciones_total` tiene 724 filas.
- Validacion: `python3 command-files/processing-command-files/29_validate_ganancias_sociedades_p0_2_3_1_1_5_1_2.py`, 0 errores y 2 advertencias.
- Checkpoints:
  - 1.447 filas solapadas con `2.3.1.1.5.1`, sin discrepancias en valores observados para `presentaciones_total` y `activo_creditos`.
  - Identidad interna sin fallas: deudores por ventas/servicios, sociedades vinculadas, cuentas particulares de socios y otros, menos previsiones, suman `activo_creditos`.
  - Advertencia de fuente: fiscal year 2020, actividad `352;353`, la tabla detallada `2.3.1.1.5.1.2` trae `presentaciones_total=40` pero deja en blanco todas las columnas de creditos; la tabla agregada `2.3.1.1.5.1` si informa `activo_creditos=79244.52968623998`. No imputar desde el agregado en la extraccion base.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_5_1_2_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_2_3_1_1_5_1_2_validation_counts.csv`

Extractos largos P0 restantes implementados:

| Tabla | Tema | Script extractor | Filas | Validacion | Checkpoints |
|---|---|---|---:|---|---|
| `2.3.1.1.5.1.3` | Bienes de cambio | `30_extract_ganancias_sociedades_p0_2_3_1_1_5_1_3.py` | 9.412 | 0 errores, 0 advertencias | Solapa con `2.3.1.1.5.1`; componentes suman `activo_bienes_cambio`. |
| `2.3.1.1.5.1.4` | Bienes de uso | `32_extract_ganancias_sociedades_p0_2_3_1_1_5_1_4.py` | 7.964 | 0 errores, 0 advertencias | Solapa con `2.3.1.1.5.1`; componentes suman `activo_bienes_uso`. |
| `2.3.1.1.5.2` | Pasivo | `34_extract_ganancias_sociedades_p0_2_3_1_1_5_2.py` | 5.068 | 0 errores, 0 advertencias | Solapa con `2.3.1.1.1`; deudas + previsiones = `pasivo_total`. |
| `2.3.1.1.5.2.1` | Deudas | `36_extract_ganancias_sociedades_p0_2_3_1_1_5_2_1.py` | 13.737 | 0 errores, 2 advertencias | Solapa con `2.3.1.1.5.2`; componentes suman `pasivo_deudas`. Advertencia: fiscal year 2022 no trae fila `TOTAL` en la fuente. |
| `2.3.1.1.5.3` | Patrimonio neto | `38_extract_ganancias_sociedades_p0_2_3_1_1_5_3.py` | 12.308 | 0 errores, 0 advertencias | Solapa con `2.3.1.1.1`; identidad de flujo patrimonial cierra. |
| `2.3.1.1.5.3.1` | Aumentos de patrimonio neto | `40_extract_ganancias_sociedades_p0_2_3_1_1_5_3_1.py` | 6.516 | 0 errores, 0 advertencias | Solapa con `2.3.1.1.5.3`; componentes suman `patrimonio_neto_aumentos`. |
| `2.3.1.1.5.3.2` | Disminuciones de patrimonio neto | `42_extract_ganancias_sociedades_p0_2_3_1_1_5_3_2.py` | 7.954 | 0 errores, 2 advertencias | Solapa con `2.3.1.1.5.3`; componentes suman `patrimonio_neto_disminuciones`. Advertencia: fiscal year 2020, actividad `267;268`, trae solo `presentaciones_total=47` y columnas de disminuciones en blanco. |

Ensamble P0 implementado:

- Script: `python3 command-files/processing-command-files/44_assemble_ganancias_sociedades_p0_long.py`.
- Salida: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p0.csv`.
- Resultado actual: 491.435 filas largas, 20 tablas fuente, fiscal years 2014-2022.
- Validacion: `python3 command-files/processing-command-files/45_validate_ganancias_sociedades_p0_long.py`, 0 errores y 0 advertencias.
- Reportes:
  - `data/output-data/validation_reports/ganancias_sociedades_p0_long_validation.md`
  - `data/output-data/validation_reports/ganancias_sociedades_p0_long_counts.csv`

Avance relativo actual dentro de P0 `2.3.1.1.*`:

- Tablas de actividad P0 inventariadas: 20.
- Tablas con extractor y validacion implementados: 20.
- Avance relativo de la fase P0 XLS directo: 100% para fiscal years 2014-2022.
- Filas largas P0 generadas y ensambladas: 491.435.

Actualizacion Fase 3 sobre P0:

- Publication years 2015-2023 / fiscal years 2014-2022 fueron incorporados al P0 principal.
- El ensamble P0 cubre ahora fiscal years 2014-2022.
- La validacion consolidada del ensamble P0 tiene 0 errores y 0 advertencias.
- Las advertencias de cuadro estan documentadas en `documentation/afip/warnings_by_period.md`; se preservan valores fuente y codigos originales sin homologacion.

### Fase 3: extension P0 completa, 2015-2023

Objetivo: extender el mismo parser XLS a publication years 2015-2020 para completar fiscal years 2014-2019.

Estado: completada para fiscal years 2014-2022.

Artefactos:

- Inventario retrospectivo: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_p0_backward_inventory.csv`.
- Validacion del inventario: `data/output-data/validation_reports/ganancias_sociedades_p0_backward_inventory_validation.md`.
- Prueba de detectores: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_p0_backward_detector_probe.csv`.
- Reporte de detectores: `data/output-data/validation_reports/ganancias_sociedades_p0_backward_detector_probe.md`.
- Bitacora metodologica de advertencias: `documentation/afip/warnings_by_period.md`.

Resultado actual:

- 112 filas inventariadas para publication years 2015-2020 / fiscal years 2014-2019.
- Validacion de inventario: 0 fallas, 17 advertencias.
- Prueba de detectores: 112 filas y 0 advertencias despues de adaptar los detectores.
- Fiscal years 2014-2022 fueron extraidos, ensamblados y validados dentro de `P0_new_xls_detail`.
- El P0 principal ahora tiene 892 filas de inventario, 20 tablas de actividad extraidas y 491.435 filas largas ensambladas para fiscal years 2014-2022.

Riesgos documentados:

- Carpetas raiz variables.
- 2015 tiene etiqueta interna inconsistente.
- Fiscal year 2014 usa 13 archivos de continuacion con sufijo `_2-` que requieren concatenacion controlada.
- Fiscal years 2014-2016 no traen siete tablas detalladas recientes del bloque `2.3.1.1.5.*`.
- Algunas variables de ventas, quebrantos, activo y patrimonio aparecen con cobertura o encabezados distintos en fiscal years 2014-2018.
- La homologacion amplia de ramas se aplica solo despues del ensamble final; los extractores preservan `activity_code`, `activity_label_original` y `activity_section_original` tal como aparecen en la fuente.

Estado posterior recomendado:

1. Usar el CSV fechado sin homologar para auditoria de fuente.
2. Usar el CSV fechado homologado para analisis por rama comun amplia.
3. Documentar antes cualquier variable derivada, deflactacion o empalme sectorial fino.

### Fase 4: extension P1, fiscal year 2013

Objetivo: incorporar publication year 2014, HTML exportado desde Excel, con clasificador nuevo.

Estado: completada.

Criterio:

- Parser HTML.
- Buscar maxima desagregacion en archivo/hoja secundaria cuando exista.
- Mantener el mismo esquema largo del P0.

Artefactos:

- Inventario P1: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p1.csv`.
- Extraccion larga P1: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p1.csv`.
- Validacion P1: `data/output-data/validation_reports/ganancias_sociedades_p1_long_validation.md`.
- Conteos P1: `data/output-data/validation_reports/ganancias_sociedades_p1_long_counts.csv`.
- Bitacora P1: `documentation/afip/warnings_by_period.md`.

Resultado actual:

- 13 cuadros de actividad inventariados.
- 37.088 filas largas extraidas.
- 127 variables canonicas observadas.
- Validacion: 0 fallas y 0 advertencias.
- Se prefirieron archivos/hojas secundarias `_2` para conservar el maximo detalle disponible.

### Fase 5: extension P2-P3, fiscal years 2008-2012

Objetivo: incorporar publication years 2009-2013, HTML exportado desde Excel, con clasificador viejo.

Criterio:

- No leer como XLS.
- Para maxima desagregacion, no usar solo `sheet001.htm`; inspeccionar `sheet002.htm` y continuaciones.
- Registrar `classifier_period = old`.

Estado P2: completado para publication year 2013 / fiscal year 2012.

Artefactos P2:

- Inventario P2: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p2.csv`.
- Extraccion larga P2: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p2.csv`.
- Validacion P2: `data/output-data/validation_reports/ganancias_sociedades_p2_long_validation.md`.
- Conteos P2: `data/output-data/validation_reports/ganancias_sociedades_p2_long_counts.csv`.
- Bitacora P2: `documentation/afip/warnings_by_period.md`.

Resultado P2:

- 13 cuadros de actividad inventariados.
- 27.208 filas largas extraidas.
- 127 variables canonicas observadas.
- Validacion: 0 fallas y 0 advertencias.
- Se uso `sheet002.htm` para conservar el maximo detalle disponible.

Estado P3: completado para publication years 2009-2012 / fiscal years 2008-2011.

Artefactos P3:

- Inventario P3: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p3.csv`.
- Extraccion larga P3: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p3.csv`.
- Validacion P3: `data/output-data/validation_reports/ganancias_sociedades_p3_long_validation.md`.
- Conteos P3: `data/output-data/validation_reports/ganancias_sociedades_p3_long_counts.csv`.
- Bitacora P3: `documentation/afip/warnings_by_period.md`.

Resultado P3:

- 49 pares anio-cuadro inventariados.
- 97.775 filas largas extraidas.
- 129 variables canonicas observadas.
- Validacion: 0 fallas y 10 advertencias estructurales.
- Unidad monetaria original: `miles_pesos_corrientes`.
- Se uso `sheet002.htm` cuando existia; tres cuadros quedaron solo en `sheet001.htm`.
- Fiscal year 2008 tiene desplazamientos de contenido respecto del `source_table_id` y tres subcuadros ausentes.

### Fase 6: extension P4, fiscal years 2002-2007

Objetivo: incorporar publication years 2003-2008, `AFIP.CAB` con XLS y numeracion moderna `2.3.*`.

Criterio:

- Extraer/inventariar CAB.
- Leer cuadros y continuaciones `_2`.
- Preservar componentes contables cuando existan.

Estado P4: completado para publication years 2003-2008 / fiscal years 2002-2007.

Artefactos P4:

- Inventario P4: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p4.csv`.
- Extraccion larga P4: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p4.csv`.
- Validacion P4: `data/output-data/validation_reports/ganancias_sociedades_p4_long_validation.md`.
- Conteos P4: `data/output-data/validation_reports/ganancias_sociedades_p4_long_counts.csv`.
- Bitacora P4: `documentation/afip/warnings_by_period.md`.

Resultado P4:

- 60 pares anio-cuadro inventariados.
- 132.088 filas largas extraidas.
- 111 variables canonicas observadas.
- Validacion: 0 fallas y 25 advertencias documentadas.
- Unidad monetaria original: `miles_pesos_corrientes`.
- Se uso `_2.xls` en todos los cuadros para conservar el maximo detalle de actividad disponible.
- La numeracion antigua mantiene resultados condensados en `2.3.1.1.2.2`, `2.3.1.1.2.3` y `2.3.1.1.2.4`; el parser los mapea a las variables canonicas de resultado bruto, otros resultados y resultado contable.
- El cuadro `2.3.1.1.2.1` usa el componente `OTROS` de costos, conservado como `costos_otros`.
- Fiscal year 2007, actividad `142. Explotacion de minas y canteras n.c.p.`, trae solo `presentaciones_total` en `2.3.1.1.2.1`; los otros valores de ese renglon estan en blanco en la fuente y no se imputan.

### Fase 7: extension P5, fiscal years 1999-2001

Objetivo: incorporar publication years 2000-2002 con numeracion antigua `3.3.*`.

Criterio:

- Resolver duplicados de fiscal years embebidos en ZIPs 2001-2002.
- Preferir una regla canonica explicita: ultima publicacion disponible para un fiscal year, salvo discrepancia documentada.
- Conservar detalle 3 digitos cuando este en continuaciones `_2`.

Estado P5: completado para publication year 2002 / fiscal years 1999-2001.

Regla canonica P5:

- Usar `estadisticasTributarias2002.zip` como publicacion canonica para fiscal years 1999-2001.
- Leer XLS dentro de `AFIP.CAB`.
- Mapear sufijos `_2000`, `_2001` y `_2002` a fiscal years 1999, 2000 y 2001 respectivamente.
- Tratar las publicaciones 2000 y 2001 como duplicados anteriores para esta fase, no como insumos combinados.

Artefactos P5:

- Inventario P5: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p5.csv`.
- Extraccion larga P5: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p5.csv`.
- Validacion P5: `data/output-data/validation_reports/ganancias_sociedades_p5_long_validation.md`.
- Conteos P5: `data/output-data/validation_reports/ganancias_sociedades_p5_long_counts.csv`.
- Bitacora P5: `documentation/afip/warnings_by_period.md`.

Resultado P5:

- 18 pares anio-cuadro inventariados.
- 31.229 filas largas extraidas.
- 114 variables canonicas observadas.
- Validacion: 0 fallas y 35 advertencias documentadas.
- Unidad monetaria original: `miles_pesos_corrientes`.
- Fiscal years 1999-2000 usan esquema compacto de cuatro cuadros.
- Fiscal year 2001 usa numeracion antigua expandida, con mas detalle patrimonial y de resultados.
- La etiqueta vieja `Actividades no bien especificadas 9/` se clasifica como `other_activity`, no como rama de 3 digitos.
- La homologacion amplia de ramas ya fue implementada despues del ensamble final.

### Fase 8: extension P6, fiscal years 1997-1998

Objetivo: incorporar la etapa mas antigua con actividad amplia.

Criterio:

- No inventar subramas.
- Cargar el maximo nivel disponible por fiscal year.
- Marcar `activity_level = broad_activity` cuando la fuente solo trae actividad amplia.
- Conservar `activity_3digit` cuando aparece observado en continuaciones `_2`.

Estado P6: completado para publication years 1998-1999 / fiscal years 1997-1998.

Artefactos P6:

- Inventario P6: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p6.csv`.
- Extraccion larga P6: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p6.csv`.
- Validacion P6: `data/output-data/validation_reports/ganancias_sociedades_p6_long_validation.md`.
- Conteos P6: `data/output-data/validation_reports/ganancias_sociedades_p6_long_counts.csv`.
- Bitacora P6: `documentation/afip/warnings_by_period.md`.

Resultado P6:

- 8 pares anio-cuadro inventariados.
- 3.044 filas largas extraidas.
- 36 variables canonicas observadas.
- Validacion: 0 fallas y 24 advertencias documentadas.
- Unidad monetaria original: `miles_pesos_corrientes`.
- Fiscal year 1997 usa numeracion `4.4.*` y solo actividad amplia.
- Fiscal year 1998 usa numeracion `3.3.*` y tiene detalle 3 digitos en archivos `_2.xls`.
- El cuadro fiscal 1997 `4.4.1.1.3` agrega variables de ajustes fiscales no observadas en fiscal 1998.
- La homologacion amplia de ramas ya fue implementada despues del ensamble final.

### Fase 9: homologacion y salidas analiticas

Objetivo: construir una base larga completa, homologar ramas y publicar una
salida tidy compartible por GitHub.

Estado: completada.

Productos generados:

```text
data/analysis-data/2026-05-31_afip_ganancias_sociedades_tidy_homologado.csv.gz
data/intermediate-data/afip-estadisticas-tributarias/2026-05-31_afip_ganancias_sociedades_source_dictionary.csv
data/intermediate-data/afip-estadisticas-tributarias/2026-05-31_afip_ganancias_sociedades_activity_dictionary.csv
data/intermediate-data/afip-estadisticas-tributarias/2026-05-31_afip_ganancias_sociedades_ramas_homologacion_diccionario.csv
```

El panel tidy conserva maxima desagregacion original mediante llaves
`source_key` y `activity_key`, mas codigos analiticos de actividad y rama. Las
etiquetas largas, rutas fuente y notas viven en diccionarios intermedios
regenerables.

Validacion:

- Script: `python3 command-files/processing-command-files/68_validate_ganancias_sociedades_tidy_outputs.py`.
- Resultado: 0 fallas, 0 advertencias.
- Filas del panel final: 819.867.
- Tamano del panel final: 11.758.387 bytes.
- Cobertura fiscal: 1997-2022.
- Entradas de diccionario de fuente: 320.
- Entradas de diccionario de actividad/ramas: 569.

### Fase 10: variables derivadas y analisis R

Variables derivadas candidatas:

- margen de ganancia neta imponible sobre ventas.
- tasa de impuesto determinado sobre ganancia neta imponible.
- resultado contable neto sobre activo.
- resultado contable neto sobre patrimonio neto.
- estructura de activos, pasivos y patrimonio cuando el detalle exista.

No calcular derivados definitivos sin documentar tratamiento de ceros, negativos, faltantes, cambios legales y clasificador sectorial.

## 14. Punto De Partida Para El Siguiente Prompt

La Fase P0 XLS directo quedo cerrada para publication years 2015-2023 / fiscal years 2014-2022.
La Fase P1 HTML nuevo quedo cerrada para publication year 2014 / fiscal year 2013.
La Fase P2 HTML viejo en millones quedo cerrada para publication year 2013 / fiscal year 2012.
La Fase P3 HTML viejo en miles quedo cerrada para publication years 2009-2012 / fiscal years 2008-2011.
La Fase P4 CAB/XLS viejo en miles quedo cerrada para publication years 2003-2008 / fiscal years 2002-2007.
La Fase P5 CAB/XLS viejo con numeracion `3.3.*` quedo cerrada para publication year 2002 / fiscal years 1999-2001.
La Fase P6 XLS directo antiguo quedo cerrada para publication years 1998-1999 / fiscal years 1997-1998.

El ensamble validado P0 cubre fiscal years 2014-2022 con 491.435 filas y 20 cuadros fuente.
La extraccion validada P1 cubre fiscal year 2013 con 37.088 filas y 13 cuadros fuente.
La extraccion validada P2 cubre fiscal year 2012 con 27.208 filas y 13 cuadros fuente.
La extraccion validada P3 cubre fiscal years 2008-2011 con 97.775 filas y 49 pares anio-cuadro.
La extraccion validada P4 cubre fiscal years 2002-2007 con 132.088 filas y 60 pares anio-cuadro.
La extraccion validada P5 cubre fiscal years 1999-2001 con 31.229 filas y 18 pares anio-cuadro.
La extraccion validada P6 cubre fiscal years 1997-1998 con 3.044 filas y 8 pares anio-cuadro.

El flujo reproducible actual cubre fiscal years 1997-2022 con 819.867 filas intermedias validadas entre P0-P6.
Los CSV intermedios AFIP canonicos viven en `data/intermediate-data/afip-estadisticas-tributarias/`; los CSV AFIP antiguos que estaban directamente bajo `data/intermediate-data/` fueron eliminados por ser duplicados obsoletos y regenerables.

La salida final fechada ya esta creada:

- `data/analysis-data/2026-05-31_afip_ganancias_sociedades_tidy_homologado.csv.gz`.
- `data/intermediate-data/afip-estadisticas-tributarias/2026-05-31_afip_ganancias_sociedades_source_dictionary.csv`.
- `data/intermediate-data/afip-estadisticas-tributarias/2026-05-31_afip_ganancias_sociedades_activity_dictionary.csv`.
- `data/intermediate-data/afip-estadisticas-tributarias/2026-05-31_afip_ganancias_sociedades_ramas_homologacion_diccionario.csv`.

El siguiente paso recomendado es iniciar analisis R o decidir una homologacion fina de actividades de 3 digitos entre clasificador viejo y nuevo:

- Usar `documentation/afip/warnings_by_period.md` como guia consolidada de discontinuidades y notas estructurales P0-P6.
- Usar `documentation/afip/branch_harmonization.md` como guia de ramas comunes.
- Mantener el criterio de no imputar desde cuadros agregados cuando una tabla detallada trae celdas en blanco.

Evitar supuestos metodologicos sobre empalmes, deflactacion, correspondencias sectoriales finas o variables derivadas finales. La homologacion amplia actual no resuelve equivalencias directas de actividades de 3 digitos entre clasificadores.
