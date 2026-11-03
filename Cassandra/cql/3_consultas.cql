USE aforo_salas;

-- Q1: ocupación de una sala a lo largo de un día
SELECT hora, ocupados, libres, porcentaje
FROM ocupacion_sala
WHERE sala_id = 'MOS-BIB-S1' AND fecha = '2026-05-25';

-- Q2: misma sala, tramo horario
SELECT hora, ocupados, porcentaje
FROM ocupacion_sala
WHERE sala_id = 'MOS-BIB-S1' AND fecha = '2026-05-25'
  AND hora >= '10:00:00' AND hora <= '14:00:00';

-- Q3: historial de un estudiante en un mes
SELECT ts_entrada, sala_id, puesto, duracion_min, redirigido
FROM visitas
WHERE estudiante_id = 'EST00062' AND mes = '2026-04';

-- Q4: top salas más llenas de un campus un dia (por pico)
SELECT sala_id, pico_pct, pico_ocupados, entradas
FROM top_salas_dia
WHERE campus = 'MOS' AND fecha = '2026-05-25'
LIMIT 5;

-- Q5: resumen diario de una sala en un mes
SELECT fecha, periodo, pico_pct, ocupacion_media_pct, entradas, minutos_completa
FROM resumen_sala
WHERE sala_id = 'MOS-BIB-S1' AND mes = '2026-05';

-- Q6: puestos más usados de una sala en un mes
SELECT puesto, usos, minutos_uso, enchufe, ventana
FROM puestos_mes
WHERE sala_id = 'MOS-BIB-S1' AND mes = '2026-05'
LIMIT 10;