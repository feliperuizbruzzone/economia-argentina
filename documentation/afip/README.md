# AFIP Documentation

Documentacion especifica de la fuente AFIP/ARCA para el proyecto
`economia-argentina`.

## Criterio De Organizacion

Los documentos especificos de una fuente se guardan bajo
`documentation/<fuente>/`. En esta carpeta, el prefijo `afip_` se elimina de
los nombres porque la fuente ya queda indicada por la ruta.

Archivos actuales:

- `source.md`: fuente oficial y notas iniciales.
- `archive_inventory.md`: inventario estructural preliminar de ZIPs 1998-2023.
- `structural_mapping.yml`: diccionario estructural por epoca.
- `work_plan.md`: plan de trabajo por fases.
- `etl_design.md`: diseno modular del pipeline.
- `variable_comparability.md`: comparabilidad de variables por periodo.
- `branch_harmonization.md`: criterio de homologacion de ramas economicas.
- `warnings_by_period.md`: advertencias y notas estructurales consolidadas por periodo P0-P6.
