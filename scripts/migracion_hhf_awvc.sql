-- Ejecutar en Supabase > SQL Editor. Haz antes una copia: create table atmosfera_backup as select * from atmosfera;
create table if not exists atmosfera_backup_20261117 as select * from atmosfera;
alter table atmosfera rename column fce to hhf;
alter table atmosfera rename column awgp to awvc;
alter table atmosfera add column if not exists estacion_id text;
alter table atmosfera add column if not exists d_km numeric;
alter table atmosfera add column if not exists dz_m numeric;
alter table atmosfera add column if not exists baja_representatividad boolean default false;
alter table atmosfera add column if not exists n_dias_validos int;
-- clave unica necesaria para el upsert del cargador (falla si hay duplicados: revisalos antes)
create unique index if not exists atmosfera_mun_anio_uq on atmosfera (municipio_id, "año");
