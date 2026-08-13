import json
import re
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "bench" / "results"
REPORT_PATH = ROOT / "bench" / "report.pdf"

DEFAULT_CONCURRENCY = 200


def to_milliseconds(value: str) -> float:
    m = re.match(r"([\d.]+)\s*([a-zA-Z]+)", value.strip())
    if not m:
        return 0.0
    number = float(m.group(1))
    unit = m.group(2)
    if unit == "us":
        return number / 1000.0
    if unit == "ms":
        return number
    if unit == "s":
        return number * 1000.0
    if unit in ("m", "min"):
        return number * 60000.0
    return number


def parse_wrk(path: Path) -> tuple:
    text = path.read_text()
    throughput = None
    p50 = None
    p99 = None

    m = re.search(r"Requests/sec:\s+([\d.,]+)", text)
    if m:
        throughput = float(m.group(1).replace(",", ""))

    percentiles = {}
    for match in re.finditer(r"(\d+)%\s+([\d.]+[a-zA-Z]+)", text):
        percentiles[match.group(1)] = to_milliseconds(match.group(2))
    p50 = percentiles.get("50")
    p99 = percentiles.get("99")

    return throughput, p50, p99


def parse_filename(path: Path) -> tuple:
    m = re.match(r"(.+)_(db|static)_c(\d+)(?:_l(\d+))?\.txt$", path.name)
    if m:
        return m.group(1), m.group(2), int(m.group(3)), int(m.group(4)) if m.group(4) else None
    return path.stem, "db", 200, None


def load_data() -> list:
    keyed = {}
    for path in RESULTS_DIR.glob("*.txt"):
        if path.name.endswith("_warmup.txt"):
            continue
        throughput, p50, p99 = parse_wrk(path)
        if throughput is None:
            continue
        service, mode, concurrency, limit = parse_filename(path)
        res_path = path.with_suffix(".resources.json")
        resources = json.loads(res_path.read_text()) if res_path.exists() else {}
        key = (service, mode, concurrency, limit)
        mtime = path.stat().st_mtime
        if key in keyed and mtime <= keyed[key]["_mtime"]:
            continue
        keyed[key] = {
            "service": service,
            "mode": mode,
            "concurrency": concurrency,
            "limit": limit,
            "throughput": throughput,
            "p50": p50,
            "p99": p99,
            "cpu_percent": resources.get("cpu_percent"),
            "memory_mb": resources.get("memory_mb"),
            "_mtime": mtime,
        }
    for item in keyed.values():
        del item["_mtime"]
    return list(keyed.values())


def chart_path(name: str) -> Path:
    return RESULTS_DIR / f"{name}.png"


def line_chart(data: list, mode: str, metric: str, ylabel: str, title: str) -> Path | None:
    services = sorted({d["service"] for d in data if d["mode"] == mode})
    if not services:
        return None
    out = chart_path(f"{metric}_{mode}")
    plt.figure(figsize=(8, 4))
    for service in services:
        points = sorted(
            [(d["concurrency"], d[metric]) for d in data if d["service"] == service and d["mode"] == mode],
            key=lambda x: x[0],
        )
        concurrencies = [p[0] for p in points]
        values = [p[1] for p in points]
        plt.plot(concurrencies, values, marker="o", label=service)
    plt.xlabel("Connections")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return out


def grouped_bar_chart(data: list, metric: str, ylabel: str, title: str, concurrency: int) -> Path:
    services = sorted({d["service"] for d in data})
    out = chart_path(f"{metric}_c{concurrency}")
    db_vals = []
    static_vals = []
    for service in services:
        db = next(
            (d[metric] for d in data if d["service"] == service and d["mode"] == "db" and d["concurrency"] == concurrency),
            None,
        )
        static = next(
            (d[metric] for d in data if d["service"] == service and d["mode"] == "static" and d["concurrency"] == concurrency),
            None,
        )
        db_vals.append(db if db is not None else 0)
        static_vals.append(static if static is not None else 0)

    x = np.arange(len(services))
    width = 0.35
    plt.figure(figsize=(8, 4))
    plt.bar(x - width / 2, db_vals, width, label="db", color="steelblue")
    plt.bar(x + width / 2, static_vals, width, label="static", color="coral")
    plt.xlabel("Service")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(x, services)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return out


def resource_chart(data: list, concurrency: int) -> tuple:
    services = sorted({d["service"] for d in data})
    cpu = []
    mem = []
    cpu_services = []
    mem_services = []
    for service in services:
        row = next(
            (d for d in data if d["service"] == service and d["mode"] == "db" and d["concurrency"] == concurrency and d["cpu_percent"] is not None),
            None,
        )
        if row:
            cpu.append(row["cpu_percent"])
            mem.append(row["memory_mb"])
            cpu_services.append(service)
            mem_services.append(service)

    cpu_path = chart_path(f"cpu_c{concurrency}")
    plt.figure(figsize=(8, 4))
    plt.bar(cpu_services, cpu, color="seagreen")
    plt.xlabel("Service")
    plt.ylabel("CPU %")
    plt.title(f"DB mode CPU usage at {concurrency} connections")
    plt.tight_layout()
    plt.savefig(cpu_path)
    plt.close()

    mem_path = chart_path(f"memory_c{concurrency}")
    plt.figure(figsize=(8, 4))
    plt.bar(mem_services, mem, color="mediumpurple")
    plt.xlabel("Service")
    plt.ylabel("Memory (MB)")
    plt.title(f"DB mode RSS at {concurrency} connections")
    plt.tight_layout()
    plt.savefig(mem_path)
    plt.close()

    return cpu_path, mem_path


def create_charts(data: list, concurrency: int) -> list:
    charts = []
    for label, metric, ylabel in [
        ("Throughput (DB)", "throughput", "Requests/sec"),
        ("p99 Latency (DB)", "p99", "ms"),
    ]:
        out = line_chart(data, "db", metric, ylabel, f"DB {label.split(' (')[0]} vs Concurrency")
        if out:
            charts.append((label, out))
    for label, metric, ylabel in [
        ("Throughput (Static)", "throughput", "Requests/sec"),
        ("p99 Latency (Static)", "p99", "ms"),
    ]:
        out = line_chart(data, "static", metric, ylabel, f"Static {label.split(' (')[0]} vs Concurrency")
        if out:
            charts.append((label, out))
    charts.append(
        (
            f"Throughput c{concurrency}",
            grouped_bar_chart(data, "throughput", "Requests/sec", f"Throughput at {concurrency} connections", concurrency),
        )
    )
    charts.append(
        (
            f"p99 c{concurrency}",
            grouped_bar_chart(data, "p99", "ms", f"p99 Latency at {concurrency} connections", concurrency),
        )
    )
    if any(d["cpu_percent"] is not None for d in data):
        cpu, mem = resource_chart(data, concurrency)
        charts.append(("CPU", cpu))
        charts.append(("Memory", mem))
    return charts


def row_for_concurrency(data: list, concurrency: int) -> list:
    return [d for d in data if d["concurrency"] == concurrency]


def create_pdf(data: list, charts: list, concurrency: int) -> None:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "REST API Benchmark Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Configuration: wrk -t8 -d30s -L --timeout 10s", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.cell(0, 8, f"Table at concurrency {concurrency}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(4)

    rows = row_for_concurrency(data, concurrency)
    col_widths = [45, 25, 35, 35, 35]
    headers = ["Service", "Mode", "Throughput", "p50 (ms)", "p99 (ms)"]
    pdf.set_font("Helvetica", "B", 9)
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 8, h, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for r in rows:
        values = [
            r["service"],
            r["mode"],
            f"{r['throughput']:.2f}",
            f"{r['p50']:.2f}" if r["p50"] is not None else "N/A",
            f"{r['p99']:.2f}" if r["p99"] is not None else "N/A",
        ]
        for w, v in zip(col_widths, values):
            pdf.cell(w, 8, v, border=1, align="L")
        pdf.ln()

    for title, path in charts:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.image(str(path), x=10, w=190)

    pdf.output(str(REPORT_PATH))


def generate_report() -> None:
    data = load_data()
    if not data:
        raise RuntimeError("No wrk results found in bench/results/")
    concurrencies = {d["concurrency"] for d in data}
    concurrency = DEFAULT_CONCURRENCY if DEFAULT_CONCURRENCY in concurrencies else max(concurrencies)
    charts = create_charts(data, concurrency)
    create_pdf(data, charts, concurrency)
    print(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    generate_report()
