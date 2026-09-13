"""Build veloflux.db - a small e-bike rental network database.

Deterministic: same seed -> byte-identical data. Run from a clean clone.
"""
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

SEED = 496
OUT = Path("veloflux.db")

SCHEMA = """
CREATE TABLE plan (
    plan_id          INTEGER PRIMARY KEY,
    name             TEXT    NOT NULL,
    monthly_fee      REAL    NOT NULL,
    included_minutes INTEGER NOT NULL
);

CREATE TABLE station (
    station_id INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL,
    city       TEXT    NOT NULL,
    capacity   INTEGER NOT NULL,
    opened_on  TEXT    NOT NULL
);

CREATE TABLE model (
    model_id     INTEGER PRIMARY KEY,
    name         TEXT    NOT NULL,
    manufacturer TEXT    NOT NULL,
    battery_wh   INTEGER,
    is_electric  INTEGER NOT NULL
);

CREATE TABLE bike (
    bike_id      INTEGER PRIMARY KEY,
    model_id     INTEGER NOT NULL REFERENCES model(model_id),
    station_id   INTEGER          REFERENCES station(station_id),
    status       TEXT    NOT NULL,
    purchased_on TEXT    NOT NULL
);

CREATE TABLE member (
    member_id   INTEGER PRIMARY KEY,
    full_name   TEXT    NOT NULL,
    city        TEXT    NOT NULL,
    plan_id     INTEGER NOT NULL REFERENCES plan(plan_id),
    joined_on   TEXT    NOT NULL,
    referred_by INTEGER          REFERENCES member(member_id)
);

CREATE TABLE trip (
    trip_id          INTEGER PRIMARY KEY,
    bike_id          INTEGER NOT NULL REFERENCES bike(bike_id),
    member_id        INTEGER NOT NULL REFERENCES member(member_id),
    start_station_id INTEGER NOT NULL REFERENCES station(station_id),
    end_station_id   INTEGER          REFERENCES station(station_id),
    started_at       TEXT    NOT NULL,
    ended_at         TEXT    NOT NULL,
    distance_km      REAL    NOT NULL
);

CREATE TABLE payment (
    payment_id INTEGER PRIMARY KEY,
    member_id  INTEGER NOT NULL REFERENCES member(member_id),
    amount     REAL    NOT NULL,
    paid_on    TEXT    NOT NULL,
    method     TEXT    NOT NULL
);

CREATE TABLE maintenance (
    maint_id    INTEGER PRIMARY KEY,
    bike_id     INTEGER NOT NULL REFERENCES bike(bike_id),
    reported_on TEXT    NOT NULL,
    resolved_on TEXT,
    cost        REAL,
    issue       TEXT    NOT NULL
);
"""

PLANS = [
    (1, "Basic",    0.0,   0),
    (2, "Commuter", 14.5,  300),
    (3, "Premium",  29.0,  900),
    (4, "Student",  9.0,   240),
    (5, "Corporate", 45.0, 1800),
]

CITIES = ["Lyon", "Bordeaux", "Nantes", "Toulouse", "Lille"]

STATIONS = [
    (1,  "Gare Part-Dieu",   "Lyon",      40, "2022-03-14"),
    (2,  "Bellecour",        "Lyon",      32, "2022-03-14"),
    (3,  "Croix-Rousse",     "Lyon",      18, "2023-06-01"),
    (4,  "Quai des Chartrons", "Bordeaux", 28, "2022-09-20"),
    (5,  "Place Pey-Berland", "Bordeaux", 36, "2023-02-11"),
    (6,  "Victoire",         "Bordeaux",  22, "2024-05-03"),
    (7,  "Commerce",         "Nantes",    30, "2023-04-18"),
    (8,  "Ile de Versailles", "Nantes",   16, "2023-11-27"),
    (9,  "Capitole",         "Toulouse",  44, "2022-07-05"),
    (10, "Saint-Cyprien",    "Toulouse",  24, "2024-01-22"),
    (11, "Grand Place",      "Lille",     38, "2023-08-09"),
    (12, "Wazemmes",         "Lille",     20, "2025-02-17"),
]

MODELS = [
    (1, "Aria 300",   "Velotek",   360,  1),
    (2, "Aria 500",   "Velotek",   500,  1),
    (3, "Urbo Lite",  "Velotek",   None, 0),
    (4, "Kestrel E",  "Norvane",   420,  1),
    (5, "Kestrel S",  "Norvane",   None, 0),
    (6, "Fjord 7",    "Norvane",   630,  1),
    (7, "Mesa Cargo", "Ridgeline", 720,  1),
    (8, "Mesa Classic", "Ridgeline", None, 0),
]

FIRST = ["Amira", "Yanis", "Sofia", "Malik", "Ines", "Karim", "Lena", "Nabil",
         "Claire", "Omar", "Julie", "Tarek", "Manon", "Ryan", "Sarah", "Hugo",
         "Nora", "Adam", "Camille", "Ilyes", "Elodie", "Selim", "Maya", "Theo",
         "Lina", "Farid", "Chloe", "Nadir", "Alice", "Wassim"]
LAST = ["Bennani", "Moreau", "Chakroun", "Dubois", "Trabelsi", "Lambert",
        "Haddad", "Rousseau", "Ferchichi", "Girard", "Mansour", "Blanc",
        "Zouari", "Perrin", "Ayari"]

STATUSES = ["active", "active", "active", "active", "maintenance", "retired"]
METHODS = ["card", "card", "card", "transfer", "cash"]
ISSUES = ["flat tyre", "brake wear", "battery fault", "display error",
          "chain slip", "vandalism", "motor noise"]


def d(s):
    return date.fromisoformat(s)


def main():
    rng = random.Random(SEED)
    if OUT.exists():
        OUT.unlink()
    con = sqlite3.connect(OUT)
    con.executescript(SCHEMA)

    con.executemany("INSERT INTO plan VALUES (?,?,?,?)", PLANS)
    con.executemany("INSERT INTO station VALUES (?,?,?,?,?)", STATIONS)
    con.executemany("INSERT INTO model VALUES (?,?,?,?,?)", MODELS)

    # --- bikes -------------------------------------------------------
    bikes = []
    for bike_id in range(1, 201):
        model_id = rng.choice([1, 1, 2, 2, 3, 4, 4, 5, 6, 7, 8])
        # a handful of bikes sit in no station (in transit)
        station_id = rng.choice([s[0] for s in STATIONS] + [None, None])
        status = rng.choice(STATUSES)
        purchased = d("2022-01-10") + timedelta(days=rng.randint(0, 1200))
        bikes.append((bike_id, model_id, station_id, status, purchased.isoformat()))
    con.executemany("INSERT INTO bike VALUES (?,?,?,?,?)", bikes)

    # --- members -----------------------------------------------------
    members = []
    for member_id in range(1, 301):
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        city = rng.choice(CITIES)
        plan_id = rng.choice([1, 1, 2, 2, 2, 3, 3, 4, 4, 5])
        joined = d("2022-04-01") + timedelta(days=rng.randint(0, 1250))
        # ~35% were referred by an earlier member
        referred = rng.randint(1, member_id - 1) if member_id > 1 and rng.random() < 0.35 else None
        members.append((member_id, name, city, plan_id, joined.isoformat(), referred))
    con.executemany("INSERT INTO member VALUES (?,?,?,?,?,?)", members)

    joined_on = {m[0]: d(m[4]) for m in members}

    # --- trips -------------------------------------------------------
    # 40 members never ride; the rest ride a variable amount
    riders = [m[0] for m in members if m[0] % 7 != 0]
    trips = []
    for trip_id in range(1, 4001):
        member_id = rng.choice(riders)
        bike_id = rng.randint(1, 200)
        start = rng.choice([s[0] for s in STATIONS])
        # 4% of trips are abandoned away from any station
        end = None if rng.random() < 0.04 else rng.choice([s[0] for s in STATIONS])
        earliest = max(joined_on[member_id], d("2024-01-01"))
        span = (d("2026-08-31") - earliest).days
        if span <= 1:
            continue
        day = earliest + timedelta(days=rng.randint(0, span))
        hour = rng.randint(6, 21)
        minute = rng.randint(0, 59)
        dur = rng.randint(4, 95)
        started = f"{day.isoformat()} {hour:02d}:{minute:02d}:00"
        end_dt = hour * 60 + minute + dur
        ended = f"{day.isoformat()} {(end_dt // 60) % 24:02d}:{end_dt % 60:02d}:00"
        distance = round(dur * rng.uniform(0.12, 0.34), 2)
        trips.append((trip_id, bike_id, member_id, start, end, started, ended, distance))
    con.executemany("INSERT INTO trip VALUES (?,?,?,?,?,?,?,?)", trips)

    # --- payments ----------------------------------------------------
    fee = {p[0]: p[2] for p in PLANS}
    payments = []
    pid = 1
    for m in members:
        member_id, _, _, plan_id, joined, _ = m
        if fee[plan_id] == 0.0:
            continue
        n = rng.randint(1, 14)
        for k in range(n):
            paid = d(joined) + timedelta(days=30 * k + rng.randint(0, 4))
            if paid > d("2026-09-01"):
                break
            amount = round(fee[plan_id] + rng.choice([0, 0, 0, 2.5, 5.0]), 2)
            payments.append((pid, member_id, amount, paid.isoformat(), rng.choice(METHODS)))
            pid += 1
    con.executemany("INSERT INTO payment VALUES (?,?,?,?,?)", payments)

    # --- maintenance -------------------------------------------------
    maints = []
    for maint_id in range(1, 261):
        bike_id = rng.randint(1, 200)
        reported = d("2024-02-01") + timedelta(days=rng.randint(0, 940))
        if rng.random() < 0.22:                       # still open
            resolved, cost = None, None
        else:
            resolved = (reported + timedelta(days=rng.randint(1, 45))).isoformat()
            cost = round(rng.uniform(12, 340), 2)
        maints.append((maint_id, bike_id, reported.isoformat(), resolved, cost,
                       rng.choice(ISSUES)))
    con.executemany("INSERT INTO maintenance VALUES (?,?,?,?,?,?)", maints)

    con.commit()
    for t in ["plan", "station", "model", "bike", "member", "trip", "payment", "maintenance"]:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t:14s} {n:5d}")
    con.close()


if __name__ == "__main__":
    main()
