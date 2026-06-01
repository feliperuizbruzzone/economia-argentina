# AFIP P4 Warnings

Periodo: `P4_old_cab_xls_detail_thousands`.

Cobertura: publication years 2003-2008 / fiscal years 2002-2007.

Artefactos:

- Inventario: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_inventory_p4.csv`.
- Extraccion larga: `data/intermediate-data/afip-estadisticas-tributarias/afip_ganancias_sociedades_long_p4.csv`.
- Validacion: `data/output-data/validation_reports/ganancias_sociedades_p4_long_validation.md`.
- Conteos: `data/output-data/validation_reports/ganancias_sociedades_p4_long_counts.csv`.

## Resultado De Validacion

- Filas largas: 132.088.
- Pares anio-cuadro: 60.
- Variables canonicas observadas: 111.
- Fallas: 0.
- Advertencias: 25.

## Advertencias Documentadas

1. Los archivos fuente estan dentro de `AFIP.CAB`; el pipeline extrae solo los XLS `2.3.1.1*.xls` en carpetas temporales y no modifica los ZIP crudos.
   - Dependencia operativa: `cabextract`.
2. En todos los cuadros P4 se uso la continuacion `_2.xls`, que contiene el maximo detalle de actividad economica disponible.
3. El cuadro `2.3.1.1.2.1` usa el componente `OTROS` dentro de costos. Se conserva como `costos_otros` y `costos_otros_casos`; no se homologa automaticamente a `gastos_vinculados_al_costo`.
4. La numeracion antigua de P4 condensa resultados en menos cuadros que P0-P2:
   - `2.3.1.1.2.2` contiene resultado bruto, resultado por venta de acciones, deudores incobrables y otros gastos operativos.
   - `2.3.1.1.2.3` contiene resultados por inversiones permanentes, financieros, contratos derivados y otros ingresos/egresos.
   - `2.3.1.1.2.4` contiene resultados extraordinarios, impuesto a las ganancias y resultado contable.
5. Fiscal year 2007, actividad `142. Explotacion de minas y canteras n.c.p.`, en `2.3.1.1.2.1`, trae solo `presentaciones_total`. Las variables restantes del renglon estan en blanco en la fuente y el pipeline no las imputa.

## Implicacion Metodologica

P4 es comparable con P3 en clasificador viejo y unidad monetaria (`miles_pesos_corrientes`), pero no tiene el mismo detalle de subcuadros que P0-P2. Para series largas se deben distinguir:

- variables observadas directamente en P4;
- variables disponibles solo en epocas mas recientes;
- variables derivables por resta o agregacion, que requieren una decision metodologica posterior.

La homologacion de ramas economicas sigue pendiente y no fue implementada en esta fase.
