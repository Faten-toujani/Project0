CREATE TABLE bike (
    bike_id      INTEGER PRIMARY KEY,
    model_id     INTEGER NOT NULL REFERENCES model(model_id),
    station_id   INTEGER          REFERENCES station(station_id),
    status       TEXT    NOT NULL,
    purchased_on TEXT    NOT NULL
);

CREATE TABLE maintenance (
    maint_id    INTEGER PRIMARY KEY,
    bike_id     INTEGER NOT NULL REFERENCES bike(bike_id),
    reported_on TEXT    NOT NULL,
    resolved_on TEXT,
    cost        REAL,
    issue       TEXT    NOT NULL
);

CREATE TABLE member (
    member_id   INTEGER PRIMARY KEY,
    full_name   TEXT    NOT NULL,
    city        TEXT    NOT NULL,
    plan_id     INTEGER NOT NULL REFERENCES plan(plan_id),
    joined_on   TEXT    NOT NULL,
    referred_by INTEGER          REFERENCES member(member_id)
);

CREATE TABLE model (
    model_id     INTEGER PRIMARY KEY,
    name         TEXT    NOT NULL,
    manufacturer TEXT    NOT NULL,
    battery_wh   INTEGER,
    is_electric  INTEGER NOT NULL
);

CREATE TABLE payment (
    payment_id INTEGER PRIMARY KEY,
    member_id  INTEGER NOT NULL REFERENCES member(member_id),
    amount     REAL    NOT NULL,
    paid_on    TEXT    NOT NULL,
    method     TEXT    NOT NULL
);

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
