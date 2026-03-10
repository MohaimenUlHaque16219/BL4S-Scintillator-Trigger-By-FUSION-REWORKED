"""
run_all_energies.py
-------------------
Automates G4beamline simulations across 0.5 to 10 GeV/c beam momenta.
For each energy it calls g4bl and saves det1/2/3.txt into organized folders.

Usage:
    python run_all_energies.py

Requirements:
    - G4beamline installed and g4bl in PATH
    - scintillator_trigger.g4bl in the same directory
"""

import subprocess
import os
import shutil

# ── Configuration ──────────────────────────────────────────────────────────────

G4BL_SCRIPT  = "scintillator_trigger.g4bl"
OUTPUT_DIR   = "simulation_output"
N_EVENTS     = 5000

# Beam momenta in MeV/c  (0.5 GeV/c = 500 MeV/c  →  10 GeV/c = 10000 MeV/c)
BEAM_MOMENTA = [500, 1000, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 10000]

# ── Functions ──────────────────────────────────────────────────────────────────

def run_simulation(momentum):
    print(f"\n{'='*55}")
    print(f"  pi+ beam  |  momentum = {momentum} MeV/c  ({momentum/1000:.1f} GeV/c)")
    print(f"{'='*55}")

    cmd = [
        "g4bl", G4BL_SCRIPT,
        f"beam_momentum={momentum}",
        f"nEvents={N_EVENTS}",
    ]
    result = subprocess.run(cmd, text=True)

    if result.returncode != 0:
        print(f"  ⚠  Non-zero exit code: {result.returncode}")
    else:
        print(f"  ✓  Done: {momentum} MeV/c ({momentum/1000:.1f} GeV/c)")

    return result.returncode


def collect_outputs(momentum):
    run_dir = os.path.join(OUTPUT_DIR, f"momentum_{momentum}_MeV")
    os.makedirs(run_dir, exist_ok=True)

    for det_file in ["det1.txt", "det2.txt", "det3.txt"]:
        if os.path.exists(det_file):
            shutil.move(det_file, os.path.join(run_dir, det_file))
            print(f"  Saved: {run_dir}\\{det_file}")
        else:
            print(f"  ⚠  Missing: {det_file}")


def main():
    print("\n" + "="*55)
    print("  Scintillator Trigger — Multi-Energy Simulation")
    print(f"  Particle  : pi+")
    print(f"  Range     : 0.5 — 10.0 GeV/c")
    print(f"  Steps     : {len(BEAM_MOMENTA)} runs × {N_EVENTS} events")
    print(f"  Output    : {OUTPUT_DIR}/")
    print("="*55)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    failed = []

    for momentum in BEAM_MOMENTA:
        ret = run_simulation(momentum)
        collect_outputs(momentum)
        if ret != 0:
            failed.append(momentum)

    print(f"\n{'='*55}")
    print("  All simulations complete.")
    if failed:
        print(f"  ⚠  Failed: {[f'{p} MeV/c' for p in failed]}")
    else:
        print("  ✓  All runs succeeded — 0 errors")
    print(f"\n  Next step → python analyze_detector.py")
    print("="*55 + "\n")


if __name__ == "__main__":
    main()
