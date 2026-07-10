# economia-argentina

Repositorio organizado segun el protocolo Project TIER 4.0 para sistematizar series economicas de empresas publicadas por AFIP en el anuario de estadisticas tributarias.

El objetivo es construir una serie 1998-2023 en CSV para analizar rentabilidad y desempeno economico por rama o subrama economica cuando los archivos fuente lo permitan.
El foco operativo actual es el capitulo `Impuesto a las Ganancias Sociedades`, con maxima desagregacion disponible y base canonica en formato largo.

Estado actual: los 26 ZIP crudos AFIP/ARCA para 1998-2023 ya estan descargados en `data/input-data/raw/afip-estadisticas-tributarias/`. El pipeline de Ganancias Sociedades ya cubre P0-P6, fiscal years 1997-2022, y genera un panel analitico homologado sin comprimir menor a 100 MB, con anio, rama original, rama homologada, variable economica y valor monetario.

## Archivos relevantes

- [Minuta del procedimiento AFIP/ARCA](docs/20260710_minuta_afip_arca.md): resumen de descarga, sistematizacion, homologacion y estructura del panel.
- [Panel analitico homologado](data/analysis-data/20260710_afip_ganancias_sociedades_tidy_homologado.csv): salida final sin comprimir y apta para versionar en GitHub.
- [Documentacion AFIP](documentation/afip/README.md): indice de documentos metodologicos de la fuente.

Nota: los diccionarios de trazabilidad se generan en `data/intermediate-data/afip-estadisticas-tributarias/` y no se versionan porque son salidas regenerables.

## Estructura

- `command-files/`: scripts que crean, transforman, validan y analizan los datos.
- `command-files/config/`: constantes y rutas compartidas por los scripts.
- `command-files/processing-command-files/`: pasos de procesamiento, con prefijos numericos y orden de ejecucion explicito.
- `command-files/analysis-command-files/`: scripts de tablas, figuras, modelos y otros analisis.
- `data/input-data/`: datos originales. Se tratan como solo lectura una vez descargados o incorporados.
- `data/intermediate-data/`: archivos transitorios generados por scripts. No son insumos canonicos.
- `data/intermediate-data/afip-estadisticas-tributarias/`: salidas intermedias regenerables de la fuente AFIP/ARCA.
- `data/analysis-data/`: datos listos para analisis. La salida actual es `20260710_afip_ganancias_sociedades_tidy_homologado.csv`.
- `data/output-data/`: resultados generados, como tablas, figuras o reportes.
- `documentation/`: notas metodologicas, diccionarios, referencias y bitacoras.
- `tests/`: pruebas automatizadas y validaciones de reproducibilidad.

## Uso inicial

Desde la raiz del repositorio:

```bash
python3 command-files/processing-command-files/00_prepare_directories.py
```

El parser de archivos CAB requiere `cabextract` instalado en el sistema.

El flujo reproducible actual se ejecuta desde la raiz con:

```bash
python3 command-files/run_all.py
```

Los pasos de procesamiento viven en `command-files/processing-command-files/` y tambien pueden ejecutarse individualmente desde la raiz con:

```bash
python3 command-files/processing-command-files/<script>.py
```

Antes de escribir extraccion sustantiva, revisar:

- `CONTEXT.md`
- `documentation/afip/structural_mapping.yml`
- `documentation/afip/work_plan.md`
- `documentation/afip/branch_harmonization.md`

## Reglas de reproducibilidad

- Usar rutas relativas al proyecto; no guardar rutas absolutas locales en codigo.
- Centralizar constantes en `command-files/config/project_config.py`.
- No modificar manualmente `data/input-data/` salvo el paso explicito de descarga de datos originales.
- Mantener los scripts idempotentes: correrlos dos veces debe dejar el mismo resultado.
- Documentar decisiones metodologicas no triviales en `CONTEXT.md` y, si afectan codigo, con comentarios `# DECISION:`.
