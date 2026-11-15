SELECT
  (SELECT count(*) FROM fact_inah_visits_monthly) AS inah_rows,
  (SELECT count(*) FROM fact_datatur_occupancy_monthly) AS hotel_rows,
  (SELECT count(*) FROM dim_period) AS periods,
  (SELECT count(*) FROM dim_entity) AS entities,
  (SELECT count(*) FROM dim_source) AS sources,
  (SELECT count(*) FROM fact_inah_visits_monthly WHERE total_visits=0) AS inah_reported_zeros,
  (SELECT count(*) FROM fact_datatur_occupancy_monthly WHERE observation_status<>'reported') AS hotel_missing_measures,
  (SELECT count(*) FROM campaign_calendar WHERE datatur_status='outside_snapshot') AS calendar_outside_datatur,
  (SELECT round(max(residual_pp),10) FROM fact_datatur_occupancy_monthly) AS hotel_max_residual_pp,
  (SELECT count(*)-count(DISTINCT(site_id,period)) FROM fact_inah_visits_monthly) AS fail_inah_keys,
  (SELECT count(*)-count(DISTINCT(center_id,period)) FROM fact_datatur_occupancy_monthly) AS fail_hotel_keys,
  (SELECT count(*)-count(DISTINCT(center_id,period,edition)) FROM silver_datatur_vintages) AS fail_silver_keys,
  (SELECT count(*)-count(DISTINCT(edition,sheet,source_row)) FROM bronze_datatur) AS fail_bronze_keys,
  (SELECT count(*) FROM fact_inah_visits_monthly WHERE state_code<>'24' OR
     site_id IS NULL OR day(period)<>1 OR year(period)<>year OR month(period)<>month OR
     least(national_visits,foreign_visits,total_visits)<0 OR (valid_for_comparison AND
       (national_visits IS NULL OR foreign_visits IS NULL OR total_visits<>national_visits+foreign_visits)))
     AS fail_inah_measures,
  (SELECT count(*) FROM fact_datatur_occupancy_monthly WHERE center_id<>'datatur:slp-selected-hotel-center'
     OR day(period)<>1 OR (observation_status='reported' AND
       (available_rooms_daily_avg IS NULL OR occupied_rooms_daily_avg IS NULL OR hotel_occupancy_percent IS NULL
        OR available_rooms_daily_avg<=0 OR occupied_rooms_daily_avg<0 OR occupied_rooms_daily_avg>available_rooms_daily_avg
        OR hotel_occupancy_percent NOT BETWEEN 0 AND 100 OR residual_pp>0.1))) AS fail_hotel_measures,
  ((SELECT count(*) FROM fact_inah_visits_monthly ANTI JOIN dim_period USING(period))
   +(SELECT count(*) FROM fact_datatur_occupancy_monthly ANTI JOIN dim_period USING(period))
   +(SELECT count(*) FROM fact_inah_visits_monthly i ANTI JOIN dim_entity d ON i.site_id=d.entity_id AND d.family='INAH')
   +(SELECT count(*) FROM fact_datatur_occupancy_monthly h ANTI JOIN dim_entity d ON h.center_id=d.entity_id AND d.family='DataTur')
   +(SELECT count(*) FROM fact_inah_visits_monthly ANTI JOIN dim_source USING(source_id,source_version))
   +(SELECT count(*) FROM fact_datatur_occupancy_monthly ANTI JOIN dim_source USING(source_id,source_version))) AS fail_dimension_fk,
  ((SELECT count(*) FROM bronze_datatur ANTI JOIN raw_datatur_manifest USING(source_id,edition,archive))
   +(SELECT count(*) FROM silver_datatur_vintages ANTI JOIN bronze_datatur USING(source_id,edition,member,sheet,source_row))) AS fail_datatur_lineage;
