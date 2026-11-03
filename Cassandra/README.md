# Cassandra - aforo de salas

Parte B de la práctica: histórico de ocupación de salas de estudio

## Arrancar docker

```bash
cd Cassandra
docker compose up -d
```

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
- `cql/2_carga_datos.txt` - cómo se cargaron los datos
- `cql/3_consultas.cql` - las 6 consultas (Q1–Q6)

## Parar docker

```bash
docker compose stop
```