#!/usr/bin/env python3
"""Bulk import all data into Supabase using a SINGLE psycopg2 connection.

Avoids connection pool exhaustion by bypassing the ORM entirely.
Uses COPY for bulk inserts where possible, parameterized INSERTs otherwise.
"""
import csv
import os
import sys
import time
from pathlib import Path

import psycopg2
import psycopg2.extras

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:ZWxalXIA0J0eqp3R@db.rlzfrdyznnjcidfvmumw.supabase.co:5432/postgres",
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW = PROJECT_ROOT / "data" / "raw"


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def import_locations(cur, conn):
    """Import location hierarchy: districts → talukas → gram_panchayats → villages."""
    t0 = time.time()
    print("[locations] Importing location hierarchy...", flush=True)

    rows = read_csv(RAW / "locations" / "maharashtra_lgd_villages.csv")

    # Collect unique entities
    districts = {}
    talukas = {}
    gps = {}
    for r in rows:
        d = r["district_name"]
        if d not in districts:
            districts[d] = r.get("state", "Maharashtra")
        t = r["taluka_name"]
        if (d, t) not in talukas:
            talukas[(d, t)] = r.get("lgd_code", "")
        gp = r["gram_panchayat_name"]
        if (d, t, gp) not in gps:
            gps[(d, t, gp)] = ""

    # Insert districts
    cur.execute("SELECT name FROM districts")
    existing = {row[0] for row in cur.fetchall()}
    new_districts = {d: s for d, s in districts.items() if d not in existing}
    if new_districts:
        vals = [(d, s) for d, s in new_districts.items()]
        psycopg2.extras.execute_batch(
            cur,
            "INSERT INTO districts (id, name, state) VALUES (gen_random_uuid(), %s, %s) ON CONFLICT DO NOTHING",
            vals,
            page_size=100,
        )
        conn.commit()
    print(f"  districts: {len(new_districts)} new (of {len(districts)} total)", flush=True)

    # Build district_id lookup
    cur.execute("SELECT id, name FROM districts")
    dist_id = {name: uid for uid, name in cur.fetchall()}

    # Insert talukas
    cur.execute("SELECT name FROM talukas")
    existing = {row[0] for row in cur.fetchall()}
    new_talukas = [(t, dist_id[d]) for (d, t) in talukas if t not in existing and d in dist_id]
    if new_talukas:
        psycopg2.extras.execute_batch(
            cur,
            "INSERT INTO talukas (id, name, district_id) VALUES (gen_random_uuid(), %s, %s) ON CONFLICT DO NOTHING",
            new_talukas,
            page_size=100,
        )
        conn.commit()
    print(f"  talukas: {len(new_talukas)} new (of {len(talukas)} total)", flush=True)

    # Build taluka_id lookup
    cur.execute("SELECT t.id, t.name, d.name FROM talukas t JOIN districts d ON t.district_id = d.id")
    taluka_id = {(tname, dname): uid for uid, tname, dname in cur.fetchall()}

    # Insert gram_panchayats
    cur.execute("SELECT name FROM gram_panchayats")
    existing = {row[0] for row in cur.fetchall()}
    new_gps = []
    for (d, t, gp) in gps:
        if gp not in existing and (t, d) in taluka_id:
            new_gps.append((gp, taluka_id[(t, d)], dist_id.get(d)))
    if new_gps:
        psycopg2.extras.execute_batch(
            cur,
            "INSERT INTO gram_panchayats (id, name, taluka_id, district_id) VALUES (gen_random_uuid(), %s, %s, %s) ON CONFLICT DO NOTHING",
            new_gps,
            page_size=100,
        )
        conn.commit()
    print(f"  gram_panchayats: {len(new_gps)} new (of {len(gps)} total)", flush=True)

    # Build GP lookup
    cur.execute(
        "SELECT g.id, g.name, t.name, d.name FROM gram_panchayats g "
        "JOIN talukas t ON g.taluka_id = t.id JOIN districts d ON g.district_id = d.id"
    )
    gp_id = {(gpname, tname, dname): uid for uid, gpname, tname, dname in cur.fetchall()}

    # Insert villages
    cur.execute("SELECT name FROM villages")
    existing = {row[0] for row in cur.fetchall()}
    new_villages = []
    for r in rows:
        v = r["village_name"]
        if v in existing:
            continue
        d, t, gp = r["district_name"], r["taluka_name"], r["gram_panchayat_name"]
        gp_uid = gp_id.get((gp, t, d))
        d_uid = dist_id.get(d)
        t_uid = taluka_id.get((t, d))
        if not all([gp_uid, d_uid, t_uid]):
            continue
        lat = float(r["latitude"]) if r.get("latitude") else None
        lng = float(r["longitude"]) if r.get("longitude") else None
        geom = f"SRID=4326;POINT({lng} {lat})" if lat and lng else None
        new_villages.append((v, d_uid, t_uid, gp_uid, r.get("lgd_code"), r.get("pin_code"), lat, lng, geom))
    if new_villages:
        psycopg2.extras.execute_batch(
            cur,
            """INSERT INTO villages (id, name, district_id, taluka_id, gram_panchayat_id, lgd_code, pin_code, latitude, longitude, geom)
               VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
            new_villages,
            page_size=100,
        )
        conn.commit()
    print(f"  villages: {len(new_villages)} new", flush=True)
    print(f"  [locations] Done in {time.time() - t0:.1f}s\n", flush=True)


def import_population(cur, conn):
    t0 = time.time()
    print("[population] Importing...", flush=True)
    rows = read_csv(RAW / "population" / "maharashtra_census_2011.csv")

    # Build village lookup
    cur.execute("SELECT v.id, v.name, d.name, t.name FROM villages v JOIN districts d ON v.district_id = d.id JOIN talukas t ON v.taluka_id = t.id")
    vid = {(r[1], r[2], r[3]): r[0] for r in cur.fetchall()}

    # Check existing
    cur.execute("SELECT location_id, year FROM population")
    existing = {(r[0], r[1]) for r in cur.fetchall()}

    vals = []
    for r in rows:
        v_id = vid.get((r["village_name"], r["district_name"], r["taluka_name"]))
        if not v_id or (v_id, int(r["year"])) in existing:
            continue
        vals.append((
            v_id, int(r["year"]),
            int(r["population_total"]) if r.get("population_total") else None,
            int(r["male_population"]) if r.get("male_population") else None,
            int(r["female_population"]) if r.get("female_population") else None,
            int(r["households"]) if r.get("households") else None,
            int(r["working_population"]) if r.get("working_population") else None,
            float(r["literacy_rate"]) if r.get("literacy_rate") else None,
        ))
    if vals:
        psycopg2.extras.execute_batch(
            cur,
            """INSERT INTO population (id, location_id, year, population_total, male_population, female_population, households, working_population, literacy_rate, source)
               VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, 'Census of India')""",
            vals, page_size=100,
        )
        conn.commit()
    print(f"  {len(vals)} rows imported", flush=True)
    print(f"  [population] Done in {time.time() - t0:.1f}s\n", flush=True)


def import_agriculture(cur, conn):
    t0 = time.time()
    print("[agriculture] Importing...", flush=True)
    rows = read_csv(RAW / "agriculture" / "maharashtra_agriculture_stats.csv")

    cur.execute("SELECT v.id, v.name, d.name, t.name FROM villages v JOIN districts d ON v.district_id = d.id JOIN talukas t ON v.taluka_id = t.id")
    vid = {(r[1], r[2], r[3]): r[0] for r in cur.fetchall()}

    cur.execute("SELECT location_id, crop_name, year, season FROM agriculture")
    existing = {(r[0], r[1], r[2], r[3]) for r in cur.fetchall()}

    vals = []
    for r in rows:
        v_id = vid.get((r["village_name"], r["district_name"], r["taluka_name"]))
        year = int(r["year"])
        season = r["season"]
        crop = r["crop_name"]
        if not v_id or (v_id, crop, year, season) in existing:
            continue
        vals.append((
            v_id, crop, r.get("crop_category"),
            float(r["cultivated_area"]) if r.get("cultivated_area") else None,
            float(r["production"]) if r.get("production") else None,
            r.get("production_unit"),
            float(r["irrigated_area"]) if r.get("irrigated_area") else None,
            year, season,
        ))
    if vals:
        psycopg2.extras.execute_batch(
            cur,
            """INSERT INTO agriculture (id, location_id, crop_name, crop_category, cultivated_area, production, production_unit, irrigated_area, year, season, source)
               VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Government Data')""",
            vals, page_size=100,
        )
        conn.commit()
    print(f"  {len(vals)} rows imported", flush=True)
    print(f"  [agriculture] Done in {time.time() - t0:.1f}s\n", flush=True)


def import_livestock(cur, conn):
    t0 = time.time()
    print("[livestock] Importing...", flush=True)
    rows = read_csv(RAW / "livestock" / "maharashtra_livestock_2019.csv")

    cur.execute("SELECT v.id, v.name, d.name, t.name FROM villages v JOIN districts d ON v.district_id = d.id JOIN talukas t ON v.taluka_id = t.id")
    vid = {(r[1], r[2], r[3]): r[0] for r in cur.fetchall()}

    cur.execute("SELECT location_id, animal_type, year FROM livestock")
    existing = {(r[0], r[1], r[2]) for r in cur.fetchall()}

    vals = []
    for r in rows:
        v_id = vid.get((r["village_name"], r["district_name"], r["taluka_name"]))
        year = int(r["year"])
        animal = r["animal_type"]
        if not v_id or (v_id, animal, year) in existing:
            continue
        vals.append((
            v_id, animal,
            int(r["animal_count"]) if r.get("animal_count") else None,
            float(r["milk_production"]) if r.get("milk_production") else None,
            r.get("milk_production_unit"),
            year,
        ))
    if vals:
        psycopg2.extras.execute_batch(
            cur,
            """INSERT INTO livestock (id, location_id, animal_type, animal_count, milk_production, milk_production_unit, year, source)
               VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, 'Government Data')""",
            vals, page_size=100,
        )
        conn.commit()
    print(f"  {len(vals)} rows imported", flush=True)
    print(f"  [livestock] Done in {time.time() - t0:.1f}s\n", flush=True)


def import_markets(cur, conn):
    t0 = time.time()
    print("[markets] Importing...", flush=True)
    rows = read_csv(RAW / "markets" / "maharashtra_apmc_mandis.csv")

    cur.execute("SELECT v.id, v.name, d.name, t.name FROM villages v JOIN districts d ON v.district_id = d.id JOIN talukas t ON v.taluka_id = t.id")
    vid = {(r[1], r[2], r[3]): r[0] for r in cur.fetchall()}

    cur.execute("SELECT LOWER(name) FROM markets")
    existing = {r[0] for r in cur.fetchall()}

    vals = []
    for r in rows:
        name = r["market_name"]
        if name.lower() in existing:
            continue
        v_id = vid.get((r["village_name"], r["district_name"], r["taluka_name"]))
        lat = float(r["latitude"]) if r.get("latitude") else None
        lng = float(r["longitude"]) if r.get("longitude") else None
        geom = f"SRID=4326;POINT({lng} {lat})" if lat and lng else None
        vals.append((name, r.get("market_type"), v_id, lat, lng, geom))
    if vals:
        psycopg2.extras.execute_batch(
            cur,
            """INSERT INTO markets (id, name, market_type, location_id, latitude, longitude, geog, source)
               VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, 'Government Registries')""",
            vals, page_size=100,
        )
        conn.commit()
    print(f"  {len(vals)} rows imported", flush=True)
    print(f"  [markets] Done in {time.time() - t0:.1f}s\n", flush=True)


def import_businesses(cur, conn):
    t0 = time.time()
    print("[businesses] Importing...", flush=True)
    rows = read_csv(RAW / "businesses" / "maharashtra_msme_clusters.csv")

    cur.execute("SELECT v.id, v.name, d.name, t.name FROM villages v JOIN districts d ON v.district_id = d.id JOIN talukas t ON v.taluka_id = t.id")
    vid = {(r[1], r[2], r[3]): r[0] for r in cur.fetchall()}

    # Resolve categories
    cur.execute("SELECT id, name FROM business_categories")
    cat_id = {name: uid for uid, name in cur.fetchall()}

    cur.execute("SELECT LOWER(name), district, village FROM businesses")
    existing = {(r[0], r[1] or "", r[2] or "") for r in cur.fetchall()}

    vals = []
    for r in rows:
        name = r["business_name"]
        dist = r.get("district_name", "")
        vill = r.get("village_name", "")
        if (name.lower(), dist, vill) in existing:
            continue
        v_id = vid.get((vill, dist, r.get("taluka_name", "")))
        cat = r.get("category_name")
        cat_uid = cat_id.get(cat)
        # Create category if missing
        if cat and not cat_uid:
            cur.execute("INSERT INTO business_categories (id, name) VALUES (gen_random_uuid(), %s) RETURNING id", (cat,))
            cat_uid = cur.fetchone()[0]
            cat_id[cat] = cat_uid
            conn.commit()
        lat = float(r["latitude"]) if r.get("latitude") else None
        lng = float(r["longitude"]) if r.get("longitude") else None
        geom = f"SRID=4326;POINT({lng} {lat})" if lat and lng else None
        vals.append((name, cat_uid, v_id, dist, r.get("taluka_name"), vill, r.get("address"), lat, lng, geom))
    if vals:
        psycopg2.extras.execute_batch(
            cur,
            """INSERT INTO businesses (id, name, business_category_id, location_id, district, taluka, village, address, latitude, longitude, geom, source)
               VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'MSME Registry')""",
            vals, page_size=100,
        )
        conn.commit()
    print(f"  {len(vals)} rows imported", flush=True)
    print(f"  [businesses] Done in {time.time() - t0:.1f}s\n", flush=True)


def import_market_prices(cur, conn):
    t0 = time.time()
    print("[market_prices] Importing...", flush=True)
    rows = read_csv(RAW / "market_prices" / "maharashtra_daily_prices.csv")

    cur.execute("SELECT id, LOWER(name) FROM markets")
    mkt_id = {name: uid for uid, name in cur.fetchall()}

    cur.execute("SELECT market_id, commodity, recorded_date FROM market_prices")
    existing = {(r[0], r[1], r[2]) for r in cur.fetchall()}

    vals = []
    for r in rows:
        mkt_name = r["market_name"].lower()
        mkt = mkt_id.get(mkt_name)
        commodity = r["commodity"]
        date = r["recorded_date"]
        if mkt and (mkt, commodity, date) in existing:
            continue
        vals.append((
            mkt, commodity, r.get("commodity_variety"), r.get("unit"),
            float(r["min_price"]) if r.get("min_price") else None,
            float(r["max_price"]) if r.get("max_price") else None,
            float(r["modal_price"]) if r.get("modal_price") else None,
            float(r["arrival_quantity"]) if r.get("arrival_quantity") else None,
            r.get("arrival_unit"),
            date,
        ))
    if vals:
        psycopg2.extras.execute_batch(
            cur,
            """INSERT INTO market_prices (id, market_id, commodity, commodity_variety, unit, min_price, max_price, modal_price, arrival_quantity, arrival_unit, recorded_date, source)
               VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Agmarknet')""",
            vals, page_size=100,
        )
        conn.commit()
    print(f"  {len(vals)} rows imported", flush=True)
    print(f"  [market_prices] Done in {time.time() - t0:.1f}s\n", flush=True)


def import_weather(cur, conn):
    t0 = time.time()
    print("[weather] Importing...", flush=True)
    rows = read_csv(RAW / "weather" / "maharashtra_imd_weather.csv")

    cur.execute("SELECT v.id, v.name, d.name, t.name FROM villages v JOIN districts d ON v.district_id = d.id JOIN talukas t ON v.taluka_id = t.id")
    vid = {(r[1], r[2], r[3]): r[0] for r in cur.fetchall()}

    cur.execute("SELECT location_id, date FROM weather")
    existing = {(r[0], r[1]) for r in cur.fetchall()}

    vals = []
    for r in rows:
        v_id = vid.get((r["village_name"], r["district_name"], r["taluka_name"]))
        date = r["date"]
        if (v_id, date) in existing:
            continue
        vals.append((
            v_id, date,
            float(r["rainfall_mm"]) if r.get("rainfall_mm") else None,
            float(r["temperature_min"]) if r.get("temperature_min") else None,
            float(r["temperature_max"]) if r.get("temperature_max") else None,
            r.get("drought_indicator", "False").lower() == "true",
        ))
    if vals:
        psycopg2.extras.execute_batch(
            cur,
            """INSERT INTO weather (id, location_id, date, rainfall_mm, temperature_min, temperature_max, drought_indicator, source)
               VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, 'IMD')""",
            vals, page_size=100,
        )
        conn.commit()
    print(f"  {len(vals)} rows imported", flush=True)
    print(f"  [weather] Done in {time.time() - t0:.1f}s\n", flush=True)


def main():
    t0 = time.time()
    print("=" * 60, flush=True)
    print("BULK IMPORT TO SUPABASE (single connection)", flush=True)
    print("=" * 60, flush=True)

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        import_locations(cur, conn)
        import_population(cur, conn)
        import_agriculture(cur, conn)
        import_livestock(cur, conn)
        import_markets(cur, conn)
        import_market_prices(cur, conn)
        import_businesses(cur, conn)
        import_weather(cur, conn)

        print("=" * 60, flush=True)
        print(f"ALL IMPORTS COMPLETE in {time.time() - t0:.1f}s", flush=True)
        print("=" * 60, flush=True)
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
