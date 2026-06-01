# Intermediate Data

Archivos transitorios generados por scripts. Deben poder regenerarse desde `data/input-data/` y `command-files/`.

Las salidas intermedias de AFIP/ARCA se escriben bajo:

```text
data/intermediate-data/afip-estadisticas-tributarias/
```

Esa subcarpeta es la ubicacion canonica para esta fuente. Si quedan CSV AFIP antiguos directamente en `data/intermediate-data/`, deben tratarse como salidas obsoletas de corridas previas y no como insumos del pipeline actual.
