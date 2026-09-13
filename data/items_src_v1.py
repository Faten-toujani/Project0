# (id, tier, order_matters, question, gold_sql)
# order_matters=True  -> row order is part of the answer (ORDER BY in the question)
# order_matters=False -> rows are compared as an unordered multiset

DEV = [
    ("d-01", 1, False, "How many stations are there?",
     "SELECT COUNT(*) FROM station"),
    ("d-02", 1, False, "List the names of all plans.",
     "SELECT name FROM plan"),
    ("d-03", 1, False, "How many bikes have the status 'active'?",
     "SELECT COUNT(*) FROM bike WHERE status = 'active'"),
    ("d-04", 1, False, "What is the total number of trips?",
     "SELECT COUNT(*) FROM trip"),
    ("d-05", 1, False, "Give the name and city of every station with a capacity of at least 35.",
     "SELECT name, city FROM station WHERE capacity >= 35"),
    ("d-06", 2, False, "For each city, how many stations are there? Give the city and the count.",
     "SELECT city, COUNT(*) FROM station GROUP BY city"),
    ("d-07", 2, False, "Give the member_id and full name of every member on the Student plan.",
     "SELECT m.member_id, m.full_name FROM member m JOIN plan p ON p.plan_id = m.plan_id "
     "WHERE p.name = 'Student'"),
    ("d-08", 1, False, "What is the average station capacity, rounded to 2 decimal places?",
     "SELECT ROUND(AVG(capacity), 2) FROM station"),
    ("d-09", 1, False, "How many maintenance records have the issue 'battery fault'?",
     "SELECT COUNT(*) FROM maintenance WHERE issue = 'battery fault'"),
    ("d-10", 2, False, "Give the model name and manufacturer of every electric model with a "
                       "battery of more than 500 Wh.",
     "SELECT name, manufacturer FROM model WHERE is_electric = 1 AND battery_wh > 500"),
]

TEST = [
    # ---------------- Tier 1: single table --------------------------------
    ("t1-01", 1, True, "List the names of all stations in Lyon, in alphabetical order.",
     "SELECT name FROM station WHERE city = 'Lyon' ORDER BY name"),
    ("t1-02", 1, False, "How many bikes have the status 'maintenance'?",
     "SELECT COUNT(*) FROM bike WHERE status = 'maintenance'"),
    ("t1-03", 1, False, "Give the plan name and monthly fee of every plan with a monthly fee above 20.",
     "SELECT name, monthly_fee FROM plan WHERE monthly_fee > 20"),
    ("t1-04", 1, False, "List the names of all bike models that are not electric.",
     "SELECT name FROM model WHERE is_electric = 0"),
    ("t1-05", 1, False, "How many members joined in 2025?",
     "SELECT COUNT(*) FROM member WHERE joined_on >= '2025-01-01' AND joined_on <= '2025-12-31'"),
    ("t1-06", 1, True, "What is the name and capacity of the station with the largest capacity?",
     "SELECT name, capacity FROM station ORDER BY capacity DESC LIMIT 1"),
    ("t1-07", 1, False, "What is the total amount of all payments?",
     "SELECT SUM(amount) FROM payment"),
    ("t1-08", 1, False, "List the distinct payment methods that appear in the payment table.",
     "SELECT DISTINCT method FROM payment"),
    ("t1-09", 1, False, "How many bikes were purchased before 1 January 2024?",
     "SELECT COUNT(*) FROM bike WHERE purchased_on < '2024-01-01'"),
    ("t1-10", 1, False, "How many members live in Toulouse?",
     "SELECT COUNT(*) FROM member WHERE city = 'Toulouse'"),
    ("t1-11", 1, False, "What is the average trip distance in km, rounded to 2 decimal places?",
     "SELECT ROUND(AVG(distance_km), 2) FROM trip"),
    ("t1-12", 1, False, "How many maintenance records have not been resolved yet?",
     "SELECT COUNT(*) FROM maintenance WHERE resolved_on IS NULL"),
    ("t1-13", 1, True, "List the 3 cheapest plans by monthly fee, giving the plan name and the fee.",
     "SELECT name, monthly_fee FROM plan ORDER BY monthly_fee ASC LIMIT 3"),
    ("t1-14", 1, False, "Give the name and opening date of every station that opened in 2023.",
     "SELECT name, opened_on FROM station "
     "WHERE opened_on >= '2023-01-01' AND opened_on <= '2023-12-31'"),
    ("t1-15", 1, False, "How many bike models does the manufacturer Norvane have?",
     "SELECT COUNT(*) FROM model WHERE manufacturer = 'Norvane'"),
    ("t1-16", 1, False, "What is the largest battery capacity in Wh among electric models?",
     "SELECT MAX(battery_wh) FROM model WHERE is_electric = 1"),
    ("t1-17", 1, False, "How many trips covered more than 15 km?",
     "SELECT COUNT(*) FROM trip WHERE distance_km > 15"),
    ("t1-18", 1, False, "How many members were not referred by anyone?",
     "SELECT COUNT(*) FROM member WHERE referred_by IS NULL"),
    ("t1-19", 1, False, "What is the total amount paid with the method 'card'?",
     "SELECT SUM(amount) FROM payment WHERE method = 'card'"),
    ("t1-20", 1, True, "Give the trip_id and distance of the 5 longest trips by distance, longest first.",
     "SELECT trip_id, distance_km FROM trip ORDER BY distance_km DESC, trip_id ASC LIMIT 5"),

    # ---------------- Tier 2: joins, grouping, aggregates -----------------
    ("t2-01", 2, False, "For each station, give the station name and the number of bikes currently "
                        "assigned to it. Include stations that have no bikes.",
     "SELECT s.name, COUNT(b.bike_id) FROM station s "
     "LEFT JOIN bike b ON b.station_id = s.station_id GROUP BY s.station_id, s.name"),
    ("t2-02", 2, False, "For each plan name, give the total amount paid by the members on that plan.",
     "SELECT p.name, SUM(pay.amount) FROM plan p "
     "JOIN member m ON m.plan_id = p.plan_id "
     "JOIN payment pay ON pay.member_id = m.member_id GROUP BY p.plan_id, p.name"),
    ("t2-03", 2, True, "Which manufacturer has the most bikes in the fleet? Give the manufacturer name.",
     "SELECT mo.manufacturer FROM bike b JOIN model mo ON mo.model_id = b.model_id "
     "GROUP BY mo.manufacturer ORDER BY COUNT(*) DESC LIMIT 1"),
    ("t2-04", 2, False, "For each station that trips start from, give the station name and the "
                        "average trip distance rounded to 2 decimal places.",
     "SELECT s.name, ROUND(AVG(t.distance_km), 2) FROM trip t "
     "JOIN station s ON s.station_id = t.start_station_id GROUP BY s.station_id, s.name"),
    ("t2-05", 2, False, "How many trips ended at a station different from the one they started at?",
     "SELECT COUNT(*) FROM trip "
     "WHERE end_station_id IS NOT NULL AND end_station_id <> start_station_id"),
    ("t2-06", 2, False, "For each model name, give the number of maintenance records recorded for "
                        "bikes of that model.",
     "SELECT mo.name, COUNT(*) FROM maintenance ma JOIN bike b ON b.bike_id = ma.bike_id "
     "JOIN model mo ON mo.model_id = b.model_id GROUP BY mo.model_id, mo.name"),
    ("t2-07", 2, False, "Which cities have more than 2 stations? Give the city and the station count.",
     "SELECT city, COUNT(*) FROM station GROUP BY city HAVING COUNT(*) > 2"),
    ("t2-08", 2, False, "Give the station name and the total maintenance cost for bikes assigned to "
                        "that station.",
     "SELECT s.name, SUM(ma.cost) FROM maintenance ma JOIN bike b ON b.bike_id = ma.bike_id "
     "JOIN station s ON s.station_id = b.station_id GROUP BY s.station_id, s.name"),
    ("t2-09", 2, False, "How many members who joined in 2025 have made at least one payment?",
     "SELECT COUNT(DISTINCT m.member_id) FROM member m JOIN payment p ON p.member_id = m.member_id "
     "WHERE m.joined_on >= '2025-01-01' AND m.joined_on <= '2025-12-31'"),
    ("t2-10", 2, True, "Which station is the most common starting point for trips? Give the station name.",
     "SELECT s.name FROM trip t JOIN station s ON s.station_id = t.start_station_id "
     "GROUP BY s.station_id, s.name ORDER BY COUNT(*) DESC LIMIT 1"),
    ("t2-11", 2, False, "For each payment method, give the method, the number of payments and the "
                        "total amount.",
     "SELECT method, COUNT(*), SUM(amount) FROM payment GROUP BY method"),
    ("t2-12", 2, True, "Give the model name and the total distance ridden for the 3 models with the "
                       "highest total distance, highest first.",
     "SELECT mo.name, SUM(t.distance_km) FROM trip t JOIN bike b ON b.bike_id = t.bike_id "
     "JOIN model mo ON mo.model_id = b.model_id GROUP BY mo.model_id, mo.name "
     "ORDER BY SUM(t.distance_km) DESC LIMIT 3"),
    ("t2-13", 2, False, "For each city, give the total number of trips that started from a station "
                        "in that city.",
     "SELECT s.city, COUNT(*) FROM trip t JOIN station s ON s.station_id = t.start_station_id "
     "GROUP BY s.city"),
    ("t2-14", 2, False, "Give the member_id and total amount paid for every member whose total "
                        "payments exceed 300.",
     "SELECT member_id, SUM(amount) FROM payment GROUP BY member_id HAVING SUM(amount) > 300"),
    ("t2-15", 2, False, "How many trips started in each month of 2025? Give the month as YYYY-MM "
                        "and the number of trips.",
     "SELECT strftime('%Y-%m', started_at) AS m, COUNT(*) FROM trip "
     "WHERE started_at >= '2025-01-01' AND started_at < '2026-01-01' GROUP BY m"),
    ("t2-16", 2, False, "Give the name and city of every station that has at least one bike with "
                        "the status 'maintenance'.",
     "SELECT DISTINCT s.name, s.city FROM station s JOIN bike b ON b.station_id = s.station_id "
     "WHERE b.status = 'maintenance'"),
    ("t2-17", 2, False, "What is the average monthly fee of the plans held by members living in "
                        "Lille, rounded to 2 decimal places?",
     "SELECT ROUND(AVG(p.monthly_fee), 2) FROM member m JOIN plan p ON p.plan_id = m.plan_id "
     "WHERE m.city = 'Lille'"),
    ("t2-18", 2, False, "Give the member_id and the number of trips for every member who has taken "
                        "more than 25 trips.",
     "SELECT member_id, COUNT(*) FROM trip GROUP BY member_id HAVING COUNT(*) > 25"),
    ("t2-19", 2, False, "For each manufacturer, give the manufacturer and the number of bikes with "
                        "the status 'retired'.",
     "SELECT mo.manufacturer, COUNT(*) FROM bike b JOIN model mo ON mo.model_id = b.model_id "
     "WHERE b.status = 'retired' GROUP BY mo.manufacturer"),
    ("t2-20", 2, False, "Give the issue and the number of maintenance records for each issue that "
                        "appears more than 30 times.",
     "SELECT issue, COUNT(*) FROM maintenance GROUP BY issue HAVING COUNT(*) > 30"),

    # ---------------- Tier 3: subqueries, NULL semantics, self-joins ------
    ("t3-01", 3, False, "Give the member_id and full name of every member who has referred at least "
                        "3 other members, together with the number of people they referred.",
     "SELECT m.member_id, m.full_name, COUNT(r.member_id) FROM member m "
     "JOIN member r ON r.referred_by = m.member_id GROUP BY m.member_id, m.full_name "
     "HAVING COUNT(r.member_id) >= 3"),
    ("t3-02", 3, False, "For each station, give the station name, the number of trips that started "
                        "there and the number of trips that ended there.",
     "SELECT s.name, "
     "(SELECT COUNT(*) FROM trip t WHERE t.start_station_id = s.station_id), "
     "(SELECT COUNT(*) FROM trip t WHERE t.end_station_id = s.station_id) "
     "FROM station s"),
    ("t3-03", 3, False, "Give the member_id of every member whose average trip distance is greater "
                        "than the average trip distance across all trips.",
     "SELECT member_id FROM trip GROUP BY member_id "
     "HAVING AVG(distance_km) > (SELECT AVG(distance_km) FROM trip)"),
    ("t3-04", 3, True, "Which model has the highest total maintenance cost per bike owned? Give the "
                       "model name and that ratio rounded to 2 decimal places.",
     "WITH c AS (SELECT b.model_id, SUM(ma.cost) AS total FROM maintenance ma "
     "JOIN bike b ON b.bike_id = ma.bike_id GROUP BY b.model_id), "
     "n AS (SELECT model_id, COUNT(*) AS fleet FROM bike GROUP BY model_id) "
     "SELECT mo.name, ROUND(c.total / n.fleet, 2) FROM c JOIN n ON n.model_id = c.model_id "
     "JOIN model mo ON mo.model_id = c.model_id ORDER BY c.total / n.fleet DESC LIMIT 1"),
    ("t3-05", 3, False, "Give the bike_id of every bike that has more than one unresolved "
                        "maintenance record.",
     "SELECT bike_id FROM maintenance WHERE resolved_on IS NULL GROUP BY bike_id "
     "HAVING COUNT(*) > 1"),
    ("t3-06", 3, False, "For each plan, give the plan name and the percentage of its members who "
                        "have taken at least one trip, rounded to 1 decimal place.",
     "SELECT p.name, ROUND(100.0 * COUNT(DISTINCT t.member_id) / COUNT(DISTINCT m.member_id), 1) "
     "FROM plan p JOIN member m ON m.plan_id = p.plan_id "
     "LEFT JOIN trip t ON t.member_id = m.member_id GROUP BY p.plan_id, p.name"),
    ("t3-07", 3, True, "What is the name and capacity of the station with the second-largest capacity?",
     "SELECT name, capacity FROM station ORDER BY capacity DESC LIMIT 1 OFFSET 1"),
    ("t3-08", 3, False, "Give the member_id of every member who has made at least one payment but "
                        "has never taken a trip.",
     "SELECT DISTINCT member_id FROM payment "
     "WHERE member_id NOT IN (SELECT member_id FROM trip)"),
    ("t3-09", 3, False, "For each station, give the station name and the longest number of days "
                        "between a maintenance report and its resolution, for bikes assigned to "
                        "that station. Ignore records that are not resolved.",
     "SELECT s.name, MAX(julianday(ma.resolved_on) - julianday(ma.reported_on)) "
     "FROM maintenance ma JOIN bike b ON b.bike_id = ma.bike_id "
     "JOIN station s ON s.station_id = b.station_id WHERE ma.resolved_on IS NOT NULL "
     "GROUP BY s.station_id, s.name"),
    ("t3-10", 3, False, "Give the member_id and full name of every member who joined in 2024 and "
                        "whose first trip happened more than 120 days after they joined.",
     "SELECT m.member_id, m.full_name FROM member m JOIN trip t ON t.member_id = m.member_id "
     "WHERE m.joined_on >= '2024-01-01' AND m.joined_on <= '2024-12-31' "
     "GROUP BY m.member_id, m.full_name "
     "HAVING julianday(MIN(t.started_at)) - julianday(m.joined_on) > 120"),
]
