CREATE TABLE fact_datatur_occupancy_monthly AS
SELECT center_id,center_name,period,available_rooms_daily_avg,occupied_rooms_daily_avg,
       hotel_occupancy_percent,residual_pp,observation_status,source_id,
       strftime(edition,'%Y-%m') AS source_version,member,sheet,source_row,
       'SELECTED_HOTEL_CENTER_NOT_STATE' AS geographic_scope,
       'rooms_per_day_monthly_average' AS room_unit,
       'percent_occupied_rooms' AS rate_unit,
       'DataTur monitored hotel-center sample; month-specific reporting coverage' AS coverage
FROM silver_datatur_vintages WHERE contemporary;

CREATE TABLE dim_period AS
SELECT CAST(period AS DATE) period, year(period)::INTEGER AS year, month(period)::INTEGER AS month,
       day(last_day(period)) AS days_in_month
FROM generate_series(DATE '2015-01-01',DATE '2026-08-01',INTERVAL '1 month') t(period);

CREATE TABLE dim_entity AS
SELECT site_id AS entity_id, min(site_name) AS entity_name, 'INAH' AS family,
       min(geographic_scope) geographic_scope
FROM fact_inah_visits_monthly GROUP BY site_id
UNION ALL
SELECT center_id, min(center_name), 'DataTur', min(geographic_scope)
FROM fact_datatur_occupancy_monthly GROUP BY center_id;

CREATE TABLE dim_source AS
SELECT DISTINCT source_id,source_version,'INAH' AS family,
       'https://www.datos.inah.gob.mx/datos-abiertos' AS official_url
FROM fact_inah_visits_monthly
UNION ALL
SELECT source_id,strftime(edition,'%Y-%m'),'DataTur',official_url FROM raw_datatur_manifest;

CREATE TABLE datatur_revisions AS
SELECT h.center_id,h.period,h.source_id AS contemporary_source_id,
       s.source_id AS comparison_source_id,s.edition AS comparison_edition,
       s.available_rooms_daily_avg-h.available_rooms_daily_avg AS available_delta,
       s.occupied_rooms_daily_avg-h.occupied_rooms_daily_avg AS occupied_delta,
       s.hotel_occupancy_percent-h.hotel_occupancy_percent AS rate_delta_pp,
       (abs(available_delta)>1e-8 OR abs(occupied_delta)>1e-8 OR abs(rate_delta_pp)>1e-8) AS changed
FROM fact_datatur_occupancy_monthly h JOIN silver_datatur_vintages s USING(center_id,period)
WHERE NOT s.contemporary AND s.observation_status='reported' AND h.observation_status='reported';

CREATE VIEW campaign_calendar AS
WITH inah AS (
  SELECT period,
    max(total_visits) FILTER(WHERE site_id='museo:2301600') museo_entries,
    max(total_visits) FILTER(WHERE site_id='zona_arqueologica:3120099') tamohi_entries,
    max(total_visits) FILTER(WHERE site_id='zona_arqueologica:3120100') tamtoc_entries,
    max(observation_status) FILTER(WHERE site_id='museo:2301600') museo_status,
    max(observation_status) FILTER(WHERE site_id='zona_arqueologica:3120099') tamohi_status,
    max(observation_status) FILTER(WHERE site_id='zona_arqueologica:3120100') tamtoc_status,
    max(source_id) FILTER(WHERE site_id='museo:2301600') museo_source,
    max(source_id) FILTER(WHERE site_id='zona_arqueologica:3120099') tamohi_source,
    max(source_id) FILTER(WHERE site_id='zona_arqueologica:3120100') tamtoc_source,
    max(source_version) inah_source_version
  FROM fact_inah_visits_monthly GROUP BY period
)
SELECT d.period,i.* EXCLUDE(period),
       'registered_entries_per_INAH_site_month' AS inah_unit,
       'INAH_RECEPTION_SITE' AS inah_scope,
       'Museo Regional Potosino; Tamohí; Tamtoc, 2015-01 through 2026-08' AS inah_coverage,
       h.center_id,h.center_name,h.available_rooms_daily_avg,h.occupied_rooms_daily_avg,h.hotel_occupancy_percent,
       coalesce(h.observation_status,'outside_snapshot') AS datatur_status,
       h.source_id AS datatur_source,h.source_version AS datatur_source_version,
       'percent_occupied_rooms' AS datatur_rate_unit,
       'rooms_per_day_monthly_average' AS datatur_room_unit,
       'SELECTED_HOTEL_CENTER_NOT_STATE' AS datatur_scope,
       'DataTur monitored center; snapshot 2024-01 through 2026-07' AS datatur_coverage,
       'compare_time_patterns_only; no cross-source sums or causal inference' AS aggregation_rule
FROM dim_period d LEFT JOIN inah i USING(period)
LEFT JOIN fact_datatur_occupancy_monthly h USING(period);
