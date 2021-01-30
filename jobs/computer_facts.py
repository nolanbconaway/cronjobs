"""Log current computer stats to the DB."""
import argparse
import os
import shutil

import psutil
import psycopg2


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raise", dest="raise_", action="store_true")
    return parser


def insert(conn, name: str, value: float) -> None:
    sql = "insert into computer_facts (fact_name, fact_value) values (%s, %s)"
    with conn.cursor() as cursor:
        cursor.execute(sql, (name, value))
    conn.commit()


def gpu_temp() -> float:
    data = psutil.sensors_temperatures(fahrenheit=True)["amdgpu"][0]
    return data.current


def cpu_temp() -> float:
    data = psutil.sensors_temperatures(fahrenheit=True)["k10temp"]
    return next(i for i in data if i.label == "Tdie").current


def disk_usage() -> None:
    total, used, _ = shutil.disk_usage("/")
    return used / total


def cpu_usage() -> float:
    return psutil.cpu_percent() / 100


def memory_usage() -> float:
    return psutil.virtual_memory().percent / 100


FACTS = {
    "hd_use_pct": disk_usage,
    "cpu_use_pct": cpu_usage,
    "memory_use_pct": memory_usage,
    "gpu_temp_f": gpu_temp,
    "cpu_temp_f": cpu_temp,
}

if __name__ == "__main__":
    args = make_parser().parse_args()

    errors = []
    with psycopg2.connect(os.environ["POSTGRES_DSN"]) as conn:
        for fact_name, func in FACTS.items():
            try:
                insert(conn, fact_name, func())
            except Exception:
                if args.raise_:
                    raise
                errors.append(fact_name)

    if errors:
        raise RuntimeError(f"Errors occurred on {errors}")
