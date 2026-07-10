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

- El panel final para analisis se guarda en:

```text
data/analysis-data/
```

- Los ZIP crudos quedaron versionables en Git. La salida final se publica como
  CSV tidy sin comprimir y queda por debajo del limite normal de GitHub.

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

- Panel analitico homologado: `data/analysis-data/20260710_afip_ganancias_sociedades_tidy_homologado.csv`.
- Filas del panel: 341.103.
- Tamano sin comprimir validado: 81.500.612 bytes.
- Diccionario de fuente: `data/intermediate-data/afip-estadisticas-tributarias/20260710_afip_ganancias_sociedades_source_dictionary.csv`.
- Diccionario de actividad: `data/intermediate-data/afip-estadisticas-tributarias/20260710_afip_ganancias_sociedades_activity_dictionary.csv`.
- Diccionario de variable: `data/intermediate-data/afip-estadisticas-tributarias/20260710_afip_ganancias_sociedades_variable_dictionary.csv`.
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

Columnas agregadas al panel o a sus diccionarios:

- `rama_comun_*`: rama amplia comparable para toda la serie 1997-2022.
- `rama_detalle_homologada_*`: detalle fuente preservado con codigos namespaced
  por clasificador.

Decision metodologica:

- La rama comun es amplia porque fiscal year 1997 solo trae actividad amplia.
- Los codigos de 3 digitos de clasificador viejo y nuevo no se tratan como
  equivalentes directos.
- La homologacion fina entre actividades de 3 digitos queda como etapa
  metodologica posterior.
- El panel analitico conserva la rama original en `rama_original_codigo`,
  `rama_original_nombre`, `rama_original_nivel` y `clasificador_actividad`.
  La columna `rama_homologada_codigo` solo agrega una capa comparable de rama
  amplia.

Criterio operativo:

- Para el clasificador nuevo, la rama homologada se asigna desde la letra de
  seccion original (`A`, `B`, `C`, etc.) observada en la actividad o en la
  seccion fuente.
- Para el clasificador viejo, la rama homologada se asigna desde la letra de
  seccion original del clasificador viejo. Las letras no se interpretan como
  equivalentes directas al clasificador nuevo; se mapean hacia ramas amplias.
- Para fiscal year 1997 y otras filas de actividad amplia, la homologacion usa
  la etiqueta/codigo amplio publicado por la fuente.
- Las actividades residuales o no especificadas se agrupan en
  `OTRAS_NO_ESPECIFICADAS`.
- Las filas `TOTAL` existen como categoria de control en la homologacion, pero
  se excluyen del panel final de analisis para no mezclar agregados con ramas
  economicas.

Ramas comunes:

| `rama_comun_codigo` | Clasificador nuevo | Clasificador viejo | Actividad amplia/P6 |
|---|---|---|---|
| `AGRICULTURA_PESCA` | A | A+B | Agricultura, caza, silvicultura y pesca |
| `MINAS_CANTERAS` | B | C | Explotacion de minas y canteras |
| `INDUSTRIA_MANUFACTURERA` | C | D | Industrias manufactureras |
| `ELECTRICIDAD_GAS_AGUA` | D+E | E | Electricidad, gas y agua |
| `CONSTRUCCION` | F | F | Construccion |
| `COMERCIO_HOTELES_RESTAURANTES` | G+I | G+H | Comercio, restaurantes y hoteles |
| `TRANSPORTE_COMUNICACIONES` | H+J | I | Transporte, almacenamiento y comunicaciones |
| `FINANZAS_INMUEBLES_SERVICIOS_EMPRESARIALES` | K+L+M+N | J+K | Finanzas, seguros, inmuebles y servicios empresariales |
| `SERVICIOS_SOCIALES_PERSONALES_PUBLICOS` | O+P+Q+R+S | L+M+N+O | Servicios comunales, sociales y personales |
| `OTRAS_NO_ESPECIFICADAS` | Otras/no especificadas | Otras/no especificadas | Actividades no bien especificadas |
| `TOTAL` | Total fuente | Total fuente | Total fuente |

El criterio completo esta documentado en:

```text
documentation/afip/branch_harmonization.md
```

## 4. Estructura Del Panel Resultante

Orden fisico de los datos:

1. El ensamble final lee los extractos validados P0-P6.
2. El orden operativo va desde el periodo mas reciente hacia atras:
   P0, P1, P2, P3, P4, P5 y P6.
3. Dentro de cada periodo se conserva el orden producido por los extractores:
   fuente, cuadro, dimension y variable.
4. El panel final queda como CSV sin comprimir con columnas analiticas directas:
   anio fiscal, rama original, rama homologada, variable economica y valor.
5. Para analisis no debe dependerse del orden fisico del CSV; usar
   identificadores canonicos.

Identificadores recomendados:

- `fiscal_year`
- `rama_original_codigo`
- `rama_original_nivel`
- `clasificador_actividad`
- `variable_grupo`
- `variable_nombre`

### Libro De Codigos Del Panel Final

Archivo:

```text
data/analysis-data/20260710_afip_ganancias_sociedades_tidy_homologado.csv
```

El panel final de `analysis-data` excluye metadatos tecnicos de extraccion y
conserva solo campos directamente utiles para analisis estadistico. Esta en
formato largo: cada fila representa una observacion monetaria para una rama de
actividad y una variable economica en un anio fiscal.

Unidad de observacion:

```text
fiscal_year x rama_original_codigo x rama_original_nivel x clasificador_actividad x variable_grupo x variable_nombre
```

Uso recomendado:

- Usar `fiscal_year` como eje temporal del analisis.
- Usar `rama_original_*` cuando se quiera trabajar con el maximo detalle
  sectorial disponible en cada anio.
- Usar `rama_homologada_*` cuando se quiera comparar ramas amplias a lo largo
  de toda la serie 1997-2022.
- Usar siempre `variable_grupo` junto con `variable_nombre`; algunos nombres de
  variable aparecen en mas de un contexto economico.
- Usar `valor_pesos_corrientes` como valor monetario principal. La serie esta
  expresada en pesos corrientes; cualquier deflactacion debe hacerse en una
  etapa posterior.
- No sumar automaticamente niveles distintos de `rama_original_nivel`, porque
  secciones, actividades de 3 digitos y actividades amplias no tienen el mismo
  nivel de agregacion.

| Columna | Descripcion |
|---|---|
| `fiscal_year` | Anio fiscal informado por la fuente. Es el identificador temporal principal. |
| `rama_original_codigo` | Codigo original de actividad economica observado en AFIP/ARCA. Puede ser codigo de actividad, seccion, rama amplia o residual. |
| `rama_original_nombre` | Etiqueta original de actividad economica publicada por la fuente. |
| `rama_original_nivel` | Nivel de desagregacion de la rama original: `activity_3digit`, `broad_activity`, `section` u `other_activity`. Permite distinguir detalle fino de agregados amplios. |
| `clasificador_actividad` | Clasificador de actividad de origen: `new` u `old`. No debe asumirse equivalencia directa entre codigos de 3 digitos de ambos clasificadores. |
| `rama_homologada_codigo` | Rama amplia comparable para toda la serie 1997-2022. Es la variable recomendada para analisis historico de largo plazo por grandes ramas. |
| `rama_homologada_nombre` | Etiqueta legible de la rama amplia homologada. |
| `variable_grupo` | Bloque economico al que pertenece la variable, por ejemplo ventas/costos, gastos operativos, activo, pasivo, patrimonio, resultado impositivo o determinacion del impuesto. |
| `variable_nombre` | Nombre canonico de la variable monetaria. Debe interpretarse junto con `variable_grupo` cuando haya componentes repetidos en distintos cuadros. |
| `valor_pesos_corrientes` | Valor monetario normalizado a pesos corrientes. No esta deflactado ni expresado en moneda constante. |

Decisiones de empaquetado:

- Se excluyen variables de conteo/casos y `presentaciones_*`.
- Se excluyen filas `TOTAL` para evitar mezclar agregados con ramas.
- Se conserva el maximo detalle sectorial disponible por cuadro y anio.
- Cuando un mismo `variable_nombre` aparece en contextos economicos distintos,
  `variable_grupo` diferencia la observacion analitica.
- Las filas `other_activity` agrupan actividades residuales o no especificadas
  de la fuente y se homologan como `OTRAS_NO_ESPECIFICADAS`.
- La homologacion de ramas es amplia; no resuelve una correspondencia fina de
  actividades a 3 digitos entre clasificadores viejo y nuevo.

Columnas del diccionario de fuente:

| Columna | Descripcion |
|---|---|
| `source_key` | Llave usada en el panel tidy. |
| `publication_year` | Anio de publicacion. |
| `fiscal_year` | Anio fiscal. |
| `period_id` | Epoca estructural. |
| `archive_filename` | Nombre del ZIP anual de origen. |
| `source_table_id` | Identificador del cuadro fuente. |
| `source_table_path` | Ruta interna dentro del ZIP/CAB/HTML. |
| `source_table_title` | Titulo original del cuadro. |
| `table_family` | Familia canonica del cuadro. |
| `universe` | Universo del cuadro. |
| `dimension_type` | Tipo de dimension. |
| `source_note` | Nota de fuente o decision de mapeo. |
| `header_start_row_zero_based` | Fila inicial del encabezado detectado. |
| `data_start_row_zero_based` | Fila inicial de datos detectada. |
| `row_count` | Filas del panel asociadas a la fuente. |

Columnas del diccionario de actividad:

| Columna | Descripcion |
|---|---|
| `activity_key` | Llave usada en el panel tidy. |
| `rama_homologacion_version` | Version de la regla de homologacion. |
| `classifier_period` | Clasificador de actividad. |
| `activity_level` | Nivel de actividad. |
| `activity_code` | Codigo de actividad. |
| `activity_label_original` | Etiqueta original. |
| `activity_section_original` | Seccion original. |
| `rama_homologacion_estado` | Estado de mapeo. |
| `rama_comun_codigo` | Codigo de rama amplia comparable. |
| `rama_comun_label` | Etiqueta de rama amplia comparable. |
| `rama_comun_nivel` | Nivel de la rama comun. |
| `rama_detalle_homologada_codigo` | Codigo de detalle preservado. |
| `rama_detalle_homologada_label` | Etiqueta de detalle preservada. |
| `rama_detalle_homologada_nivel` | Nivel del detalle preservado. |
| `rama_homologacion_nota` | Nota de homologacion. |
| `fiscal_year_min` | Primer anio fiscal observado para esa clave. |
| `fiscal_year_max` | Ultimo anio fiscal observado para esa clave. |
| `row_count` | Filas del panel asociadas a la actividad. |

Columnas del diccionario de variable:

| Columna | Descripcion |
|---|---|
| `variable_key` | Llave usada en el panel tidy. |
| `variable_name` | Nombre canonico de la variable estadistica. |
| `unit_original` | Unidad original observada, por ejemplo casos, miles o millones de pesos corrientes. |
| `row_count` | Filas del panel asociadas a la variable. |

## 5. Archivos De Referencia

- Diseno ETL: `documentation/afip/etl_design.md`.
- Plan de trabajo: `documentation/afip/work_plan.md`.
- Comparabilidad de variables: `documentation/afip/variable_comparability.md`.
- Homologacion de ramas: `documentation/afip/branch_harmonization.md`.
- Advertencias por periodo: `documentation/afip/warnings_by_period.md`.
