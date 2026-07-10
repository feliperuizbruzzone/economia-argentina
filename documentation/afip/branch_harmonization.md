# AFIP Ganancias Sociedades Branch Harmonization Plan

Este documento registra la primera homologacion operativa de ramas economicas
para el capitulo `Impuesto a las Ganancias Sociedades`.

## Alcance

La homologacion se aplica despues de la extraccion y del ensamble P0-P6. No
modifica columnas fuente: conserva `activity_level`, `activity_code`,
`activity_label_original`, `activity_section_original` y `classifier_period`.

Salidas vigentes:

```text
data/analysis-data/20260710_afip_ganancias_sociedades_tidy_homologado.csv
data/intermediate-data/afip-estadisticas-tributarias/20260710_afip_ganancias_sociedades_source_dictionary.csv
data/intermediate-data/afip-estadisticas-tributarias/20260710_afip_ganancias_sociedades_activity_dictionary.csv
data/intermediate-data/afip-estadisticas-tributarias/20260710_afip_ganancias_sociedades_variable_dictionary.csv
data/intermediate-data/afip-estadisticas-tributarias/20260710_afip_ganancias_sociedades_ramas_homologacion_diccionario.csv
data/output-data/validation_reports/ganancias_sociedades_tidy_outputs_validation.md
data/output-data/validation_reports/ganancias_sociedades_tidy_branch_counts.csv
```

## Decision Metodologica

Se usan dos capas de rama:

1. `rama_comun_*`: maximo comun denominador comparable en toda la serie
   fiscal 1997-2022. Es necesariamente amplio porque fiscal 1997 solo publica
   actividad amplia.
2. `rama_detalle_homologada_*`: conserva el maximo detalle observado, con
   codigos namespaced por clasificador (`new_3d_*`, `old_3d_*`,
   `new_section_*`, `old_section_*`, `old_broad_*`). Esto evita tratar como
   equivalentes directos codigos de 3 digitos de clasificadores distintos.

La regla no implementa aun una correspondencia oficial de 3 digitos entre
clasificador viejo y nuevo. Esa correspondencia queda como tarea metodologica
posterior si se requiere una serie sectorial fina empalmada.

## Columnas Agregadas Al Diccionario De Actividad

- `rama_homologacion_version`
- `rama_homologacion_estado`
- `rama_comun_codigo`
- `rama_comun_label`
- `rama_comun_nivel`
- `rama_detalle_homologada_codigo`
- `rama_detalle_homologada_label`
- `rama_detalle_homologada_nivel`
- `rama_homologacion_nota`

## Mapeo De Ramas Comunes

| Rama comun | Clasificador nuevo | Clasificador viejo | P6 amplio |
|---|---|---|---|
| `AGRICULTURA_PESCA` | A | A+B | Agricultura/caza/silvicultura/pesca |
| `MINAS_CANTERAS` | B | C | Explotacion de minas y canteras |
| `INDUSTRIA_MANUFACTURERA` | C | D | Industrias manufactureras |
| `ELECTRICIDAD_GAS_AGUA` | D+E | E | Electricidad, gas y agua |
| `CONSTRUCCION` | F | F | Construccion |
| `COMERCIO_HOTELES_RESTAURANTES` | G+I | G+H | Comercio, restaurantes y hoteles |
| `TRANSPORTE_COMUNICACIONES` | H+J | I | Transporte, almacenamiento y comunicaciones |
| `FINANZAS_INMUEBLES_SERVICIOS_EMPRESARIALES` | K+L+M+N | J+K | Finanzas, seguros, inmuebles y servicios empresariales |
| `SERVICIOS_SOCIALES_PERSONALES_PUBLICOS` | O+P+Q+R+S | L+M+N+O | Servicios comunales, sociales y personales |
| `OTRAS_NO_ESPECIFICADAS` | Otras actividades | Otras actividades | Actividades no bien especificadas |
| `TOTAL` | Total fuente | Total fuente | Total fuente |

## Validacion

La validacion `68_validate_ganancias_sociedades_tidy_outputs.py` confirma:

- 341.103 filas monetarias en el panel analitico homologado.
- tamano sin comprimir de 81.500.612 bytes, menor al limite normal de GitHub.
- cobertura fiscal 1997-2022 completa.
- 0 filas `NO_HOMOLOGADO`.
- 320 entradas en el diccionario de fuente.
- 546 entradas en el diccionario de actividad/ramas.
- 185 entradas en el diccionario de variables.

Advertencia metodologica: la homologacion preserva filas y agrega ramas comunes
amplias; los codigos de 3 digitos viejo/nuevo siguen siendo especificos de su
clasificador.
