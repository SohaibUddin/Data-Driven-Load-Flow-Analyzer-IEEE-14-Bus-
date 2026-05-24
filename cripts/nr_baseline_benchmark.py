"""
NR-LF Annual Baseline Benchmark
================================
Runs Newton-Raphson load flow on every hour of an annual load profile using
pandapower's IEEE 14-bus network. Reports total wall-clock time so it can
be cited as the conventional-solver baseline in the SoftwareX paper.

INPUT  : a Parquet file with 23 columns (P1..P11, Q1..Q11, contingency_code)
         and one row per hour (e.g. 8 760 rows for one year)
OUTPUT : timing summary printed to stdout

The contingency column (column 23) is intentionally ignored — every hour is
solved as a base-case topology — because faithfully replicating each of the
32 contingency mappings is unnecessary for a speed benchmark. The number of
floating-point operations per Newton-Raphson iteration is dominated by the
Jacobian factorisation, which does not change appreciably between the base
case and the N-1 contingencies on a 14-bus network.

Note:  pandapower is invoked with `numba=False` to match the configuration
used inside the dashboard's NR-validation subprocess (see main.py), ensuring
a fair comparison against the ML inference path.
"""
import time
import sys
import pandas as pd
import pandapower as pp
import pandapower.networks as pn

# ── CONFIG ───────────────────────────────────────────────────────────────────
PARQUET_PATH    = "examples/chunk_1.parquet"
PROGRESS_EVERY  = 500     # print a progress line every N rows
NR_ALGORITHM    = "nr"    # 'nr' = Newton-Raphson (default, matches dashboard)
USE_NUMBA       = False   # matches main.py:_run_pandapower_worker

# ── LOAD INPUT FILE ──────────────────────────────────────────────────────────
print(f"Reading annual load profile:\n  {PARQUET_PATH}")
df = pd.read_parquet(PARQUET_PATH)
print(f"  Loaded {len(df)} rows × {df.shape[1]} columns")

if df.shape[1] < 22:
    sys.exit(f"ERROR: expected at least 22 numerical columns, got {df.shape[1]}")

# Keep only P1..P11 and Q1..Q11; drop the contingency code (col 23)
P_all = df.iloc[:, :11].values.astype(float)   # shape (n_rows, 11)
Q_all = df.iloc[:, 11:22].values.astype(float) # shape (n_rows, 11)
n_rows = len(df)

# ── INITIALISE PANDAPOWER NETWORK ────────────────────────────────────────────
net = pn.case14()
n_loads = len(net.load)
print(f"  pandapower IEEE 14-bus network has {n_loads} loads (expected 11)")

if n_loads != 11:
    sys.exit(f"ERROR: load count mismatch — expected 11, got {n_loads}")

# ── SWEEP NR OVER EVERY HOUR ─────────────────────────────────────────────────
print(f"\nRunning Newton-Raphson on {n_rows} hourly scenarios (base case)...")
print(f"  algorithm = {NR_ALGORITHM!r}   numba = {USE_NUMBA}\n")

n_converged = 0
n_diverged  = 0

t_start = time.perf_counter()

for i in range(n_rows):
    # Replace the network's nominal P/Q with the i-th hourly profile
    net.load["p_mw"]   = P_all[i]
    net.load["q_mvar"] = Q_all[i]

    try:
        pp.runpp(net, algorithm=NR_ALGORITHM, numba=USE_NUMBA)
        n_converged += 1
    except Exception:
        n_diverged += 1

    if i > 0 and (i % PROGRESS_EVERY == 0):
        elapsed = time.perf_counter() - t_start
        rate    = i / elapsed
        eta_s   = (n_rows - i) / rate if rate > 0 else float("inf")
        print(f"  [{i:>5d}/{n_rows}]   "
              f"{rate:6.1f} hr/s   "
              f"elapsed {elapsed:6.1f} s   "
              f"ETA {eta_s:5.0f} s")

t_elapsed = time.perf_counter() - t_start

# ── SUMMARY ──────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  NR-LF Annual Baseline Benchmark — Summary")
print(f"{'='*60}")
print(f"  Hours processed         : {n_rows}")
print(f"    Converged             : {n_converged}")
print(f"    Diverged              : {n_diverged}")
print(f"")
print(f"  Total wall-clock time   : {t_elapsed:>10.2f}  seconds")
print(f"                          = {t_elapsed/60:>10.2f}  minutes")
print(f"                          = {t_elapsed/3600:>10.3f}  hours")
print(f"")
print(f"  Average per hour        : {(t_elapsed/n_rows)*1000:>10.2f}  ms/hour")
print(f"  Throughput              : {n_rows/t_elapsed:>10.2f}  hours/second")

if n_rows != 8760:
    extrap = t_elapsed * 8760 / n_rows
    print(f"")
    print(f"  Extrapolated to 8 760 h : {extrap:>10.2f}  seconds "
          f"({extrap/60:.2f} min, {extrap/3600:.3f} h)")

print(f"{'='*60}")
