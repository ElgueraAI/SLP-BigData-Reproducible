-- Q1
SELECT site_id, min(site_name) AS site_name, year, count(*) AS expected_months,
       count(total_visits) AS reported_months, sum(total_visits) AS entries
FROM gold GROUP BY site_id, year
HAVING count(*)=12 AND count(total_visits)=12
ORDER BY site_id, year;

-- Q2
SELECT site_id, site_name, period, national_visits, foreign_visits, total_visits, observation_status
FROM gold ORDER BY site_id, period;

-- Q3
SELECT site_id, min(site_name) AS site_name, year, count(*) AS paired_months,
       sum(national_visits) AS national, sum(foreign_visits) AS foreign_entries, sum(total_visits) AS entries,
       round(100.0*sum(national_visits)/nullif(sum(total_visits),0),4) AS national_percent,
       round(100.0*sum(foreign_visits)/nullif(sum(total_visits),0),4) AS foreign_percent
FROM gold WHERE valid_for_comparison GROUP BY site_id, year ORDER BY site_id, year;

-- Q4
WITH counts AS (
  SELECT site_id, min(site_name) AS site_name, month, count(*) AS paired_years,
         min(year) AS first_year, max(year) AS last_year, median(total_visits) AS median_entries
  FROM gold WHERE valid_for_comparison AND year IN (
    SELECT year FROM gold GROUP BY year
    HAVING count(*)=12*count(DISTINCT site_id) AND count(total_visits)=count(*)
  )
  GROUP BY site_id,month
)
SELECT *, dense_rank() OVER (PARTITION BY site_id ORDER BY median_entries DESC) AS high_rank,
          dense_rank() OVER (PARTITION BY site_id ORDER BY median_entries) AS low_rank
FROM counts ORDER BY site_id,month;

-- Q5
SELECT site_id, min(site_name) AS site_name, count(*) AS expected_months, count(total_visits) AS reported_months,
       count(*)-count(total_visits) AS months_without_total,
       count(*) FILTER (WHERE observation_status='no_source_row') AS months_absent,
       count(*) FILTER (WHERE observation_status='missing_pair') AS months_with_no_counts,
       count(*) FILTER (WHERE observation_status='partial_pair') AS months_with_one_count,
       round(100.0*(count(*)-count(total_visits))/count(*),4) AS missing_percent
FROM gold GROUP BY site_id ORDER BY site_id;

-- Q6
WITH diff AS (
 SELECT coalesce(g.site_type,h.site_type) AS site_type, coalesce(g.site_code,h.site_code) AS site_code,
        coalesce(g.period,h.period) AS period,
        g.national_visits AS derived_national, h.national_visits AS historic_national,
        g.foreign_visits AS derived_foreign, h.foreign_visits AS historic_foreign,
        g.total_visits AS derived_total, h.total_visits AS historic_total,
        CASE WHEN g.site_id IS NULL THEN 'historical_only'
             WHEN h.site_code IS NULL THEN 'derived_only'
             WHEN g.national_visits IS DISTINCT FROM h.national_visits
               OR g.foreign_visits IS DISTINCT FROM h.foreign_visits
               OR g.total_visits IS DISTINCT FROM h.total_visits THEN 'values_differ'
             ELSE 'match' END AS comparison
 FROM gold g FULL OUTER JOIN history h ON g.site_type=h.site_type AND g.site_code=h.site_code AND g.period=h.period
)
SELECT * FROM diff ORDER BY site_type,site_code,period,comparison;

-- Q7
WITH years AS (
  SELECT site_id, min(site_name) AS site_name, year, count(*) AS expected_months, count(total_visits) AS observed_months,
         sum(total_visits) AS entries
  FROM gold GROUP BY site_id,year
  HAVING count(*)=12 AND count(total_visits)=12
)
SELECT r.site_id, r.site_name, l.year AS prior_year, r.year AS compared_year,
       l.entries AS prior_entries, r.entries AS compared_entries, r.entries-l.entries AS entry_difference,
       r.expected_months AS months
FROM years r JOIN years l ON r.site_id=l.site_id AND r.year=l.year+1 ORDER BY r.site_id,r.year;
