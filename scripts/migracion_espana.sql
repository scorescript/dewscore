-- Ejecutar en Supabase > SQL Editor (una sola vez), ANTES de cargar los municipios de España.
alter table municipios add column if not exists ine text;
alter table municipios add column if not exists geom_3857 geometry(MultiPolygon, 3857);

-- geometria proyectada precalculada + indice espacial (los tiles dejan de proyectar en cada peticion)
update municipios set geom_3857 = ST_Multi(ST_Transform(geom, 3857)) where geom is not null;
create index if not exists municipios_geom3857_gix on municipios using gist (geom_3857);

create or replace function municipios_sync_3857() returns trigger language plpgsql as $$
begin
  if new.geom is null then new.geom_3857 := null;
  else new.geom_3857 := ST_Multi(ST_Transform(new.geom, 3857)); end if;
  return new;
end $$;
drop trigger if exists trg_municipios_sync_3857 on municipios;
create trigger trg_municipios_sync_3857 before insert or update of geom on municipios
  for each row execute function municipios_sync_3857();
