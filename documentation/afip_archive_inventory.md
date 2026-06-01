# AFIP Archive Inventory

Inventario estructural preliminar de la serie 1998-2023.
Este documento no define reglas de extraccion; solo registra organizacion, formatos y metadatos observables.

Fuente: `https://www.afip.gob.ar/institucional/estudios/anuario-estadisticas-tributarias/`

Fecha de inspeccion: 2026-05-30.

## Resumen

- La serie publica 26 ZIP anuales, uno por anio entre 1998 y 2023.
- No hay una estructura interna unica para todo el periodo.
- Los formatos efectivos cambian entre XLS directo, XLS dentro de CAB, HTML exportado desde Excel y XLS moderno.
- Los metadatos disponibles por archivo son: anio del enlace, nombre del ZIP, URL, `Content-Length`, `Last-Modified`, `ETag`, fechas internas del ZIP/CAB y, para XLS inspeccionables, nombres/dimensiones de hojas.
- Para archivos antiguos, `Last-Modified` del servidor parece reflejar republicacion en 2019, no fecha original del anuario.

## Inventario Por Anio

| Anio | ZIP | Estructura efectiva | Unidades tabla observadas | Notas |
|---:|---|---|---:|---|
| 1998 | `estadisticasTributarias1998.zip` | XLS directo + instalador | 103 | Root `AFIP/Publicacion`; contiene `.xls`, `.cab`, `.exe`, `.lst`. |
| 1999 | `estadisticasTributarias1999.zip` | XLS directo + instalador | 124 | Root mixto con `Archivos/*.xls` y artefactos de instalador. |
| 2000 | `estadisticasTributarias2000.zip` | XLS dentro de `AFIP.CAB` | 133 | ZIP externo solo trae `AFIP.CAB`, `SETUP.LST`, `setup.exe`. |
| 2001 | `estadisticasTributarias2001.zip` | XLS directo + instalador | 276 | `Archivos/2000` y `Archivos/2001`; CAB sin XLS de tablas. |
| 2002 | `estadisticasTributarias2002.zip` | XLS dentro de `AFIP.CAB` | 683 | CAB incluye sufijos `_2000`, `_2001`, `_2002`; anio compuesto. |
| 2003 | `estadisticasTributarias2003.zip` | XLS dentro de `AFIP.CAB` | 376 | Instalador Windows como contenedor externo. |
| 2004 | `estadisticasTributarias2004.zip` | XLS dentro de `AFIP.CAB` | 380 | Patron CAB estable. |
| 2005 | `estadisticasTributarias2005.zip` | XLS dentro de `AFIP.CAB` | 380 | Patron CAB estable. |
| 2006 | `estadisticasTributarias2006.zip` | XLS dentro de `AFIP.CAB` | 380 | Patron CAB estable. |
| 2007 | `estadisticasTributarias2007.zip` | XLS dentro de `AFIP.CAB` | 371 | Patron CAB estable, menor cantidad de tablas. |
| 2008 | `estadisticasTributarias2008.zip` | XLS dentro de `AFIP.CAB` | 377 | Ultimo anio CAB observado. |
| 2009 | `estadisticasTributarias2009.zip` | HTML exportado desde Excel | 321 | `Archivos/**`; muchas carpetas de soporte por tabla. |
| 2010 | `estadisticasTributarias2010.zip` | HTML exportado desde Excel | 333 | `Archivos/Reca/**` y `Indice.htm`. |
| 2011 | `estadisticasTributarias2011.zip` | HTML exportado desde Excel | 319 | Root codificado como `Publicaci≤n AFIP` en listado ZIP. |
| 2012 | `estadisticasTributarias2012.zip` | HTML exportado desde Excel | 319 | Igual familia que 2011. |
| 2013 | `estadisticasTributarias2013.zip` | HTML exportado desde Excel | 319 | Incluye directorios explicitos y soportes `*_archivos`. |
| 2014 | `estadisticasTributarias2014.zip` | HTML exportado desde Excel | 393 | Root `archivos/` en minuscula; mas tablas HTML. |
| 2015 | `estadisticasTributarias2015.zip` | XLS directo | 399 | Root dice `Anuario Estadisitcas Tributarias Año 2016`; probable etiqueta inconsistente. |
| 2016 | `estadisticasTributarias2016.zip` | XLS directo | 312 | Root `AnuarioEstadisticasTributarias2016`; subcarpeta `textos/`. |
| 2017 | `estadisticasTributarias2017.zip` | XLS directo | 312 | Similar a 2016; incluye `Tabla ganancia.xls`. |
| 2018 | `estadisticasTributarias2018.zip` | XLS directo + XLSX auxiliar | 340 | Root `EstadisticasTributarias2018`; `textos/` trae duplicados `.xlsx`. |
| 2019 | `Public2019.zip` | XLS directo + algunos XLSX | 305 | Root `Public 2019/Cuadros`; no subcarpeta `textos/` detectable. |
| 2020 | `Publicacion-2020.zip` | XLS directo | 328 | Root `Cuadros/`; subcarpeta `textos/`. |
| 2021 | `Estadisticas-Tributarias-2021.zip` | XLS directo | 334 | Root `Estadísticas Tributarias 2021`; `Textos/` con mayuscula. |
| 2022 | `estadisticas-Tributarias-2022.zip` | XLS directo | 364 | Root `Estadísticas Tributarias 2022`; `textos/` minuscula. |
| 2023 | `Estadisticas-Tributarias-2023.zip` | XLS directo | 362 | Root `Estadísticas Tributarias 2023`; estructura moderna. |

## Epocas Homogeneas Propuestas

1. `legacy_direct_xls_install_layout`: 1998, 1999, 2001.
2. `cab_embedded_xls`: 2000, 2002-2008.
3. `excel_html_export`: 2009-2014.
4. `modern_direct_xls_transition`: 2015-2020.
5. `modern_direct_xls_current`: 2021-2023.

El criterio de agrupamiento es operativo: contenedor efectivo, formato de la unidad tabla, patron de rutas internas y tratamiento necesario antes de leer la tabla.

## Observaciones Sobre Estructura Interna

- En los XLS inspeccionados, la mayoria de tablas son libros de una sola hoja.
- Los nombres de hoja tienden a replicar el identificador de tabla, por ejemplo `1.1.1.1.`.
- Las dimensiones varian por tabla y anio; no conviene fijar una unica fila de encabezado sin inventario de contenido.
- Los sufijos `_2`, `_2-` y archivos con `Continuacion` deben tratarse como partes de tabla o continuaciones, no como tablas independientes hasta validar el indice.
- La epoca 2009-2014 requiere un parser distinto porque las tablas estan en HTML exportado desde Excel, no en XLS plano.
- El archivo 2002 es anomalo porque el CAB incluye tablas con sufijos de varios anios.
