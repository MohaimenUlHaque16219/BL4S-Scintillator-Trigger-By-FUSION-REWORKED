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

def compute_dead_time_fraction(particles_per_spill_array, tau_ns=50.0):
    """
    Dead time fraction = fraction of beam spill time the detector is "blind"
    after recording a hit (non-paralyzable / extending dead time model).

    Formula (non-paralyzable):
        D = rate * tau / (1 + rate * tau)

    Where:
        rate     = particles per spill / spill duration
        tau      = detector dead time per hit (ns)
        spill    = typical CERN PS/SPS spill duration = 400 ms = 4e8 ns

    Parameters:
        particles_per_spill : array of beam intensities to sweep
        tau_ns              : detector dead time in nanoseconds (default 50 ns
                              — typical for plastic scintillator + electronics)
    """
    spill_duration_ns = 400e6   # 400 ms in nanoseconds (typical CERN spill)
    dead_fractions = []

    for n in particles_per_spill_array:
        rate = n / spill_duration_ns          # particles per ns
        d    = (rate * tau_ns) / (1 + rate * tau_ns)  # non-paralyzable model
        dead_fractions.append(d)

    return np.array(dead_fractions)


def plot_dead_time(particles_array, dead_fractions):
    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor="#050810")

    ax.semilogx(particles_array, dead_fractions * 100,
                "-", color="#ffd60a", lw=2.5)
    ax.fill_between(particles_array, dead_fractions * 100,
                    alpha=0.1, color="#ffd60a")

    # Mark 10% and 50% dead time lines
    ax.axhline(y=10, color="#ff6b6b", linestyle="--", lw=1, alpha=0.7,
               label="10% dead time")
    ax.axhline(y=50, color="#ff4444", linestyle="--", lw=1, alpha=0.7,
               label="50% dead time")

    ax.legend(facecolor="#0d1117", edgecolor="#1e2a38",
              labelcolor="#aac4dd", fontsize=9)

    ax.set_xlim(particles_array[0], particles_array[-1])
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f%%'))

    style(ax, "Particles per Spill", "Dead Time Fraction (%)",
          "Detector Dead Time Fraction vs Beam Intensity\n"
          r"$\tau$ = 50 ns  |  Spill = 400 ms  |  Non-paralyzable model")

    fig.tight_layout()
    path = os.path.join(PLOT_DIR, "dead_time_vs_intensity.png")
    fig.savefig(path, dpi=150, facecolor="#050810")
    print(f"  Saved: {path}")
    plt.close(fig)


def run_dead_time_analysis():
    # Sweep from 10^4 to 10^6 particles per spill
    particles = np.logspace(4, 6, 300)
    dead_fractions = compute_dead_time_fraction(particles, tau_ns=50.0)
    plot_dead_time(particles, dead_fractions)

    # Print key values
    print("\n  Dead Time Summary (tau=50ns, spill=400ms):")
    print(f"  {'Particles/spill':>16}  {'Dead Time':>10}")
    print(f"  {'-'*16}  {'-'*10}")
    for n in [1e4, 5e4, 1e5, 5e5, 1e6]:
        rate = n / 400e6
        d = (rate * 50) / (1 + rate * 50)
        print(f"  {n:>16.0e}  {d*100:>9.2f}%")

# ── Detector Response vs Beam Energy ──────────────────────────────────────────

def compute_detector_response(momentum):
    """
    Average total momentum of ALL hits in each detector layer.
    Represents the mean signal strength seen by each scintillator.
    Higher energy beam → higher momentum hits → stronger detector response.
    """
    responses = []
    for det_file in ["det1.txt", "det2.txt", "det3.txt"]:
        h = load_hits(os.path.join(run_dir(momentum), det_file))
        if h is not None:
            p_total = total_momentum(h)
            responses.append(np.mean(p_total) / 1000.0)  # Convert to GeV/c
        else:
            responses.append(np.nan)
    return responses  # [det1_mean, det2_mean, det3_mean]


def plot_detector_response(x_vals, responses_per_momentum):
    """
    responses_per_momentum: list of [det1, det2, det3] for each momentum
    """
    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor="#050810")

    det1 = [r[0] for r in responses_per_momentum]
    det2 = [r[1] for r in responses_per_momentum]
    det3 = [r[2] for r in responses_per_momentum]

    ax.plot(x_vals, det1, "o-", color="#00e5ff", lw=2, markersize=7,
            markerfacecolor="#050810", markeredgewidth=2, label="Det 1 (z=100mm)")
    ax.plot(x_vals, det2, "s-", color="#bf5af2", lw=2, markersize=7,
            markerfacecolor="#050810", markeredgewidth=2, label="Det 2 (z=400mm)")
    ax.plot(x_vals, det3, "^-", color="#ff6b6b", lw=2, markersize=7,
            markerfacecolor="#050810", markeredgewidth=2, label="Det 3 (z=700mm)")

    ax.legend(facecolor="#0d1117", edgecolor="#1e2a38",
              labelcolor="#aac4dd", fontsize=9)

    style(ax, "Beam Momentum (GeV/c)", "Mean Hit Momentum (GeV/c)",
          "Detector Response vs Beam Energy\n(Mean Signal Momentum per Layer)")

    fig.tight_layout()
    path = os.path.join(PLOT_DIR, "detector_response_vs_energy.png")
    fig.savefig(path, dpi=150, facecolor="#050810")
    print(f"  Saved: {path}")
    plt.close(fig)


# ── Coincidence Rate vs Beam Intensity ────────────────────────────────────────

def compute_coincidence_rate(particles_array, base_efficiency=0.97, tau_ns=50.0):
    """
    Coincidence rate = expected triple-coincidence triggers per spill.

    At low intensity: rate grows linearly with beam intensity
    At high intensity: dead time kills triggers → rate saturates and rolls off

    Formula:
        true_rate      = N / spill_duration
        recorded_rate  = true_rate / (1 + true_rate * tau)   [non-paralyzable]
        coincidences   = recorded_rate * spill_duration * efficiency^3
                         (efficiency^3 because all 3 layers must fire)
    """
    spill_ns   = 400e6   # 400 ms in ns
    eff3       = base_efficiency ** 3  # triple coincidence efficiency

    coincidences = []
    for n in particles_array:
        true_rate     = n / spill_ns
        recorded_rate = true_rate / (1 + true_rate * tau_ns)
        n_recorded    = recorded_rate * spill_ns
        coincidences.append(n_recorded * eff3)

    return np.array(coincidences)


def plot_coincidence_rate(particles_array, coinc_rates):
    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor="#050810")

    ax.loglog(particles_array, coinc_rates,
              "-", color="#00e676", lw=2.5)
    ax.fill_between(particles_array, coinc_rates, 1,
                    alpha=0.08, color="#00e676")

    # Mark the saturation region — where dead time becomes significant (>10%)
    spill_ns = 400e6
    tau_ns   = 50.0
    n_10pct  = 0.10 / (tau_ns / spill_ns * (1 - 0.10))  # N where D=10%
    ax.axvline(x=n_10pct, color="#ffd60a", linestyle="--", lw=1.2, alpha=0.8,
               label=f"10% dead time (~{n_10pct:.1e} p/spill)")

    ax.legend(facecolor="#0d1117", edgecolor="#1e2a38",
              labelcolor="#aac4dd", fontsize=9)

    style(ax, "Particles per Spill", "Triple Coincidence Triggers per Spill",
          "Coincidence Rate vs Beam Intensity\n"
          r"$\eta^3$ = 91.6%  |  $\tau$ = 50 ns  |  Spill = 400 ms")

    fig.tight_layout()
    path = os.path.join(PLOT_DIR, "coincidence_rate_vs_intensity.png")
    fig.savefig(path, dpi=150, facecolor="#050810")
    print(f"  Saved: {path}")
    plt.close(fig)


def run_extra_analyses(x_vals, eff_vals):
    # --- Detector Response ---
    print("\n  Computing detector response per layer...")
    responses = []
    for p in BEAM_MOMENTA:
        responses.append(compute_detector_response(p))
    plot_detector_response(x_vals, responses)

    # --- Coincidence Rate ---
    particles = np.logspace(3, 7, 500)   # 10^3 to 10^7
    coinc     = compute_coincidence_rate(particles, base_efficiency=np.mean(eff_vals))
    plot_coincidence_rate(particles, coinc)
    os.makedirs(PLOT_DIR, exist_ok=True)
def main():
    plt.rcParams.update({"font.family": "monospace"})


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
    run_dead_time_analysis()
    run_extra_analyses(x_vals, eff_vals)

    print(f"\n  Done! All plots saved to: {PLOT_DIR}/")
    print(f"  - efficiency_vs_momentum.png")
    print(f"  - latency_vs_momentum.png")
    print(f"  - secondary_fraction_vs_threshold.png")
    print(f"  - dead_time_vs_intensity.png")
    print(f"  - detector_response_vs_energy.png")
    print(f"  - coincidence_rate_vs_intensity.png\n")

if __name__ == "__main__":
    main()
