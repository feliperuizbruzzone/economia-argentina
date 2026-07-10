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

### Grupos De Variables Disponibles

La columna `variable_grupo` identifica el bloque economico del cuadro fuente.
Debe usarse para interpretar correctamente `variable_nombre`, especialmente
cuando una misma variable aparece en mas de un contexto contable.

| `variable_grupo` | Descripcion | Variables distintas |
|---|---|---:|
| `determinacion_impuesto` | Determinacion del impuesto por actividad economica. | 6 |
| `estado_resultados_compacto` | Estado de resultados publicado en formato compacto en los anos antiguos. | 6 |
| `estado_resultados_gastos_operativos_detalle` | Detalle de gastos operativos del estado de resultados. | 7 |
| `estado_resultados_gastos_vinculados_al_costo` | Detalle de gastos vinculados al costo del estado de resultados. | 11 |
| `estado_resultados_resultado_bruto_gastos_operativos` | Resultado bruto, venta de acciones, deudores incobrables y gastos operativos. | 6 |
| `estado_resultados_resultado_contable` | Resultados extraordinarios, impuesto a las ganancias y resultado contable. | 6 |
| `estado_resultados_resultados_financieros_otros` | Inversiones permanentes, resultados financieros, derivados y otros ingresos/egresos. | 8 |
| `estado_resultados_ventas_costos` | Ventas, costos, compras, existencias y gastos de produccion. | 8 |
| `estado_resultados_ventas_exportaciones` | Ventas locales/exentas, exportaciones y derechos de exportacion. | 10 |
| `resultado_impositivo` | Determinacion del resultado impositivo. | 11 |
| `resumen_ventas_ganancia_impuesto` | Resumen de ventas, ganancia neta imponible e impuesto determinado. | 2 |
| `situacion_patrimonial_activo` | Componentes generales del activo. | 8 |
| `situacion_patrimonial_activo_bienes_cambio` | Detalle de bienes de cambio del activo. | 6 |
| `situacion_patrimonial_activo_bienes_uso` | Detalle de bienes de uso del activo. | 5 |
| `situacion_patrimonial_activo_creditos` | Detalle de creditos del activo. | 6 |
| `situacion_patrimonial_activo_disponibilidades` | Detalle de disponibilidades del activo. | 12 |
| `situacion_patrimonial_compacto` | Situacion patrimonial publicada en formato compacto en los anos antiguos. | 4 |
| `situacion_patrimonial_pasivo` | Componentes generales del pasivo. | 3 |
| `situacion_patrimonial_pasivo_deudas` | Detalle de deudas del pasivo. | 11 |
| `situacion_patrimonial_patrimonio_aumentos` | Detalle de aumentos del patrimonio neto. | 15 |
| `situacion_patrimonial_patrimonio_disminuciones` | Detalle de disminuciones del patrimonio neto. | 5 |

### Variables Disponibles Por Grupo

| `variable_grupo` | `variable_nombre` |
|---|---|
| `determinacion_impuesto` | `resultado_atribuible_socios_perdida` |
| `determinacion_impuesto` | `resultado_atribuible_socios_utilidad` |
| `determinacion_impuesto` | `resultado_neto_final_perdida` |
| `determinacion_impuesto` | `resultado_neto_final_utilidad` |
| `determinacion_impuesto` | `resultado_neto_perdida` |
| `determinacion_impuesto` | `resultado_neto_utilidad` |
| `estado_resultados_compacto` | `costos_total` |
| `estado_resultados_compacto` | `resultado_bruto_perdida` |
| `estado_resultados_compacto` | `resultado_bruto_utilidad` |
| `estado_resultados_compacto` | `resultado_contable_perdida` |
| `estado_resultados_compacto` | `resultado_contable_utilidad` |
| `estado_resultados_compacto` | `ventas_bienes_servicios_locaciones_netas` |
| `estado_resultados_gastos_operativos_detalle` | `depreciacion_bienes_uso` |
| `estado_resultados_gastos_operativos_detalle` | `gastos_operativos` |
| `estado_resultados_gastos_operativos_detalle` | `gastos_representacion` |
| `estado_resultados_gastos_operativos_detalle` | `honorarios_directores` |
| `estado_resultados_gastos_operativos_detalle` | `honorarios_retribuciones_servicios` |
| `estado_resultados_gastos_operativos_detalle` | `otros_gastos_operativos` |
| `estado_resultados_gastos_operativos_detalle` | `sueldos_aguinaldos_gratificaciones_contribuciones_social` |
| `estado_resultados_gastos_vinculados_al_costo` | `compras_netas` |
| `estado_resultados_gastos_vinculados_al_costo` | `costos_total` |
| `estado_resultados_gastos_vinculados_al_costo` | `depreciacion_bienes_uso` |
| `estado_resultados_gastos_vinculados_al_costo` | `existencia_final` |
| `estado_resultados_gastos_vinculados_al_costo` | `existencia_inicial` |
| `estado_resultados_gastos_vinculados_al_costo` | `gastos_produccion` |
| `estado_resultados_gastos_vinculados_al_costo` | `gastos_vinculados_al_costo` |
| `estado_resultados_gastos_vinculados_al_costo` | `honorarios_retribuciones_servicios` |
| `estado_resultados_gastos_vinculados_al_costo` | `otros_gastos_vinculados_al_costo` |
| `estado_resultados_gastos_vinculados_al_costo` | `sueldos_aguinaldos_gratificaciones_contribuciones_social` |
| `estado_resultados_gastos_vinculados_al_costo` | `ventas_bienes_servicios_locaciones_netas` |
| `estado_resultados_resultado_bruto_gastos_operativos` | `cargo_deudores_incobrables` |
| `estado_resultados_resultado_bruto_gastos_operativos` | `gastos_operativos` |
| `estado_resultados_resultado_bruto_gastos_operativos` | `resultado_bruto_perdida` |
| `estado_resultados_resultado_bruto_gastos_operativos` | `resultado_bruto_utilidad` |
| `estado_resultados_resultado_bruto_gastos_operativos` | `resultado_venta_acciones_perdida` |
| `estado_resultados_resultado_bruto_gastos_operativos` | `resultado_venta_acciones_utilidad` |
| `estado_resultados_resultado_contable` | `impuesto_ganancias` |
| `estado_resultados_resultado_contable` | `resultado_contable_perdida` |
| `estado_resultados_resultado_contable` | `resultado_contable_utilidad` |
| `estado_resultados_resultado_contable` | `resultado_final_contable_juegos_azar_apuestas` |
| `estado_resultados_resultado_contable` | `resultados_extraordinarios_quebranto` |
| `estado_resultados_resultado_contable` | `resultados_extraordinarios_utilidad` |
| `estado_resultados_resultados_financieros_otros` | `otros_ingresos_egresos_quebranto` |
| `estado_resultados_resultados_financieros_otros` | `otros_ingresos_egresos_utilidad` |
| `estado_resultados_resultados_financieros_otros` | `resultado_inversiones_permanentes_quebranto` |
| `estado_resultados_resultados_financieros_otros` | `resultado_inversiones_permanentes_utilidad` |
| `estado_resultados_resultados_financieros_otros` | `resultados_contratos_derivados_quebranto` |
| `estado_resultados_resultados_financieros_otros` | `resultados_contratos_derivados_utilidad` |
| `estado_resultados_resultados_financieros_otros` | `resultados_financieros_quebranto` |
| `estado_resultados_resultados_financieros_otros` | `resultados_financieros_utilidad` |
| `estado_resultados_ventas_costos` | `compras_netas` |
| `estado_resultados_ventas_costos` | `costos_otros` |
| `estado_resultados_ventas_costos` | `costos_total` |
| `estado_resultados_ventas_costos` | `existencia_final` |
| `estado_resultados_ventas_costos` | `existencia_inicial` |
| `estado_resultados_ventas_costos` | `gastos_produccion` |
| `estado_resultados_ventas_costos` | `gastos_vinculados_al_costo` |
| `estado_resultados_ventas_costos` | `ventas_bienes_servicios_locaciones_netas` |
| `estado_resultados_ventas_exportaciones` | `derechos_exportacion` |
| `estado_resultados_ventas_exportaciones` | `exportaciones_baja_nula_imposicion_sin_detraer_derechos` |
| `estado_resultados_ventas_exportaciones` | `exportaciones_exentas` |
| `estado_resultados_ventas_exportaciones` | `exportaciones_vinculados_sin_detraer_derechos_excluye_baja_nula` |
| `estado_resultados_ventas_exportaciones` | `otras_exportaciones_sin_detraer_derechos` |
| `estado_resultados_ventas_exportaciones` | `otras_ventas_gravadas_mercado_local` |
| `estado_resultados_ventas_exportaciones` | `total_ventas_servicios_locaciones_ejercicio` |
| `estado_resultados_ventas_exportaciones` | `ventas_bienes_servicios_locaciones_netas` |
| `estado_resultados_ventas_exportaciones` | `ventas_exentas_mercado_local` |
| `estado_resultados_ventas_exportaciones` | `ventas_gravadas_mercado_local_sujetos_vinculados` |
| `resultado_impositivo` | `ajustes_impositivos_aumentan_utilidad_disminuyen_perdida` |
| `resultado_impositivo` | `ajustes_impositivos_disminuyen_utilidad_aumentan_perdida` |
| `resultado_impositivo` | `ajustes_reexpresion_moneda_constante_negativo` |
| `resultado_impositivo` | `ajustes_reexpresion_moneda_constante_positivo` |
| `resultado_impositivo` | `importes_aumentan_utilidad_o_disminuyen_perdida` |
| `resultado_impositivo` | `importes_disminuyen_utilidad_o_aumentan_perdida` |
| `resultado_impositivo` | `quebranto_computable` |
| `resultado_impositivo` | `resultado_fines_fiscales_sin_reexpresar_perdida` |
| `resultado_impositivo` | `resultado_fines_fiscales_sin_reexpresar_utilidad` |
| `resultado_impositivo` | `resultado_impositivo_perdida` |
| `resultado_impositivo` | `resultado_impositivo_utilidad` |
| `resumen_ventas_ganancia_impuesto` | `ganancia_neta_imponible` |
| `resumen_ventas_ganancia_impuesto` | `impuesto_determinado` |
| `situacion_patrimonial_activo` | `activo_bienes_cambio` |
| `situacion_patrimonial_activo` | `activo_bienes_intangibles` |
| `situacion_patrimonial_activo` | `activo_bienes_uso` |
| `situacion_patrimonial_activo` | `activo_creditos` |
| `situacion_patrimonial_activo` | `activo_disponibilidades` |
| `situacion_patrimonial_activo` | `activo_inversiones` |
| `situacion_patrimonial_activo` | `activo_obras_construccion` |
| `situacion_patrimonial_activo` | `activo_total` |
| `situacion_patrimonial_activo_bienes_cambio` | `activo_bienes_cambio` |
| `situacion_patrimonial_activo_bienes_cambio` | `activo_bienes_cambio_materias_primas` |
| `situacion_patrimonial_activo_bienes_cambio` | `activo_bienes_cambio_mercaderias` |
| `situacion_patrimonial_activo_bienes_cambio` | `activo_bienes_cambio_otros` |
| `situacion_patrimonial_activo_bienes_cambio` | `activo_bienes_cambio_productos_en_proceso` |
| `situacion_patrimonial_activo_bienes_cambio` | `activo_bienes_cambio_productos_terminados` |
| `situacion_patrimonial_activo_bienes_uso` | `activo_bienes_uso` |
| `situacion_patrimonial_activo_bienes_uso` | `activo_bienes_uso_inmuebles` |
| `situacion_patrimonial_activo_bienes_uso` | `activo_bienes_uso_instalaciones` |
| `situacion_patrimonial_activo_bienes_uso` | `activo_bienes_uso_otros` |
| `situacion_patrimonial_activo_bienes_uso` | `activo_bienes_uso_rodados` |
| `situacion_patrimonial_activo_creditos` | `activo_creditos` |
| `situacion_patrimonial_activo_creditos` | `activo_creditos_cuentas_particulares_socios` |
| `situacion_patrimonial_activo_creditos` | `activo_creditos_deudores_ventas_servicios` |
| `situacion_patrimonial_activo_creditos` | `activo_creditos_otros` |
| `situacion_patrimonial_activo_creditos` | `activo_creditos_previsiones` |
| `situacion_patrimonial_activo_creditos` | `activo_creditos_soc_controlada_controlante_vinculada` |
| `situacion_patrimonial_activo_disponibilidades` | `activo_bienes_cambio` |
| `situacion_patrimonial_activo_disponibilidades` | `activo_bienes_intangibles` |
| `situacion_patrimonial_activo_disponibilidades` | `activo_bienes_uso` |
| `situacion_patrimonial_activo_disponibilidades` | `activo_cheques_cartera` |
| `situacion_patrimonial_activo_disponibilidades` | `activo_creditos` |
| `situacion_patrimonial_activo_disponibilidades` | `activo_disponibilidades` |
| `situacion_patrimonial_activo_disponibilidades` | `activo_efectivo_moneda_extranjera` |
| `situacion_patrimonial_activo_disponibilidades` | `activo_efectivo_moneda_nacional` |
| `situacion_patrimonial_activo_disponibilidades` | `activo_inversiones` |
| `situacion_patrimonial_activo_disponibilidades` | `activo_obras_construccion` |
| `situacion_patrimonial_activo_disponibilidades` | `activo_total` |
| `situacion_patrimonial_activo_disponibilidades` | `activo_total_bancos` |
| `situacion_patrimonial_compacto` | `activo_total` |
| `situacion_patrimonial_compacto` | `pasivo_total` |
| `situacion_patrimonial_compacto` | `patrimonio_neto_cierre` |
| `situacion_patrimonial_compacto` | `patrimonio_neto_inicio` |
| `situacion_patrimonial_pasivo` | `pasivo_deudas` |
| `situacion_patrimonial_pasivo` | `pasivo_previsiones` |
| `situacion_patrimonial_pasivo` | `pasivo_total` |
| `situacion_patrimonial_pasivo_deudas` | `pasivo_deudas` |
| `situacion_patrimonial_pasivo_deudas` | `pasivo_deudas_bancarias_financieras` |
| `situacion_patrimonial_pasivo_deudas` | `pasivo_deudas_comerciales` |
| `situacion_patrimonial_pasivo_deudas` | `pasivo_deudas_cta_particulares_socios` |
| `situacion_patrimonial_pasivo_deudas` | `pasivo_deudas_fiscales` |
| `situacion_patrimonial_pasivo_deudas` | `pasivo_deudas_otras_exterior` |
| `situacion_patrimonial_pasivo_deudas` | `pasivo_deudas_otras_locales` |
| `situacion_patrimonial_pasivo_deudas` | `pasivo_deudas_soc_controlada_controlante_vinculada` |
| `situacion_patrimonial_pasivo_deudas` | `pasivo_deudas_sociales` |
| `situacion_patrimonial_pasivo_deudas` | `pasivo_previsiones` |
| `situacion_patrimonial_pasivo_deudas` | `pasivo_total` |
| `situacion_patrimonial_patrimonio_aumentos` | `patrimonio_neto_ajuste_ejercicios_anteriores_negativo` |
| `situacion_patrimonial_patrimonio_aumentos` | `patrimonio_neto_ajuste_ejercicios_anteriores_positivo` |
| `situacion_patrimonial_patrimonio_aumentos` | `patrimonio_neto_aumentos` |
| `situacion_patrimonial_patrimonio_aumentos` | `patrimonio_neto_aumentos_aportes_capital` |
| `situacion_patrimonial_patrimonio_aumentos` | `patrimonio_neto_aumentos_capitalizaciones` |
| `situacion_patrimonial_patrimonio_aumentos` | `patrimonio_neto_aumentos_otros` |
| `situacion_patrimonial_patrimonio_aumentos` | `patrimonio_neto_cierre` |
| `situacion_patrimonial_patrimonio_aumentos` | `patrimonio_neto_cierre_negativo` |
| `situacion_patrimonial_patrimonio_aumentos` | `patrimonio_neto_cierre_positivo` |
| `situacion_patrimonial_patrimonio_aumentos` | `patrimonio_neto_disminuciones` |
| `situacion_patrimonial_patrimonio_aumentos` | `patrimonio_neto_inicio` |
| `situacion_patrimonial_patrimonio_aumentos` | `patrimonio_neto_inicio_negativo` |
| `situacion_patrimonial_patrimonio_aumentos` | `patrimonio_neto_inicio_positivo` |
| `situacion_patrimonial_patrimonio_aumentos` | `resultado_final_ejercicio_contable_beneficio` |
| `situacion_patrimonial_patrimonio_aumentos` | `resultado_final_ejercicio_contable_perdida` |
| `situacion_patrimonial_patrimonio_disminuciones` | `patrimonio_neto_disminuciones` |
| `situacion_patrimonial_patrimonio_disminuciones` | `patrimonio_neto_disminuciones_dividendos_efectivo_especie` |
| `situacion_patrimonial_patrimonio_disminuciones` | `patrimonio_neto_disminuciones_honorarios` |
| `situacion_patrimonial_patrimonio_disminuciones` | `patrimonio_neto_disminuciones_otros` |
| `situacion_patrimonial_patrimonio_disminuciones` | `patrimonio_neto_disminuciones_reduccion_capital` |

## 5. Archivos De Referencia

- Diseno ETL: `documentation/afip/etl_design.md`.
- Plan de trabajo: `documentation/afip/work_plan.md`.
- Comparabilidad de variables: `documentation/afip/variable_comparability.md`.
- Homologacion de ramas: `documentation/afip/branch_harmonization.md`.
- Advertencias por periodo: `documentation/afip/warnings_by_period.md`.
