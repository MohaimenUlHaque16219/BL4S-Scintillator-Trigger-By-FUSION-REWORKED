# BL4S 2025 — Scintillator Trigger Detector Simulation

**Competition:** Beamline for Schools (BL4S) by CERN  
**Team:** FUSION REWORKED
**Institution:** Dhaka Residential Model College
**Country:** Bangladesh  

---

## Project Overview

This project simulates a **multi-layer plastic scintillator trigger detector system** using G4beamline (Geant4-based simulation software). The goal is to characterize the trigger performance of a scintillator detector exposed to a **pi+ (positive pion) beam** in the momentum range of **0.5 to 10 GeV/c** — typical of particle beams used in CERN's PS and SPS beamlines.

The simulation models how detector efficiency, trigger latency, and noise characteristics vary with beam energy — key metrics for evaluating whether a detector design is suitable for a real beamline experiment.

---

## Physics Motivation

When a charged pion passes through a plastic scintillator, it deposits energy and produces a detectable signal. By placing three scintillator layers along the beamline and requiring **coincidence** (signals in all three layers), we can build a reliable trigger that:

- Confirms a real particle has passed through the full detector stack
- Rejects random noise and low-energy background hits
- Measures the particle's time-of-flight between layers

This is the same principle used in large-scale experiments like LHCb, NA61/SHINE, and COMPASS at CERN.

---

## Detector Setup

```
Beam direction (+Z) →

  [pi+ Beam]  →  [Det 1]  →  [Det 2]  →  [Det 3]
  z = -50mm      z = 100mm    z = 400mm    z = 700mm
```

| Component | Specification |
|---|---|
| Beam particle | pi+ (positive pion, PDG id = 211) |
| Beam momentum | 0.5 — 10.0 GeV/c |
| Beam profile | Gaussian, σ = 5mm |
| Scintillator material | G4_PLASTIC_SC_VINYLTOLUENE |
| Scintillator dimensions | 200 × 200 × 10 mm |
| Layer positions (Z) | 100 mm, 400 mm, 700 mm |
| Virtual detector offset | 6 mm upstream of each layer |
| Events per run | 5000 |
| Physics list | QGSP_BERT |

---

## Results

### 1. Trigger Efficiency vs Beam Momentum

Efficiency measures how reliably the detector records a pi+ event — defined as the fraction of beam events that produce hits in **both Det1 and Det3** (coincidence trigger).

| Momentum (GeV/c) | KE (GeV) | Efficiency |
|---|---|---|
| 0.50 | 0.380 | 94.2% |
| 1.00 | 0.870 | 96.1% |
| 2.00 | 1.865 | 96.7% |
| 5.00 | 4.862 | 97.6% |
| 10.00 | 9.861 | 97.9% |

**Trend:** Efficiency increases with momentum because higher-energy pions travel straighter, scatter less in the scintillator material, and are less likely to decay before reaching the downstream detector.

---

### 2. Trigger Latency vs Beam Momentum

Latency is the time difference between a hit in Det1_vd (z = 94 mm) and Det3_vd (z = 694 mm) — a 600 mm flight path.

| Momentum (GeV/c) | Latency (ns) |
|---|---|
| 0.50 | 2.079 ± 0.004 |
| 1.00 | 2.021 ± 0.002 |
| 5.00 | 2.002 ± 0.000 |
| 10.00 | 2.002 ± 0.000 |

**Trend:** Latency decreases with momentum and converges toward **~2.000 ns** — the theoretical minimum for a relativistic particle traveling 600 mm at the speed of light (600 mm / c ≈ 2.0 ns). This confirms the simulation is physically consistent.

---

### 3. Secondary Particle Fraction vs Momentum Threshold

This plot characterizes detector noise. Not all hits in the detector are from the primary beam particle — secondary particles (electrons, gammas, scattered hadrons) are produced when the pion interacts with the scintillator material. By applying a **momentum threshold**, low-energy secondary hits can be rejected.

**Interpretation:** As the threshold increases, the fraction of secondary (noise) hits that pass the threshold drops sharply — showing the optimal threshold range for clean trigger operation.

---

## Repository Structure

```
BL4S-Scintillator-Trigger/
│
├── scintillator_trigger.g4bl     # G4beamline simulation script
├── run_all_energies.py           # Automates multi-energy simulation runs
├── analyze_detector.py           # Analyzes output data and generates plots
│
├── simulation_output/            # Raw hit data (generated after running)
│   ├── momentum_500_MeV/
│   │   ├── det1.txt
│   │   ├── det2.txt
│   │   └── det3.txt
│   └── ...
│
├── plots/                        # Output plots (generated after analysis)
│   ├── efficiency_vs_momentum.png
│   ├── latency_vs_momentum.png
│   └── secondary_fraction_vs_threshold.png
│
└── README.md
```

---

## How to Reproduce

### Requirements

- [G4beamline 3.08](https://g4beamline.muonsinc.com) — includes Geant4 bundled
- Python 3.x with `numpy` and `matplotlib`

### Installation (Windows)

1. Download and install G4beamline from https://g4beamline.muonsinc.com
2. Add `C:\Program Files\Muons, Inc\G4beamline\bin` to your system PATH
3. Install Python dependencies:
   ```
   pip install numpy matplotlib
   ```

### Running the Simulation

```bash
# Run all 11 beam momenta (0.5 to 10 GeV/c)
python run_all_energies.py

# Analyze results and generate plots
python analyze_detector.py
```

### Single Energy Test

```bash
g4bl scintillator_trigger.g4bl beam_momentum=500
```

---

## Output File Format

G4beamline writes hit data in space-separated columns:

```
# x(mm)  y(mm)  z(mm)  Px(MeV)  Py(MeV)  Pz(MeV)  t(ns)  PDGid  EventID  TrackID  ParentID  Weight
```

The most important columns for analysis are:
- `t` — hit time in nanoseconds (used for latency)
- `Pz` — longitudinal momentum (used for secondary particle filtering)
- `EventID` — links hits across detectors to the same beam particle
- `TrackID` — 1 = primary beam particle, >1 = secondary particle

---

## Key Physics Concepts

| Term | Meaning |
|---|---|
| **Trigger efficiency** | Fraction of real beam events correctly recorded by the detector |
| **Coincidence trigger** | Requiring hits in multiple detector layers to confirm a real event |
| **Latency** | Time delay between the first and last detector signal |
| **Secondary particles** | Particles produced by beam interactions inside the detector material |
| **Momentum threshold** | Minimum momentum required for a hit to be counted as a real signal |
| **pi+ (pion)** | Positively charged pion — a common secondary particle in accelerator beamlines |

---

## About BL4S

The **Beamline for Schools (BL4S)** competition, organized by CERN, invites high school students from around the world to propose experiments to be performed at a real CERN beamline. Winning teams get to travel to CERN and conduct their experiment with support from CERN physicists.

More information: https://beamlineforschools.cern

---

*Simulation developed using G4beamline 3.08 / Geant4 11.0*
