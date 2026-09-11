# MENDS-X G0/G1 femtoamp breadboard execution plan

## Purpose
Produce the first physical MENDS-X evidence without needing the neutral sensor head or a vacuum chamber.

## Architecture
Two guarded ADA4530-1 electrometer channels are used as capacitive integrators with nominal 1 pF C0G/NP0 feedback capacitors and guarded dry-reed reset relays. Channel A/B layouts should be mirrored, high-impedance nodes fully guarded, and the analog section enclosed in a conductive shield.

For an ideal integrator, dV/dt = I/C. With C=1 pF: 0.5 fA -> 0.5 mV/s; 1 fA -> 1 mV/s; 5 fA -> 5 mV/s; 10 fA -> 10 mV/s.

## G0 dark baseline
Configuration: electron source absent/off; steering driver disconnected; guarded inputs capped/shielded; enclosure closed; board temperature logged.

Sequence:
1. Clean high-Z area and handle with gloves.
2. Warm up >=30 min.
3. Reset integrator and wait declared post-reset blanking interval.
4. Acquire >=30 min uninterrupted dark data per channel.
5. Repeat after power cycle and reset operation.
6. If practical repeat at two board temperatures.

Report mean equivalent current, RMS, P95 absolute current, drift slope, A/B difference, Allan deviation, temperature and reset-settling curve.

Preferred engineering gate: dark RMS <=0.5 fA equivalent over declared science bandwidth, with no unexplained drift large enough to consume the P95 allocation.

## G1 steering-only synchronous null
Connect isolated bipolar steering driver to representative electrode/load fixture. Electron source remains OFF and no gas signal is present.

Sequence:
1. Exercise 20 and 80 V/m-equivalent states or their breadboard voltage equivalents.
2. Use intended blank -> integrate -> sample timing.
3. Acquire >=1000 steering cycles.
4. Repeat at multiple switching rates.
5. Run steering-driver-off control.
6. Perturb cable routing/grounding if pickup appears.

Primary observable: synchronous false current correlated with steering state.

Preferred gate: <=0.5 fA RMS equivalent after declared blanking/filter bandwidth.

Failure diagnosis order: capacitive pickup; shared return impedance; enclosure/chassis coupling; reset recovery; DAQ/USB ground injection; dielectric relaxation/surface contamination.

## Calibration injection
Before interpreting femtoamp data, inject known current/charge using either I=C*dV/dt or I_avg=C*deltaV*f. Propagate capacitor and source uncertainty.

## Evidence package
Every run gets immutable raw CSV, configuration ID, circuit revision, channel calibration, software revision, timestamps, temperature/humidity, operator notes and SHA-256 checksum.

## Procurement decision
Default to custom guarded prototype rather than the expensive ADA4530-1 evaluation board. Current web checks on 2026-09-10 found the ADA4530-1 IC around $42, the official eval board around $755, 1 pF C0G capacitors around $0.14, and a suitable low-level dry-reed relay around $15.40. The current custom breadboard estimate is about $281 before shipping/tax and any bench equipment already owned. These prices are procurement snapshots, not fixed quotes.
