-- SlopeGuard database schema (Supabase / PostgreSQL)
-- Run this in the Supabase SQL editor, or via `psql`.

-- Optional but recommended: enables spatial types/queries.
create extension if not exists postgis;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  full_name text,
  role text not null default 'viewer' check (role in ('viewer','analyst','admin')),
  created_at timestamptz not null default now()
);

create table if not exists locations (
  id uuid primary key default gen_random_uuid(),
  state text not null,
  district text not null,
  latitude double precision not null,
  longitude double precision not null,
  geom geometry(Point, 4326),
  created_at timestamptz not null default now(),
  unique (state, district)
);

create table if not exists model_versions (
  id uuid primary key default gen_random_uuid(),
  version text unique not null,
  algorithm text not null,
  trained_on text not null,          -- 'synthetic' | 'production'
  metrics jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create table if not exists environmental_data (
  id uuid primary key default gen_random_uuid(),
  location_id uuid references locations(id) on delete cascade,
  rainfall_24h double precision,
  rainfall_cumulative double precision,
  soil_moisture double precision,
  slope double precision,
  elevation double precision,
  ndvi double precision,
  distance_to_road double precision,
  temperature double precision,
  source text not null default 'demo',   -- 'demo' | 'isro' | 'bhuvan' | 'gee' | 'weather_api'
  recorded_at timestamptz not null default now()
);

create table if not exists historical_landslides (
  id uuid primary key default gen_random_uuid(),
  location_id uuid references locations(id) on delete set null,
  latitude double precision not null,
  longitude double precision not null,
  event_date date,
  severity text,
  source text,
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists risk_predictions (
  id uuid primary key default gen_random_uuid(),
  latitude double precision not null,
  longitude double precision not null,
  state text,
  district text,
  risk_score double precision not null check (risk_score >= 0 and risk_score <= 100),
  risk_level text not null check (risk_level in ('LOW','MODERATE','HIGH','VERY_HIGH')),
  confidence double precision,
  rainfall_24h double precision,
  rainfall_cumulative double precision,
  soil_moisture double precision,
  slope double precision,
  elevation double precision,
  ndvi double precision,
  distance_to_road double precision,
  historical_landslide_density double precision,
  temperature double precision,
  prediction_timestamp timestamptz not null default now(),
  model_version text
);

create table if not exists risk_zones (
  id uuid primary key default gen_random_uuid(),
  location_id uuid references locations(id) on delete cascade,
  state text not null,
  district text not null,
  latitude double precision not null,
  longitude double precision not null,
  risk_score double precision not null,
  risk_level text not null,
  confidence double precision,
  rainfall double precision,
  soil_moisture double precision,
  slope double precision,
  elevation double precision,
  ndvi double precision,
  historical_landslide_density double precision,
  model_version text,
  updated_at timestamptz not null default now()
);

create table if not exists weather_data (
  id uuid primary key default gen_random_uuid(),
  latitude double precision not null,
  longitude double precision not null,
  rainfall_mm double precision,
  temperature_c double precision,
  humidity_pct double precision,
  wind_kmh double precision,
  forecast_note text,
  data_mode text not null default 'demo',
  recorded_at timestamptz not null default now()
);

create table if not exists alerts (
  id uuid primary key default gen_random_uuid(),
  severity text not null check (severity in ('Advisory','Watch','Warning','Critical')),
  title text not null,
  description text,
  state text not null,
  district text not null,
  risk_score double precision not null,
  data_mode text not null default 'demo',
  created_at timestamptz not null default now()
);

create table if not exists data_sources (
  id uuid primary key default gen_random_uuid(),
  name text unique not null,
  type text,
  purpose text,
  update_frequency text,
  status text not null default 'NOT CONFIGURED'
    check (status in ('CONNECTED','AVAILABLE','DEMO MODE','NOT CONFIGURED')),
  updated_at timestamptz not null default now()
);

create table if not exists push_subscriptions (
  id uuid primary key default gen_random_uuid(),
  endpoint text unique not null,
  p256dh text not null,
  auth text not null,
  user_agent text,
  created_at timestamptz not null default now()
);

-- Indexes
create index if not exists idx_risk_predictions_location on risk_predictions (latitude, longitude);
create index if not exists idx_risk_predictions_timestamp on risk_predictions (prediction_timestamp desc);
create index if not exists idx_risk_zones_state on risk_zones (state);
create index if not exists idx_alerts_created on alerts (created_at desc);
create index if not exists idx_alerts_severity on alerts (severity);
create index if not exists idx_environmental_location on environmental_data (location_id);
create index if not exists idx_locations_geom on locations using gist (geom);

-- Seed reference data sources (status reflects prototype defaults)
insert into data_sources (name, type, purpose, update_frequency, status) values
  ('ISRO', 'Environmental / soil-moisture data', 'Soil moisture and terrain indices', 'Daily', 'DEMO MODE'),
  ('Bhuvan', 'ISRO geospatial platform', 'Satellite imagery, DEM, land cover', 'Weekly', 'NOT CONFIGURED'),
  ('Bhusanket', 'Landslide / geospatial info', 'Landslide inventory reference', 'Periodic', 'NOT CONFIGURED'),
  ('Google Earth Engine', 'Satellite processing platform', 'NDVI, rainfall, land cover extraction', 'Daily', 'DEMO MODE'),
  ('Weather Forecast API', 'Meteorological data', 'Rainfall, precipitation forecast', 'Hourly', 'DEMO MODE'),
  ('Historical Landslide Records', 'Ground-truth event log', 'Model training and validation', 'Static / periodic', 'AVAILABLE'),
  ('DEM / Terrain Data', 'Digital elevation model', 'Slope, aspect, elevation features', 'Static', 'AVAILABLE')
on conflict (name) do nothing;
