# v2 item set. Distribution rebalanced after the v1 pilot showed tier 1 had zero
# discriminative power (20/20 for all three models).
#   v1: T1=20  T2=20  T3=10
#   v2: T1=10  T2=15  T3=25
#
# Every question that touches a join now states explicitly whether rows with no
# match are included. The v1 pilot lost an item to exactly that ambiguity.
#
# (id, tier, order_matters, question, gold_sql)

DEV = [
    ("d-01", 1, False, "How many stations are there?",
     "SELECT COUNT(*) FROM station"),
    ("d-02", 1, False, "List the names of all plans.",
     "SELECT name FROM plan"),
    ("d-03", 1, False, "How many bikes have the status 'active'?",
     "SELECT COUNT(*) FROM bike WHERE status = 'active'"),
    ("d-04", 2, False, "For each city, how many stations are there? Give the city and the count.",
     "SELECT city, COUNT(*) FROM station GROUP BY city"),
    ("d-05", 2, False, "Give the member_id and full name of every member on the Student plan.",
     "SELECT m.member_id, m.full_name FROM member m JOIN plan p ON p.plan_id = m.plan_id "
     "WHERE p.name = 'Student'"),
    ("d-06", 2, False, "Give the model name and manufacturer of every electric model with a "
                       "battery of more than 500 Wh.",
     "SELECT name, manufacturer FROM model WHERE is_electric = 1 AND battery_wh > 500"),
    ("d-07", 3, False, "Give the bike_id of every bike that has more than one unresolved "
                       "maintenance record.",
     "SELECT bike_id FROM maintenance WHERE resolved_on IS NULL GROUP BY bike_id "
     "HAVING COUNT(*) > 1"),
    ("d-08", 3, True, "What is the name and capacity of the station with the second-largest "
                      "capacity?",
     "SELECT name, capacity FROM station ORDER BY capacity DESC LIMIT 1 OFFSET 1"),
    ("d-09", 3, False, "Give the member_id of every member whose average trip distance is "
                       "greater than the average trip distance across all trips.",
     "SELECT member_id FROM trip GROUP BY member_id "
     "HAVING AVG(distance_km) > (SELECT AVG(distance_km) FROM trip)"),
    ("d-10", 3, False, "For each manufacturer, give the manufacturer and the number of distinct "
                       "bikes of theirs that have at least one maintenance record.",
     "SELECT mo.manufacturer, COUNT(DISTINCT b.bike_id) FROM bike b "
     "JOIN model mo ON mo.model_id = b.model_id "
     "WHERE b.bike_id IN (SELECT bike_id FROM maintenance) GROUP BY mo.manufacturer"),
]

TEST = [
    # ---------------- Tier 1: single table (10) ---------------------------
    ("t1-01", 1, True, "List the names of all stations in Lyon, in alphabetical order.",
     "SELECT name FROM station WHERE city = 'Lyon' ORDER BY name"),
    ("t1-02", 1, False, "How many bikes have the status 'maintenance'?",
     "SELECT COUNT(*) FROM bike WHERE status = 'maintenance'"),
    ("t1-03", 1, False, "How many members joined in 2025?",
     "SELECT COUNT(*) FROM member WHERE joined_on >= '2025-01-01' AND joined_on <= '2025-12-31'"),
    ("t1-04", 1, False, "What is the average trip distance in km, rounded to 2 decimal places?",
     "SELECT ROUND(AVG(distance_km), 2) FROM trip"),
    ("t1-05", 1, False, "How many maintenance records have not been resolved yet?",
     "SELECT COUNT(*) FROM maintenance WHERE resolved_on IS NULL"),
    ("t1-06", 1, True, "List the 3 cheapest plans by monthly fee, giving the plan name and the fee.",
     "SELECT name, monthly_fee FROM plan ORDER BY monthly_fee ASC LIMIT 3"),
    ("t1-07", 1, False, "What is the total amount paid with the method 'card'?",
     "SELECT SUM(amount) FROM payment WHERE method = 'card'"),
    ("t1-08", 1, False, "How many trips did not end at any station?",
     "SELECT COUNT(*) FROM trip WHERE end_station_id IS NULL"),
    ("t1-09", 1, True, "Give the trip_id and distance of the 5 longest trips by distance, "
                       "longest first.",
     "SELECT trip_id, distance_km FROM trip ORDER BY distance_km DESC, trip_id ASC LIMIT 5"),
    ("t1-10", 1, False, "What is the largest battery capacity in Wh among electric models?",
     "SELECT MAX(battery_wh) FROM model WHERE is_electric = 1"),

    # ---------------- Tier 2: joins, grouping, aggregates (15) ------------
    ("t2-01", 2, False, "For each station, give the station name and the number of bikes "
                        "currently assigned to it. Include stations that have no bikes, with a "
                        "count of 0.",
     "SELECT s.name, COUNT(b.bike_id) FROM station s "
     "LEFT JOIN bike b ON b.station_id = s.station_id GROUP BY s.station_id, s.name"),
    ("t2-02", 2, False, "For each plan, give the plan name and the total amount paid by members "
                        "on that plan. Include every plan, even those whose members have made no "
                        "payments; use 0 for those.",
     "SELECT p.name, COALESCE(SUM(pay.amount), 0) FROM plan p "
     "LEFT JOIN member m ON m.plan_id = p.plan_id "
     "LEFT JOIN payment pay ON pay.member_id = m.member_id GROUP BY p.plan_id, p.name"),
    ("t2-03", 2, True, "Which manufacturer has the most bikes in the fleet? Give the "
                       "manufacturer name only.",
     "SELECT mo.manufacturer FROM bike b JOIN model mo ON mo.model_id = b.model_id "
     "GROUP BY mo.manufacturer ORDER BY COUNT(*) DESC LIMIT 1"),
    ("t2-04", 2, False, "For each station that at least one trip started from, give the station "
                        "name and the average distance of those trips, rounded to 2 decimal "
                        "places.",
     "SELECT s.name, ROUND(AVG(t.distance_km), 2) FROM trip t "
     "JOIN station s ON s.station_id = t.start_station_id GROUP BY s.station_id, s.name"),
    ("t2-05", 2, False, "How many trips ended at a station different from the one they started "
                        "at? Trips that did not end at any station do not count.",
     "SELECT COUNT(*) FROM trip "
     "WHERE end_station_id IS NOT NULL AND end_station_id <> start_station_id"),
    ("t2-06", 2, False, "For each model, give the model name and the number of maintenance "
                        "records for bikes of that model. Include models with no maintenance "
                        "records, with a count of 0.",
     "SELECT mo.name, COUNT(ma.maint_id) FROM model mo "
     "LEFT JOIN bike b ON b.model_id = mo.model_id "
     "LEFT JOIN maintenance ma ON ma.bike_id = b.bike_id GROUP BY mo.model_id, mo.name"),
    ("t2-07", 2, False, "Which cities have more than 2 stations? Give the city and the station "
                        "count.",
     "SELECT city, COUNT(*) FROM station GROUP BY city HAVING COUNT(*) > 2"),
    ("t2-08", 2, False, "For each station that has at least one bike with a maintenance record, "
                        "give the station name and the total resolved maintenance cost of bikes "
                        "assigned to it. Ignore unresolved records, which have no cost.",
     "SELECT s.name, SUM(ma.cost) FROM maintenance ma JOIN bike b ON b.bike_id = ma.bike_id "
     "JOIN station s ON s.station_id = b.station_id WHERE ma.cost IS NOT NULL "
     "GROUP BY s.station_id, s.name"),
    ("t2-09", 2, False, "How many members who joined in 2025 have made at least one payment?",
     "SELECT COUNT(DISTINCT m.member_id) FROM member m JOIN payment p ON p.member_id = m.member_id "
     "WHERE m.joined_on >= '2025-01-01' AND m.joined_on <= '2025-12-31'"),
    ("t2-10", 2, False, "For each payment method, give the method, the number of payments and "
                        "the total amount.",
     "SELECT method, COUNT(*), SUM(amount) FROM payment GROUP BY method"),
    ("t2-11", 2, True, "Give the model name and the total distance ridden for the 3 models with "
                       "the highest total distance, highest first.",
     "SELECT mo.name, SUM(t.distance_km) FROM trip t JOIN bike b ON b.bike_id = t.bike_id "
     "JOIN model mo ON mo.model_id = b.model_id GROUP BY mo.model_id, mo.name "
     "ORDER BY SUM(t.distance_km) DESC LIMIT 3"),
    ("t2-12", 2, False, "Give the member_id and total amount paid for every member whose total "
                        "payments exceed 300.",
     "SELECT member_id, SUM(amount) FROM payment GROUP BY member_id HAVING SUM(amount) > 300"),
    ("t2-13", 2, False, "How many trips started in each month of 2025? Give the month as YYYY-MM "
                        "and the number of trips.",
     "SELECT strftime('%Y-%m', started_at) AS m, COUNT(*) FROM trip "
     "WHERE started_at >= '2025-01-01' AND started_at < '2026-01-01' GROUP BY m"),
    ("t2-14", 2, False, "What is the average monthly fee of the plans held by members living in "
                        "Lille, rounded to 2 decimal places?",
     "SELECT ROUND(AVG(p.monthly_fee), 2) FROM member m JOIN plan p ON p.plan_id = m.plan_id "
     "WHERE m.city = 'Lille'"),
    ("t2-15", 2, False, "For each station, give the station name and the number of bikes "
                        "assigned to it whose status is 'retired'. Include stations with none, "
                        "with a count of 0.",
     "SELECT s.name, COUNT(b.bike_id) FROM station s "
     "LEFT JOIN bike b ON b.station_id = s.station_id AND b.status = 'retired' "
     "GROUP BY s.station_id, s.name"),

    # ---------------- Tier 3: subqueries, windows, NULL semantics (25) ----
    ("t3-01", 3, False, "Give the member_id and full name of every member who has referred at "
                        "least 3 other members, together with the number of people they referred.",
     "SELECT m.member_id, m.full_name, COUNT(r.member_id) FROM member m "
     "JOIN member r ON r.referred_by = m.member_id GROUP BY m.member_id, m.full_name "
     "HAVING COUNT(r.member_id) >= 3"),
    ("t3-02", 3, False, "For each station, give the station name, the number of trips that "
                        "started there and the number of trips that ended there. Include every "
                        "station.",
     "SELECT s.name, "
     "(SELECT COUNT(*) FROM trip t WHERE t.start_station_id = s.station_id), "
     "(SELECT COUNT(*) FROM trip t WHERE t.end_station_id = s.station_id) FROM station s"),
    ("t3-03", 3, False, "Give the member_id of every member whose average trip distance is "
                        "greater than the average trip distance across all trips.",
     "SELECT member_id FROM trip GROUP BY member_id "
     "HAVING AVG(distance_km) > (SELECT AVG(distance_km) FROM trip)"),
    ("t3-04", 3, True, "Which model has the highest total resolved maintenance cost per bike "
                       "owned? Give the model name and that ratio rounded to 2 decimal places. "
                       "Consider only models that have at least one maintenance record.",
     "WITH c AS (SELECT b.model_id, SUM(ma.cost) AS total FROM maintenance ma "
     "JOIN bike b ON b.bike_id = ma.bike_id WHERE ma.cost IS NOT NULL GROUP BY b.model_id), "
     "n AS (SELECT model_id, COUNT(*) AS fleet FROM bike GROUP BY model_id) "
     "SELECT mo.name, ROUND(c.total / n.fleet, 2) FROM c JOIN n ON n.model_id = c.model_id "
     "JOIN model mo ON mo.model_id = c.model_id ORDER BY c.total / n.fleet DESC LIMIT 1"),
    ("t3-05", 3, False, "For each plan, give the plan name and the percentage of its members who "
                        "have taken at least one trip, rounded to 1 decimal place. Include every "
                        "plan.",
     "SELECT p.name, ROUND(100.0 * COUNT(DISTINCT t.member_id) / COUNT(DISTINCT m.member_id), 1) "
     "FROM plan p JOIN member m ON m.plan_id = p.plan_id "
     "LEFT JOIN trip t ON t.member_id = m.member_id GROUP BY p.plan_id, p.name"),
    ("t3-06", 3, False, "Give the member_id of every member who has made at least one payment "
                        "but has never taken a trip.",
     "SELECT DISTINCT member_id FROM payment "
     "WHERE member_id NOT IN (SELECT member_id FROM trip)"),
    ("t3-07", 3, False, "For each station that has at least one resolved maintenance record on "
                        "an assigned bike, give the station name and the longest number of days "
                        "between a maintenance report and its resolution.",
     "SELECT s.name, MAX(julianday(ma.resolved_on) - julianday(ma.reported_on)) "
     "FROM maintenance ma JOIN bike b ON b.bike_id = ma.bike_id "
     "JOIN station s ON s.station_id = b.station_id WHERE ma.resolved_on IS NOT NULL "
     "GROUP BY s.station_id, s.name"),
    ("t3-08", 3, False, "Give the member_id and full name of every member who joined in 2024 and "
                        "whose first trip happened more than 120 days after they joined.",
     "SELECT m.member_id, m.full_name FROM member m JOIN trip t ON t.member_id = m.member_id "
     "WHERE m.joined_on >= '2024-01-01' AND m.joined_on <= '2024-12-31' "
     "GROUP BY m.member_id, m.full_name "
     "HAVING julianday(MIN(t.started_at)) - julianday(m.joined_on) > 120"),
    ("t3-09", 3, False, "Give the member_id of every member who took trips in at least 4 "
                        "different calendar months of 2025.",
     "SELECT member_id FROM trip WHERE started_at >= '2025-01-01' AND started_at < '2026-01-01' "
     "GROUP BY member_id HAVING COUNT(DISTINCT strftime('%Y-%m', started_at)) >= 4"),
    ("t3-10", 3, False, "Give the member_id of every member who has started trips from stations "
                        "in all 5 cities.",
     "SELECT t.member_id FROM trip t JOIN station s ON s.station_id = t.start_station_id "
     "GROUP BY t.member_id HAVING COUNT(DISTINCT s.city) = 5"),
    ("t3-11", 3, False, "For each model, give the model name and the percentage of its bikes "
                        "that have at least one maintenance record, rounded to 1 decimal place. "
                        "Include every model.",
     "SELECT mo.name, ROUND(100.0 * COUNT(DISTINCT CASE WHEN b.bike_id IN "
     "(SELECT bike_id FROM maintenance) THEN b.bike_id END) / COUNT(DISTINCT b.bike_id), 1) "
     "FROM model mo JOIN bike b ON b.model_id = mo.model_id GROUP BY mo.model_id, mo.name"),
    ("t3-12", 3, False, "Give the bike_id of every bike whose most recent maintenance record is "
                        "unresolved.",
     "SELECT bike_id FROM maintenance ma WHERE reported_on = "
     "(SELECT MAX(reported_on) FROM maintenance x WHERE x.bike_id = ma.bike_id) "
     "AND resolved_on IS NULL"),
    ("t3-13", 3, False, "Give the member_id of every member who has taken 2 or more trips on the "
                        "same calendar day.",
     "SELECT DISTINCT member_id FROM (SELECT member_id, date(started_at) AS d FROM trip "
     "GROUP BY member_id, date(started_at) HAVING COUNT(*) >= 2)"),
    ("t3-14", 3, False, "Give the member_id of the referred member and the member_id of their "
                        "referrer, for every pair where both live in the same city.",
     "SELECT b.member_id, a.member_id FROM member a JOIN member b ON b.referred_by = a.member_id "
     "WHERE a.city = b.city"),
    ("t3-15", 3, True, "For each city, give the city and the member_id of the member who has "
                       "started the most trips from stations in that city, with their trip count. "
                       "Break ties by the lower member_id. Order by city name.",
     "WITH c AS (SELECT s.city AS city, t.member_id AS mid, COUNT(*) AS n FROM trip t "
     "JOIN station s ON s.station_id = t.start_station_id GROUP BY s.city, t.member_id), "
     "r AS (SELECT city, mid, n, ROW_NUMBER() OVER "
     "(PARTITION BY city ORDER BY n DESC, mid ASC) AS rk FROM c) "
     "SELECT city, mid, n FROM r WHERE rk = 1 ORDER BY city"),
    ("t3-16", 3, True, "For each month of 2025, give the month as YYYY-MM, the number of trips, "
                       "and the change in trip count compared with the previous month. The first "
                       "month has no previous month, so its change is NULL. Order by month.",
     "WITH m AS (SELECT strftime('%Y-%m', started_at) AS mo, COUNT(*) AS n FROM trip "
     "WHERE started_at >= '2025-01-01' AND started_at < '2026-01-01' GROUP BY mo) "
     "SELECT mo, n, n - LAG(n) OVER (ORDER BY mo) FROM m ORDER BY mo"),
    ("t3-17", 3, False, "Give the trip_id of every trip whose distance is more than twice the "
                        "average distance of all trips starting from the same station.",
     "SELECT t.trip_id FROM trip t WHERE t.distance_km > 2 * "
     "(SELECT AVG(x.distance_km) FROM trip x WHERE x.start_station_id = t.start_station_id)"),
    ("t3-18", 3, False, "Give the station name and the share of trips starting there that ended "
                        "at a different station, as a percentage rounded to 1 decimal place. "
                        "Trips that did not end at any station count in the denominator but not "
                        "the numerator.",
     "SELECT s.name, ROUND(100.0 * SUM(CASE WHEN t.end_station_id IS NOT NULL "
     "AND t.end_station_id <> t.start_station_id THEN 1 ELSE 0 END) / COUNT(*), 1) "
     "FROM trip t JOIN station s ON s.station_id = t.start_station_id "
     "GROUP BY s.station_id, s.name"),
    ("t3-19", 3, True, "Give the 2 models with the most trips within each manufacturer: the "
                       "manufacturer, the model name and the trip count. Break ties by model "
                       "name ascending. Order by manufacturer then trip count descending.",
     "WITH c AS (SELECT mo.manufacturer AS man, mo.name AS nm, COUNT(*) AS n FROM trip t "
     "JOIN bike b ON b.bike_id = t.bike_id JOIN model mo ON mo.model_id = b.model_id "
     "GROUP BY mo.model_id, mo.manufacturer, mo.name), "
     "r AS (SELECT man, nm, n, ROW_NUMBER() OVER "
     "(PARTITION BY man ORDER BY n DESC, nm ASC) AS rk FROM c) "
     "SELECT man, nm, n FROM r WHERE rk <= 2 ORDER BY man, n DESC"),
    ("t3-20", 3, False, "Give the member_id and the number of days between their first and last "
                        "trip, for members where that gap is more than 500 days.",
     "SELECT member_id, julianday(MAX(started_at)) - julianday(MIN(started_at)) FROM trip "
     "GROUP BY member_id HAVING julianday(MAX(started_at)) - julianday(MIN(started_at)) > 500"),
    ("t3-21", 3, False, "Give the bike_id of every bike that has never been ridden by a member "
                        "on the Premium plan.",
     "SELECT bike_id FROM bike WHERE bike_id NOT IN "
     "(SELECT t.bike_id FROM trip t JOIN member m ON m.member_id = t.member_id "
     "JOIN plan p ON p.plan_id = m.plan_id WHERE p.name = 'Premium')"),
    ("t3-22", 3, True, "Which maintenance issue has the highest average resolution time in days? "
                       "Give the issue and that average rounded to 2 decimal places, considering "
                       "only resolved records.",
     "SELECT issue, ROUND(AVG(julianday(resolved_on) - julianday(reported_on)), 2) AS a "
     "FROM maintenance WHERE resolved_on IS NOT NULL GROUP BY issue ORDER BY a DESC LIMIT 1"),
    ("t3-23", 3, True, "Give the 5 busiest calendar days of 2025 by number of trips started: the "
                       "date as YYYY-MM-DD and the trip count, busiest first. Break ties by date "
                       "ascending.",
     "SELECT date(started_at) AS d, COUNT(*) AS n FROM trip "
     "WHERE started_at >= '2025-01-01' AND started_at < '2026-01-01' "
     "GROUP BY d ORDER BY n DESC, d ASC LIMIT 5"),
    ("t3-24", 3, False, "For each city, give the city and the total resolved maintenance cost of "
                        "bikes assigned to stations in that city. Include every city that has at "
                        "least one station, using 0 where there is no cost.",
     "SELECT s.city, COALESCE(SUM(ma.cost), 0) FROM station s "
     "LEFT JOIN bike b ON b.station_id = s.station_id "
     "LEFT JOIN maintenance ma ON ma.bike_id = b.bike_id AND ma.cost IS NOT NULL "
     "GROUP BY s.city"),
    ("t3-25", 3, False, "Give the station name of every station whose number of assigned bikes "
                        "is more than half its capacity.",
     "SELECT s.name FROM station s JOIN bike b ON b.station_id = s.station_id "
     "GROUP BY s.station_id, s.name, s.capacity HAVING COUNT(b.bike_id) > s.capacity / 2.0"),
]
