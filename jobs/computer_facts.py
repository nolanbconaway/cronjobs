"""Log current computer stats to the DB.

The database DDL is:

create table computer_facts (
	ts_utc timestamp with time zone default CURRENT_TIMESTAMP not null,
	fact_name text not null,
	fact_value real not null
);
"""
import argparse
import os
import shutil
import subprocess

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


def rpi_temperature() -> float:
    command = os.environ["RPI_SSH_COMMAND"].split()
    command += ["/opt/vc/bin/vcgencmd", "measure_temp"]

    out = subprocess.check_output(command).decode().strip()
    assert out.startswith("temp="), out
    assert out.endswith("'C"), out

    temp_c = float(out[5:-2])
    return (temp_c * 1.8) + 32


FACTS = {
    "hd_use_pct": disk_usage,
    "cpu_use_pct": cpu_usage,
    "memory_use_pct": memory_usage,
    "gpu_temp_f": gpu_temp,
    "cpu_temp_f": cpu_temp,
    "rpi_temp_f": rpi_temperature,
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
