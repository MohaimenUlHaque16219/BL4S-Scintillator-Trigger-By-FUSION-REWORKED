"""
analyze_detector.py
-------------------
Reads G4beamline virtualdetector output files and computes:

  1. Efficiency vs Beam Momentum   — coincidence trigger (Det1 & Det3)
  2. Latency vs Beam Momentum      — time difference Det1_vd → Det3_vd
  3. Secondary Fraction vs Threshold — noise characterization

Particle : pi+  (PDGid=211, rest mass=139.57 MeV/c²)
Range    : 0.5 to 10 GeV/c

G4beamline output columns (0-indexed):
  0:x  1:y  2:z  3:Px  4:Py  5:Pz  6:t  7:PDGid  8:EventID  9:TrackID  10:ParentID  11:Weight
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ── Configuration ──────────────────────────────────────────────────────────────

OUTPUT_DIR   = "simulation_output"
PLOT_DIR     = "plots"

# MeV/c  (0.5 GeV/c → 10 GeV/c)
BEAM_MOMENTA = [500, 1000, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 10000]

PI_MASS = 139.57   # MeV/c²  rest mass of pi+
PDG_PI_PLUS = 211  # PDG particle ID for pi+

# Momentum thresholds for secondary fraction plot (MeV/c)
THRESHOLDS = np.linspace(50, 800, 50)

# Column indices
COL_PX  = 3
COL_PY  = 4
COL_PZ  = 5
COL_T   = 6
COL_PDG = 7
COL_EID = 8   # EventID
COL_TID = 9   # TrackID  (1 = primary beam particle)

# ── Helpers ────────────────────────────────────────────────────────────────────

def mom_to_ke(p_MeV):
    """Convert momentum (MeV/c) → kinetic energy (GeV)."""
    return (np.sqrt(p_MeV**2 + PI_MASS**2) - PI_MASS) / 1000.0

def mom_to_GeV(p_MeV):
    """Convert MeV/c → GeV/c for axis labels."""
    return p_MeV / 1000.0

def load_hits(filepath):
    if not os.path.exists(filepath):
        return None
    try:
        data = np.loadtxt(filepath, comments='#')
        if data.ndim == 1:
            data = data.reshape(1, -1)
        return data if len(data) > 0 else None
    except Exception as e:
        print(f"    Warning: {filepath}: {e}")
        return None

def primary_pi_plus(hits):
    """Filter to primary pi+ beam particles only (TrackID=1, PDGid=211)."""
    if hits is None:
        return None
    mask = (hits[:, COL_TID].astype(int) == 1) & \
           (hits[:, COL_PDG].astype(int) == PDG_PI_PLUS)
    result = hits[mask]
    return result if len(result) > 0 else None

def event_ids(hits):
    if hits is None:
        return set()
    return set(hits[:, COL_EID].astype(int))

def total_momentum(hits):
    """|p| = sqrt(Px²+Py²+Pz²) in MeV/c."""
    if hits is None:
        return np.array([])
    return np.sqrt(hits[:, COL_PX]**2 + hits[:, COL_PY]**2 + hits[:, COL_PZ]**2)

def run_dir(momentum):
    return os.path.join(OUTPUT_DIR, f"momentum_{momentum}_MeV")

# ── Metric 1: Efficiency ───────────────────────────────────────────────────────

def compute_efficiency(momentum):
    """
    Efficiency = fraction of beam events where pi+ hits BOTH Det1 AND Det3.
    This is the coincidence trigger logic used in real experiments.
    """
    h1 = primary_pi_plus(load_hits(os.path.join(run_dir(momentum), "det1.txt")))
    h3 = primary_pi_plus(load_hits(os.path.join(run_dir(momentum), "det3.txt")))

    ev1 = event_ids(h1)
    ev3 = event_ids(h3)

    if len(ev1) == 0:
        return 0.0

    return len(ev1 & ev3) / len(ev1)

# ── Metric 2: Latency ──────────────────────────────────────────────────────────

def compute_latency(momentum):
    """
    Latency = mean time for pi+ to travel from Det1_vd (z=94mm) to Det3_vd (z=694mm).
    Distance = 600mm. Higher momentum → faster particle → shorter latency.
    """
    h1 = primary_pi_plus(load_hits(os.path.join(run_dir(momentum), "det1.txt")))
    h3 = primary_pi_plus(load_hits(os.path.join(run_dir(momentum), "det3.txt")))

    if h1 is None or h3 is None:
        return np.nan, np.nan

    def evt_time(hits):
        m = {}
        for row in hits:
            eid = int(row[COL_EID])
            if eid not in m:
                m[eid] = row[COL_T]
        return m

    m1 = evt_time(h1)
    m3 = evt_time(h3)
    common = set(m1) & set(m3)

    if not common:
        return np.nan, np.nan

    deltas = np.array([m3[e] - m1[e] for e in common if m3[e] > m1[e]])
    if len(deltas) == 0:
        return np.nan, np.nan

    return np.mean(deltas), np.std(deltas)

# ── Metric 3: Secondary Fraction vs Threshold ──────────────────────────────────

def compute_secondary_fraction():
    """
    For each momentum threshold, compute the fraction of ALL hits (primaries +
    secondaries) in Det1 that fall BELOW the threshold.
    These sub-threshold hits represent noise / secondary particles.
    Raising the trigger threshold cuts them out.
    """
    all_p = []
    for mom in BEAM_MOMENTA:
        h = load_hits(os.path.join(run_dir(mom), "det1.txt"))
        if h is not None:
            all_p.append(total_momentum(h))

    if not all_p:
        return np.zeros(len(THRESHOLDS))

    all_p = np.concatenate(all_p)
    total = len(all_p)
    return np.array([np.sum(all_p < thr) / total for thr in THRESHOLDS])

# ── Plot Styling ───────────────────────────────────────────────────────────────

def style(ax, xlabel, ylabel, title):
    ax.set_facecolor("#0d1117")
    ax.set_xlabel(xlabel, color="#aac4dd", fontsize=11)
    ax.set_ylabel(ylabel, color="#aac4dd", fontsize=11)
    ax.set_title(title, color="#e0eaf4", fontsize=13, pad=12)
    ax.tick_params(colors="#607d8b")
    for sp in ax.spines.values():
        sp.set_edgecolor("#1e2a38")
    ax.grid(True, color="#1e2a38", linestyle="--", linewidth=0.6)

# ── Plots ──────────────────────────────────────────────────────────────────────

def plot_efficiency(x, y):
    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor="#050810")
    ax.plot(x, y, "o-", color="#00e5ff", lw=2,
            markersize=8, markerfacecolor="#050810", markeredgewidth=2)
    ax.fill_between(x, y, alpha=0.1, color="#00e5ff")
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
    style(ax, "Beam Momentum (GeV/c)", "Trigger Efficiency",
          "pi⁺ Detector Efficiency vs Beam Momentum")
    fig.tight_layout()
    path = os.path.join(PLOT_DIR, "efficiency_vs_momentum.png")
    fig.savefig(path, dpi=150, facecolor="#050810")
    print(f"  Saved: {path}")
    plt.close(fig)

def plot_latency(x, means, stds):
    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor="#050810")
    means = np.array(means, dtype=float)
    stds  = np.array(stds,  dtype=float)
    ax.errorbar(x, means, yerr=stds, fmt="o-",
                color="#bf5af2", lw=2, markersize=8,
                markerfacecolor="#050810", markeredgewidth=2,
                ecolor="#bf5af280", capsize=5)
    style(ax, "Beam Momentum (GeV/c)", "Trigger Latency (ns)",
          "pi⁺ Trigger Latency vs Beam Momentum")
    fig.tight_layout()
    path = os.path.join(PLOT_DIR, "latency_vs_momentum.png")
    fig.savefig(path, dpi=150, facecolor="#050810")
    print(f"  Saved: {path}")
    plt.close(fig)

def plot_secondary(rates):
    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor="#050810")
    clipped = np.clip(rates, 1e-5, 1)
    ax.semilogy(THRESHOLDS / 1000.0, clipped, "-", color="#ff6b6b", lw=2)
    ax.fill_between(THRESHOLDS / 1000.0, clipped, 1e-5,
                    alpha=0.1, color="#ff6b6b")
    style(ax, "Momentum Threshold (GeV/c)", "Secondary Particle Fraction",
          "Noise Characterization — Secondary Fraction vs Threshold")
    fig.tight_layout()
    path = os.path.join(PLOT_DIR, "secondary_fraction_vs_threshold.png")
    fig.savefig(path, dpi=150, facecolor="#050810")
    print(f"  Saved: {path}")
    plt.close(fig)

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    plt.rcParams.update({"font.family": "monospace"})
    os.makedirs(PLOT_DIR, exist_ok=True)

    x_vals   = [mom_to_GeV(p) for p in BEAM_MOMENTA]
    eff_vals = []
    lat_mean = []
    lat_std  = []

    print("\n  Analyzing pi+ simulation output...\n")
    print(f"  {'Momentum':>10}  {'KE':>8}  {'Efficiency':>10}  {'Latency':>16}")
    print(f"  {'-'*10}  {'-'*8}  {'-'*10}  {'-'*16}")

    for p, x in zip(BEAM_MOMENTA, x_vals):
        eff      = compute_efficiency(p)
        mean, sd = compute_latency(p)
        ke       = mom_to_ke(p)
        eff_vals.append(eff)
        lat_mean.append(mean)
        lat_std.append(sd)
        print(f"  {x:>8.2f} GeV/c  {ke:>6.3f} GeV  {eff:>10.3f}  {mean:>7.3f}±{sd:.3f} ns")

    sec_rates = compute_secondary_fraction()

    print("\n  Generating plots...")
    plot_efficiency(x_vals, eff_vals)
    plot_latency(x_vals, lat_mean, lat_std)
    plot_secondary(sec_rates)

    print(f"\n  Done! All plots saved to: {PLOT_DIR}/")
    print(f"  - efficiency_vs_momentum.png")
    print(f"  - latency_vs_momentum.png")
    print(f"  - secondary_fraction_vs_threshold.png\n")

if __name__ == "__main__":
    main()
