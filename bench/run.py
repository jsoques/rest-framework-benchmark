import argparse
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import psutil
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT / ".env")

RESULTS_DIR = ROOT / "bench" / "results"
RESULTS_DIR.mkdir(exist_ok=True)

SERVICE_PORTS = {
    "fastapi-uvicorn": os.environ["FASTAPI_UVICORN_PORT"],
    "fastapi-granian": os.environ["FASTAPI_GRANIAN_PORT"],
    "robyn": os.environ["ROBYN_PORT"],
    "robyn-process-workers": os.environ["ROBYN_PROCESS_WORKERS_PORT"],
    "go-fiber": os.environ["GO_FIBER_PORT"],
    "rust-axum": os.environ["RUST_AXUM_PORT"],
}

SERVICES = {
    "fastapi-uvicorn": {
        "cwd": ROOT / "fastapi-uvicorn",
        "cmd": [
            ".venv/bin/uvicorn",
            "main:app",
            "--host",
            "0.0.0.0",
            "--port",
            SERVICE_PORTS["fastapi-uvicorn"],
        ],
    },
    "fastapi-granian": {
        "cwd": ROOT / "fastapi-granian",
        "cmd": [
            ".venv/bin/granian",
            "--interface",
            "asgi",
            "main:app",
            "--host",
            "0.0.0.0",
            "--port",
            SERVICE_PORTS["fastapi-granian"],
        ],
    },
    "robyn": {
        "cwd": ROOT / "robyn",
        "cmd": [".venv/bin/python", "app.py"],
    },
    "robyn-process-workers": {
        "cwd": ROOT / "robyn-process-workers",
        "cmd": [".venv/bin/python", "app.py"],
    },
    "go-fiber": {
        "cwd": ROOT / "go-fiber",
        "cmd": ["./go-fiber"],
    },
    "rust-axum": {
        "cwd": ROOT / "rust-axum",
        "cmd": ["./target/release/rust-axum"],
    },
}


def wait_for_port(host: str, port: int, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def run_wrk(
    url: str,
    threads: int,
    connections: int,
    duration: str,
    output_path: Path | None = None,
) -> subprocess.CompletedProcess:
    cmd = [
        "wrk",
        "-t",
        str(threads),
        "-c",
        str(connections),
        "-d",
        duration,
        "-L",
        "--timeout",
        "10s",
        url,
    ]
    print(f"  wrk -c{connections} {duration} {url}")
    if output_path is None:
        return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    result = subprocess.run(cmd, capture_output=True, text=True)
    output_path.write_text(result.stdout + "\n" + result.stderr)
    return result


def start_service(name: str, cfg: dict) -> subprocess.Popen:
    log_path = RESULTS_DIR / f"{name}.log"
    print(f"Starting {name}...")
    return subprocess.Popen(
        cfg["cmd"],
        cwd=cfg["cwd"],
        stdout=log_path.open("w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def stop_service(proc: subprocess.Popen, name: str) -> None:
    print(f"Stopping {name} (pid {proc.pid})...")
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass


def monitor_start(proc_pid: int):
    if not psutil.pid_exists(proc_pid):
        return []
    p = psutil.Process(proc_pid)
    procs = [p] + p.children(recursive=True)
    for pr in procs:
        try:
            pr.cpu_percent(interval=None)
        except psutil.NoSuchProcess:
            pass
    return procs


def monitor_end(procs) -> dict:
    cpu = 0.0
    mem = 0
    for pr in procs:
        try:
            cpu += pr.cpu_percent(interval=None)
            mem += pr.memory_info().rss
        except psutil.NoSuchProcess:
            pass
    return {"cpu_percent": round(cpu, 2), "memory_mb": round(mem / (1024 * 1024), 2)}


def build_url(port: int, mode: str, limit: int | None = None) -> str:
    url = f"http://127.0.0.1:{port}/spatial_ref_sys"
    params = []
    if mode == "static":
        params.append("static=1")
    if limit is not None:
        params.append(f"limit={limit}")
    if params:
        url += "?" + "&".join(params)
    return url


def run_benchmark(
    name: str,
    mode: str,
    concurrency: int,
    duration: str,
    warmup: str,
    threads: int,
    monitor: bool,
    limit: int | None,
) -> int:
    cfg = SERVICES[name]
    port = int(SERVICE_PORTS[name])
    proc = start_service(name, cfg)

    if not wait_for_port("127.0.0.1", port):
        print(f"{name} did not start on port {port}", file=sys.stderr)
        stop_service(proc, name)
        return 1

    url = build_url(port, mode, limit)

    procs = monitor_start(proc.pid) if monitor else []

    if warmup != "0s":
        print(f"  Warm-up {warmup}")
        run_wrk(url, threads, concurrency, warmup)

    out_path = RESULTS_DIR / f"{name}_{mode}_c{concurrency}.txt"
    if limit is not None:
        out_path = RESULTS_DIR / f"{name}_{mode}_c{concurrency}_l{limit}.txt"
    result = run_wrk(url, threads, concurrency, duration, output_path=out_path)

    if monitor:
        metrics = monitor_end(procs)
        res_path = out_path.with_suffix(".resources.json")
        res_path.write_text(json.dumps(metrics))
        print(f"  CPU {metrics['cpu_percent']}%  RAM {metrics['memory_mb']} MB")

    stop_service(proc, name)
    time.sleep(0.3)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="REST API performance benchmark")
    parser.add_argument(
        "--mode",
        nargs="+",
        choices=["db", "static"],
        default=["db"],
        help="Endpoint mode(s) to benchmark",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        nargs="+",
        default=[200],
        help="wrk connection counts to sweep",
    )
    parser.add_argument(
        "--duration",
        default="30s",
        help="measured wrk duration",
    )
    parser.add_argument(
        "--warmup",
        default="5s",
        help="warm-up wrk duration per run (use 0s to disable)",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=8,
        help="wrk thread count",
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="record CPU and memory usage for each run",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="override the SQL LIMIT value on supported services",
    )
    parser.add_argument(
        "--services",
        nargs="+",
        choices=list(SERVICES),
        default=list(SERVICES),
        help="services to benchmark",
    )
    parser.add_argument(
        "--skip-report",
        action="store_true",
        help="skip PDF report generation",
    )
    args = parser.parse_args()

    for name in args.services:
        for mode in args.mode:
            for concurrency in args.concurrency:
                if (
                    run_benchmark(
                        name,
                        mode,
                        concurrency,
                        args.duration,
                        args.warmup,
                        args.threads,
                        args.monitor,
                        args.limit,
                    )
                    != 0
                ):
                    return 1

    if not args.skip_report:
        print("Benchmark runs complete. Generating PDF report...")
        report_result = subprocess.run(
            [sys.executable, "report.py"],
            cwd=ROOT / "bench",
        )
        return report_result.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())
