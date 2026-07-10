# Minuta Del Procedimiento AFIP/ARCA

Esta minuta resume el procedimiento aplicado a la fuente AFIP/ARCA para
sistematizar el capitulo `Impuesto a las Ganancias Sociedades` del anuario de
estadisticas tributarias.

## 1. Descarga Y Organizacion De Datos Crudos

Fuente de partida:

```text
https://www.afip.gob.ar/institucional/estudios/anuario-estadisticas-tributarias/
```

Cobertura de publicacion:

```text
1998-2023
```

Procedimiento:

- Se descargaron 26 archivos ZIP anuales, uno por publication year.
- Los ZIP originales se guardaron sin edicion manual en:

```text
data/input-data/raw/afip-estadisticas-tributarias/
```

- Los datos crudos se tratan como insumos de solo lectura.
- Las salidas transitorias del pipeline se guardan en:

```text
data/intermediate-data/afip-estadisticas-tributarias/
```

- Las salidas finales para analisis se guardan en:

```text
data/analysis-data/
```

- Los ZIP crudos quedaron versionables en Git. Los CSV finales de analisis
  quedan ignorados por `.gitignore` porque superan el limite normal de GitHub
  para blobs, pero son regenerables con el pipeline completo.

Validacion basica:

- Los ZIP fueron inspeccionados e inventariados.
- La estructura general de archivos, formatos y periodos esta documentada en
  `documentation/afip/archive_inventory.md` y
  `documentation/afip/structural_mapping.yml`.

## 2. Sistematizacion De Ganancias Sociedades

Capitulo sistematizado:

```text
Impuesto a las Ganancias Sociedades
```

Cobertura fiscal resultante:

```text
1997-2022
```

Formato del panel:

```text
largo
```

Unidad fisica de fila:

```text
celda estadistica normalizada
```

La clave conceptual de fila es:

```text
publication_year x fiscal_year x source_table_id x dimension_type x dimension_value x variable_name
```

El pipeline se desarrollo por epocas estructurales porque la fuente no mantiene
un formato unico a lo largo del tiempo.

| Periodo | Publication years | Fiscal years | Formato | Clasificador / detalle | Unidad monetaria original |
|---|---:|---:|---|---|---|
| `P0_new_xls_detail` | 2015-2023 | 2014-2022 | XLS directo | Clasificador nuevo; seccion y actividad 3 digitos | Millones de pesos corrientes |
| `P1_new_html_detail` | 2014 | 2013 | HTML exportado desde Excel | Clasificador nuevo; detalle en archivo/hoja secundaria | Millones de pesos corrientes |
| `P2_old_html_detail_millions` | 2013 | 2012 | HTML exportado desde Excel | Clasificador viejo; detalle 3 digitos | Millones de pesos corrientes |
| `P3_old_html_detail_thousands` | 2009-2012 | 2008-2011 | HTML exportado desde Excel | Clasificador viejo; detalle en `sheet002.htm` cuando existe | Miles de pesos corrientes |
| `P4_old_cab_xls_detail_thousands` | 2003-2008 | 2002-2007 | XLS dentro de `AFIP.CAB` | Clasificador viejo; continuaciones `_2.xls` | Miles de pesos corrientes |
| `P5_old_cab_xls_detail_legacy_numbering` | 2002 canonico | 1999-2001 | XLS dentro de `AFIP.CAB` | Clasificador viejo; numeracion `3.3.*` | Miles de pesos corrientes |
| `P6_legacy_broad_activity` | 1998-1999 | 1997-1998 | XLS directo antiguo | Fiscal 1997 amplio; fiscal 1998 con detalle 3 digitos | Miles de pesos corrientes |

Cada periodo tiene scripts de inventario, extraccion y validacion propios en:

```text
command-files/processing-command-files/
```

El flujo reproducible completo se ejecuta con:

```bash
python3 command-files/run_all.py
```

Resultado final validado:

- CSV sin homologar: `data/analysis-data/2026-05-31_afip_ganancias_sociedades_long_sin_homologar.csv`.
- CSV homologado: `data/analysis-data/2026-05-31_afip_ganancias_sociedades_long_homologada.csv`.
- Filas en cada CSV final: 819.867.
- Validacion final: 0 fallas.

## 3. Homologacion De Ramas Economicas

La homologacion se implementa como capa posterior al ensamble completo. No
reemplaza ni elimina los campos originales de actividad.

Columnas fuente preservadas:

- `activity_level`
- `activity_code`
- `activity_label_original`
- `activity_section_original`
- `classifier_period`

Columnas agregadas:

- `rama_comun_*`: rama amplia comparable para toda la serie 1997-2022.
- `rama_detalle_homologada_*`: detalle fuente preservado con codigos namespaced
  por clasificador.

Decision metodologica:

- La rama comun es amplia porque fiscal year 1997 solo trae actividad amplia.
- Los codigos de 3 digitos de clasificador viejo y nuevo no se tratan como
  equivalentes directos.
- La homologacion fina entre actividades de 3 digitos queda como etapa
  metodologica posterior.

Ramas comunes:

| `rama_comun_codigo` | Criterio de agrupacion |
|---|---|
| `AGRICULTURA_PESCA` | Agricultura, ganaderia, caza, silvicultura y pesca |
| `MINAS_CANTERAS` | Explotacion de minas y canteras |
| `INDUSTRIA_MANUFACTURERA` | Industria manufacturera |
| `ELECTRICIDAD_GAS_AGUA` | Electricidad, gas, agua y saneamiento |
| `CONSTRUCCION` | Construccion |
| `COMERCIO_HOTELES_RESTAURANTES` | Comercio, hoteles y restaurantes |
| `TRANSPORTE_COMUNICACIONES` | Transporte, almacenamiento y comunicaciones |
| `FINANZAS_INMUEBLES_SERVICIOS_EMPRESARIALES` | Finanzas, seguros, inmuebles y servicios empresariales |
| `SERVICIOS_SOCIALES_PERSONALES_PUBLICOS` | Administracion publica, ensenanza, salud y otros servicios |
| `OTRAS_NO_ESPECIFICADAS` | Otras actividades o actividades no especificadas |
| `TOTAL` | Total fuente |

El criterio completo esta documentado en:

```text
documentation/afip/branch_harmonization.md
```

## 4. Estructura Del Panel Resultante

Orden fisico de los datos:

1. El ensamble final concatena los extractos validados P0-P6.
2. El orden operativo va desde el periodo mas reciente hacia atras:
   P0, P1, P2, P3, P4, P5 y P6.
3. Dentro de cada periodo se conserva el orden producido por los extractores:
   fuente, cuadro, dimension y variable.
4. Para analisis no debe dependerse del orden fisico del CSV; usar
   identificadores canonicos.

Identificadores recomendados:

- `publication_year`
- `fiscal_year`
- `source_table_id`
- `dimension_type`
- `dimension_value`
- `variable_name`

Diccionario de columnas:

| Columna | Descripcion |
|---|---|
| `publication_year` | Anio de publicacion del anuario o ZIP fuente. |
| `fiscal_year` | Anio fiscal informado en el cuadro. |
| `archive_filename` | Nombre del ZIP anual de origen. |
| `period_id` | Epoca estructural asignada por el pipeline. |
| `source_table_id` | Identificador original del cuadro fuente. |
| `source_table_path` | Ruta interna del archivo o tabla dentro del ZIP/CAB/HTML. |
| `source_table_title` | Titulo original del cuadro fuente. |
| `table_family` | Familia canonica del cuadro dentro del capitulo. |
| `universe` | Universo del cuadro, actualmente Ganancias Sociedades. |
| `dimension_type` | Tipo de dimension; para esta base principal, actividad economica. |
| `dimension_value` | Codigo canonico de la dimension dentro del cuadro. |
| `activity_level` | Nivel de actividad: total, seccion, actividad 3 digitos, amplia u otras. |
| `activity_code` | Codigo de actividad extraido o normalizado desde la fuente. |
| `activity_label_original` | Etiqueta original de actividad. |
| `activity_section_original` | Seccion original de actividad cuando existe. |
| `classifier_period` | Clasificador de actividad: `new` u `old`. |
| `variable_name` | Nombre canonico de la variable estadistica. |
| `value` | Valor normalizado como texto/decimal segun fuente. |
| `unit_original` | Unidad original observada, por ejemplo casos, miles o millones de pesos corrientes. |
| `value_pesos_current` | Monto monetario convertido a pesos corrientes cuando aplica. |
| `source_note` | Nota de fuente o decision de mapeo especifica de la fila. |
| `header_start_row_zero_based` | Fila inicial del encabezado detectado, base cero. |
| `data_start_row_zero_based` | Fila inicial de datos detectada, base cero. |
| `source_row_zero_based` | Fila fuente de la celda extraida, base cero. |
| `source_column_zero_based` | Columna fuente de la celda extraida, base cero. |
| `rama_homologacion_version` | Version de la regla de homologacion de ramas. |
| `rama_homologacion_estado` | Estado de mapeo: `mapped`, `source_other` o `source_total`. |
| `rama_comun_codigo` | Codigo de rama amplia comparable en toda la serie. |
| `rama_comun_label` | Etiqueta de rama amplia comparable. |
| `rama_comun_nivel` | Nivel de la rama comun. |
| `rama_detalle_homologada_codigo` | Codigo de detalle preservado con namespace por clasificador. |
| `rama_detalle_homologada_label` | Etiqueta de detalle preservada. |
| `rama_detalle_homologada_nivel` | Nivel del detalle homologado/preservado. |
| `rama_homologacion_nota` | Nota sobre la regla usada para homologar la rama. |

## 5. Archivos De Referencia

- Diseno ETL: `documentation/afip/etl_design.md`.
- Plan de trabajo: `documentation/afip/work_plan.md`.
- Comparabilidad de variables: `documentation/afip/variable_comparability.md`.
- Homologacion de ramas: `documentation/afip/branch_harmonization.md`.
- Advertencias por periodo: `documentation/afip/warnings_by_period.md`.
