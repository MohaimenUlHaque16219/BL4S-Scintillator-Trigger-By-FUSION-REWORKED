# BL4S 2025 — Scintillator Trigger Detector Simulation

**Competition:** Beamline for Schools (BL4S) by CERN  
**Team:** FUSION REWORKED  
**Institution:** DHAKA RESIDENTIAL MODEL COLLEGE 
**Country:** Bangladesh  

---

## What is this project?

We're a team of students from Bangladesh competing in CERN's Beamline for Schools competition. Our idea is to study how a scintillator-based trigger detector performs under different beam conditions — specifically using a pi+ (positive pion) beam ranging from 0.5 to 10 GeV/c.

Since we obviously can't build a real detector right now, we decided to simulate one using G4beamline, which is basically a front-end for Geant4 (the same simulation toolkit used by actual CERN experiments). We set up three plastic scintillator layers along a beamline, fired pi+ particles through them at different energies, and measured how well the detector responds.

The whole point is to figure out — before proposing a real experiment — whether our detector design actually works. Things like: does it catch most of the particles? How fast does it respond? At what beam intensity does it start falling apart due to dead time?

---

## Why scintillators?

Plastic scintillators are one of the most common detector types in particle physics. They're cheap, fast, and robust. When a charged particle passes through, it excites molecules in the plastic which then emit light — that light gets converted to an electrical signal.

We chose them because:
- They're fast enough for trigger applications (response in nanoseconds)
- They're used in real CERN experiments like NA61/SHINE and COMPASS
- They're simple enough that we can actually simulate and understand them

The trigger logic we implemented is called a **coincidence trigger** — the detector only fires if all three layers see a hit at roughly the same time. This cuts out most random noise and background signals.

---

## Detector Layout

```
pi+ beam →   [Scintillator 1]        [Scintillator 2]        [Scintillator 3]
             z = 100 mm              z = 400 mm              z = 700 mm
             (upstream trigger)      (middle layer)          (downstream trigger)
```

Each scintillator is 50 × 50 × 10 mm and made of G4_PLASTIC_SC_VINYLTOLUENE — 
the standard Geant4 plastic scintillator material.

We also placed thin "virtual detectors" 6mm upstream of each scintillator. These are just recording planes that log every particle passing through without actually stopping them — kind of like a camera that doesn't affect what it's filming.

| Parameter | Value |
|---|---|
| Beam particle | pi+ (PDG id = 211) |
| Beam momentum range | 0.5 — 10.0 GeV/c |
| Beam spot size | σ = 5 mm (Gaussian) |
| Scintillator size | 50 × 50 × 10 mm |
| Scintillator material | G4_PLASTIC_SC_VINYLTOLUENE |
| Detector positions | z = 100, 400, 700 mm |
| Events per run | 5000 |
| Physics list | QGSP_BERT |
| Simulation software | G4beamline 3.08 / Geant4 11.0 |

---

## What we measured

### Trigger Efficiency

This is simply: out of 5000 beam particles fired, how many actually triggered all three detectors? A particle can miss if it scatters sideways, decays before reaching the last layer, or loses too much energy in the material.

| Momentum (GeV/c) | Kinetic Energy (GeV) | Efficiency |
|---|---|---|
| 0.50 | 0.380 | 91.5% |
| 1.00 | 0.870 | 93.7% |
| 2.00 | 1.865 | 94.9% |
| 5.00 | 4.862 | 96.2% |
| 10.00 | 9.861 | 96.5% |

At low momentum, pions are more likely to scatter or decay in the material, so efficiency is lower. As momentum increases, the beam goes straighter and efficiency climbs. It flattens out around 96-97% at high energies because some losses are basically unavoidable (edge effects, geometry, etc).

---

### Trigger Latency

This is the time it takes for the signal to travel from the first detector to the last — basically the flight time of the pion across 600 mm.

| Momentum (GeV/c) | Latency |
|---|---|
| 0.50 | 2.079 ± 0.003 ns |
| 1.00 | 2.021 ± 0.000 ns |
| 5.00 | 2.002 ± 0.000 ns |
| 10.00 | 2.002 ± 0.000 ns |

The latency converges toward 2.000 ns at high energies. This makes physical sense — 600mm divided by the speed of light is exactly 2.0 ns. At high momentum the pion is traveling close to c, so it can't go faster than that. Seeing this in the simulation was actually a good sanity check that everything was working correctly.

---

### Dead Time

Every time the detector records a hit, it's "blind" for about 50 ns while it processes the signal (this is called dead time). At low beam intensities this doesn't matter much, but at high intensities the detector starts missing particles because it's still recovering from the previous hit.

We swept beam intensities from 10^4 to 10^6 particles per spill (a spill is ~400 ms at CERN's PS). The dead time fraction stays under 1% up to about 10^5 particles/spill, then starts climbing quickly.

---

### Coincidence Rate vs Beam Intensity

Related to dead time — this shows how many triple-coincidence triggers you actually get per spill. At low intensity it's basically linear. But past around 10^5 particles/spill, dead time starts eating into the coincidence rate and it rolls off from the ideal linear trend.

---

### Detector Response per Layer

We also looked at the average signal momentum recorded in each of the three layers separately. Det1 sees the beam fresh, Det2 and Det3 see it after it's already passed through material. Interestingly the response is nearly identical across layers at high momentum — the pion barely loses energy passing through 10mm of plastic.

---

## Files in this repo

```
BL4S-Scintillator-Trigger/
│
├── scintillator_trigger.g4bl     ← the actual simulation (run with g4bl)
├── run_all_energies.py           ← runs the simulation at all 11 momenta
├── analyze_detector.py           ← reads output files, makes all 6 plots
├── README.md                     ← this file
│
├── simulation_output/            ← created when you run the simulation
│   ├── momentum_500_MeV/
│   │   ├── det1.txt
│   │   ├── det2.txt
│   │   └── det3.txt
│   └── ... (one folder per energy)
│
└── plots/                        ← created when you run analyze_detector.py
    ├── efficiency_vs_momentum.png
    ├── latency_vs_momentum.png
    ├── secondary_fraction_vs_threshold.png
    ├── dead_time_vs_intensity.png
    ├── detector_response_vs_energy.png
    └── coincidence_rate_vs_intensity.png
```

---

## How to run it yourself

You'll need G4beamline (free download, includes Geant4) and Python with numpy and matplotlib.

**Install G4beamline:**
1. Download from https://g4beamline.muonsinc.com (Windows installer available)
2. Add the bin folder to your system PATH:
   `C:\Program Files\Muons, Inc\G4beamline\bin`

**Install Python packages:**
```
pip install numpy matplotlib
```

**Run everything:**
```bash
# Step 1 — simulate all energies (takes a few minutes)
python run_all_energies.py

# Step 2 — analyze and plot
python analyze_detector.py
```

**Quick single-energy test:**
```bash
g4bl scintillator_trigger.g4bl beam_momentum=500
```

---

## Output data format

G4beamline saves hit data as plain text files with these columns:

```
x(mm)  y(mm)  z(mm)  Px(MeV/c)  Py(MeV/c)  Pz(MeV/c)  t(ns)  PDGid  EventID  TrackID  ParentID  Weight
```

For our analysis the key columns are `t` (hit time), `EventID` (to match hits across layers), and `TrackID` (1 = primary beam particle, anything higher = secondary).

---

## Some things we learned

- The coincidence trigger works really well even at moderate efficiencies. Even at 91% per layer, a triple coincidence still fires about 76% of the time (0.91³ ≈ 0.75).
- Dead time is the main limiting factor at high beam intensities, not efficiency.
- The latency hitting exactly 2.000 ns at high momentum was a cool moment — it basically proved our simulation was giving physically correct results.
- 50×50mm scintillators are quite small. At the beam sigmas we used (5mm), almost all particles hit the detector, but in a real experiment with beam halo or misalignment this would be a concern.

---

## About BL4S

Beamline for Schools is a competition run by CERN where student teams from around the world propose real physics experiments to be carried out at a CERN beamline. Winning teams actually get to come to CERN and do the experiment. We think that's pretty incredible and it's why we put so much work into making this simulation as realistic as possible.

More info: https://beamlineforschools.cern

---

*G4beamline 3.08 / Geant4 11.0 — simulation done on Windows 11*
