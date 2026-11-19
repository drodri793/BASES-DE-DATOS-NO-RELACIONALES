# Cassandra - aforo de salas

Parte B de la práctica: histórico de ocupación de salas de estudio

## Requisitos

- Docker Desktop instalado y abierto.
- Este repositorio clonado.

Los comandos se ejecutan en PowerShell desde la carpeta `Cassandra`.

## Puesta en marcha desde cero

### 1. Arrancar Cassandra

```bash
docker compose up -d
```

La primera vez descarga la imagen `cassandra:4.1`, lo que puede tardar unos minutos.

### 2. Esperar a que el nodo esté listo

```bash
docker exec -it cassandra-aforo nodetool status
```

Repetir hasta que el estado sea `UN` (puede tardar 1-2 minutos). Si da error o aparece `UJ`, todavía está arrancando.

### 3. Crear el keyspace y las tablas

```bash
docker exec cassandra-aforo mkdir -p /cql
docker cp cql/. cassandra-aforo:/cql/
docker exec cassandra-aforo cqlsh -f /cql/1_crear_tablas.cql
```

### 4. Copiar los CSV al contenedor

```bash
docker exec cassandra-aforo mkdir -p /data
docker cp dataset_aforo/. cassandra-aforo:/data/
```

### 5. Cargar los datos

```bash
docker exec cassandra-aforo cqlsh -f /cql/2_carga_datos.cql
```

Filas esperadas por tabla:

| Tabla | Filas |
|---|---|
| `ocupacion_sala` | 29262 |
| `puestos_mes` | 2196 |
| `visitas` | 61949 |
| `top_salas_dia` | 612 |
| `resumen_sala` | 612 |

### 6. Comprobar que funciona

```bash
docker exec -it cassandra-aforo cqlsh
```

Dentro de `cqlsh`:

```sql
USE aforo_salas;
TRACING ON;
```

Y lanzar la consulta Q1 de `cql/3_consultas.cql`: debe devolver 50 filas.

## Entrar a cqlsh

```bash
docker exec -it cassandra-aforo cqlsh
```

### Dentro de cqlsh:

```sql
USE aforo_salas;
```

## Qué hay en esta carpeta

- `docker-compose.yml` - un nodo de Cassandra
- `dataset_aforo/` - CSVs para cargar
- `cql/1_crear_tablas.cql` - keyspace y tablas
- `cql/2_carga_datos.cql` - carga de los CSV con `COPY`
- `cql/3_consultas.cql` - las 6 consultas (Q1–Q6)

## Parar docker

```bash
docker compose stop
```