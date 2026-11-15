-- Q1
SELECT 'INAH' AS family,site_id AS entity_id,min(site_name) AS entity_name,min(period) AS first_period,
       max(period) AS last_period,count(*) AS rows,count(total_visits) AS reported_months
FROM fact_inah_visits_monthly GROUP BY site_id
UNION ALL
SELECT 'DataTur',center_id,min(center_name),min(period),max(period),count(*),count(hotel_occupancy_percent)
FROM fact_datatur_occupancy_monthly GROUP BY center_id
ORDER BY family,entity_id;

-- Q2
WITH samples AS (
  SELECT site_id,month(period) AS calendar_month,count(*) AS reported_years,median(total_visits) AS median_registered_entries
  FROM fact_inah_visits_monthly
  WHERE valid_for_comparison AND year(period) BETWEEN 2015 AND 2025
  GROUP BY site_id,calendar_month HAVING count(*)=11
), ranks AS (
  SELECT *,dense_rank() OVER(PARTITION BY site_id ORDER BY median_registered_entries) AS low_rank,
           dense_rank() OVER(PARTITION BY site_id ORDER BY median_registered_entries DESC) AS high_rank
  FROM samples
)
SELECT * FROM ranks WHERE low_rank=1 OR high_rank=1 ORDER BY site_id,calendar_month;

-- Q3
WITH hotel AS (
  SELECT *,lag(period) OVER(PARTITION BY center_id ORDER BY period) previous_period,
    lag(hotel_occupancy_percent) OVER(PARTITION BY center_id ORDER BY period) previous_rate
  FROM fact_datatur_occupancy_monthly
)
SELECT center_id,period,available_rooms_daily_avg,occupied_rooms_daily_avg,hotel_occupancy_percent,
       CASE WHEN date_diff('month',previous_period,period)=1 THEN round(hotel_occupancy_percent-previous_rate,8) END AS difference_pp,
       rate_unit,room_unit,geographic_scope,observation_status,source_id,source_version
FROM hotel ORDER BY period;

-- Q4
SELECT period,museo_status,tamohi_status,tamtoc_status,datatur_status,
       datatur_status='outside_snapshot' AS datatur_outside_snapshot,
       datatur_status IN ('source_missing','no_source_row') AS datatur_missing_in_snapshot
FROM campaign_calendar WHERE museo_status IS DISTINCT FROM 'reported' OR tamohi_status IS DISTINCT FROM 'reported'
   OR tamtoc_status IS DISTINCT FROM 'reported' OR datatur_status<>'reported'
ORDER BY period;

-- Q5
WITH samples AS (
  SELECT site_id,month(period) AS calendar_month,count(*) AS n_2015_2025,
    count(*) FILTER(WHERE year(period)>=2022) AS n_2022_2025,
    median(total_visits) AS median_2015_2025,
    median(total_visits) FILTER(WHERE year(period)>=2022) AS median_2022_2025
  FROM fact_inah_visits_monthly WHERE valid_for_comparison AND year(period) BETWEEN 2015 AND 2025
  GROUP BY site_id,calendar_month HAVING n_2015_2025=11 AND n_2022_2025=4
)
SELECT *,median_2022_2025-median_2015_2025 AS difference_registered_entries
FROM samples ORDER BY site_id,calendar_month;

-- Q6
SELECT * FROM campaign_calendar WHERE period BETWEEN DATE '2024-01-01' AND DATE '2026-08-01' ORDER BY period;

-- Q7
SELECT * FROM (VALUES
 ('access_and_operation','site','operator validation before promotion'),
 ('environmental_capacity','site','capacity and environmental restrictions'),
 ('campaign_response','channel and offer','experiment, spend and conversion'),
 ('hotel_sample_history','monitored center','coverage and methodological breaks'),
 ('travel_constraints_and_costs','route and destination','costs, accessibility and feasible dates')
) AS v(gap,required_scope,decision_gate) ORDER BY gap;

-- Q8
SELECT * FROM (VALUES
 ('Mining','fact_inah_visits_monthly + fact_datatur_occupancy_monthly','EDA by measurement, entity and compatible window'),
 ('Machine Learning','fact_inah_visits_monthly + fact_datatur_occupancy_monthly','time splits and contemporaneous vintages; no unobserved label'),
 ('Stochastic Models','fact_inah_visits_monthly + datatur_revisions','zeros, revision scenarios and regime changes'),
 ('Operations Research','campaign_calendar','context only; budget, capacity and costs still required'),
 ('Digital Marketing','campaign_calendar','hypotheses of calendar; operational verification and outcome measurement')
) AS v(uca,product,gate) ORDER BY uca;
