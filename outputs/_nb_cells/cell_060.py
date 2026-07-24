# ── 7.7  Monitor de recursos: RAM / VRAM / CPU / GPU ────────────────────────
import subprocess
import json
import os
import csv
import time
from pathlib import Path
from datetime import datetime

# psutil para RAM y CPU
try:
    import psutil
    ram = psutil.virtual_memory()
    cpu_pct = psutil.cpu_percent(interval=1)
    ram_used_gib  = ram.used / 1024**3
    ram_total_gib = ram.total / 1024**3
    ram_pct = ram.percent
except ImportError:
    ram_used_gib = ram_total_gib = ram_pct = cpu_pct = None
    print("[INFO] psutil no disponible. Instala con: pip install psutil")

# GPU via nvidia-smi
gpu_info = {}
try:
    res = subprocess.run(
        ["nvidia-smi",
         "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu",
         "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=10,
    )
    if res.returncode == 0:
        parts = [p.strip() for p in res.stdout.strip().split(",")]
        if len(parts) >= 6:
            gpu_info = {
                "gpu_index"      : parts[0],
                "gpu_name"       : parts[1],
                "gpu_util_pct"   : float(parts[2]),
                "vram_used_mib"  : float(parts[3]),
                "vram_total_mib" : float(parts[4]),
                "gpu_temp_c"     : float(parts[5]),
                "vram_used_gib"  : float(parts[3]) / 1024,
                "vram_total_gib" : float(parts[4]) / 1024,
                "vram_used_pct"  : 100.0 * float(parts[3]) / max(float(parts[4]), 1),
            }
except Exception as e:
    print(f"[WARN] nvidia-smi error: {e}")

snap = {
    "timestamp"       : datetime.now().isoformat(),
    "ram_used_gib"    : round(ram_used_gib or 0, 2),
    "ram_total_gib"   : round(ram_total_gib or 0, 2),
    "ram_used_pct"    : round(ram_pct or 0, 1),
    "cpu_used_pct"    : round(cpu_pct or 0, 1),
    **{k: round(v, 2) if isinstance(v, float) else v for k, v in gpu_info.items()},
}

# Guardar snapshot CSV
out_dir = Path(globals().get("OUTPUT_ROOT", "/tmp"))
snap_path = out_dir / "resource_usage_snapshot.csv"
file_exists = snap_path.exists()
with open(snap_path, "a", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(snap.keys()))
    if not file_exists:
        w.writeheader()
    w.writerow(snap)

print(f"{'=' * 55}")
print(f"  SNAPSHOT DE RECURSOS — {snap['timestamp'][:19]}")
print(f"{'=' * 55}")
print(f"  RAM         : {snap['ram_used_gib']:.1f} / {snap['ram_total_gib']:.1f} GiB  ({snap['ram_used_pct']:.0f}%)")
print(f"  CPU         : {snap['cpu_used_pct']:.0f}% utilizado")
if gpu_info:
    print(f"  GPU         : {gpu_info.get('gpu_name', '?')}")
    print(f"  GPU util    : {gpu_info.get('gpu_util_pct', 0):.0f}%")
    print(f"  VRAM usada  : {gpu_info.get('vram_used_gib', 0):.1f} / {gpu_info.get('vram_total_gib', 0):.1f} GiB  ({gpu_info.get('vram_used_pct', 0):.0f}%)")
    print(f"  Temp GPU    : {gpu_info.get('gpu_temp_c', 0):.0f} C")
print(f"  Guardado en : {snap_path}")
