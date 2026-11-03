CREATE KEYSPACE aforo_salas
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE aforo_salas;

CREATE TABLE ocupacion_sala (
  sala_id text,
  fecha date,
  hora time,
  ocupados int,
  libres int,
  porcentaje float,
  PRIMARY KEY ((sala_id, fecha), hora)
) WITH CLUSTERING ORDER BY (hora ASC);

CREATE TABLE top_salas_dia (
  campus text,
  fecha date,
  pico_pct float,
  sala_id text,
  capacidad int,
  pico_ocupados int,
  ocupacion_media_pct float,
  entradas int,
  PRIMARY KEY ((campus, fecha), pico_pct, sala_id)
) WITH CLUSTERING ORDER BY (pico_pct DESC, sala_id ASC);

CREATE TABLE resumen_sala (
  sala_id text,
  mes text,
  fecha date,
  campus text,
  periodo text,
  capacidad int,
  entradas int,
  pico_pct float,
  ocupacion_media_pct float,
  minutos_completa int,
  PRIMARY KEY ((sala_id, mes), fecha)
) WITH CLUSTERING ORDER BY (fecha ASC);

CREATE TABLE visitas (
  estudiante_id text,
  mes text,
  ts_entrada timestamp,
  ts_salida timestamp,
  fecha date,
  campus text,
  sala_id text,
  puesto int,
  duracion_min int,
  salida_en_cierre boolean,
  redirigido boolean,
  PRIMARY KEY ((estudiante_id, mes), ts_entrada)
) WITH CLUSTERING ORDER BY (ts_entrada ASC);

CREATE TABLE puestos_mes (
  sala_id text,
  mes text,
  usos int,
  puesto int,
  minutos_uso int,
  enchufe boolean,
  ventana boolean,
  PRIMARY KEY ((sala_id, mes), usos, puesto)
) WITH CLUSTERING ORDER BY (usos DESC, puesto ASC);