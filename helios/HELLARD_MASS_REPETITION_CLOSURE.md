# Hellard Mass-Repetition Closure Criterion

This note extends the HELIOS reduced-order closure model with firing-cell duplication and shared-hardware mass.

For aggregate pulse rate f_agg, per-cell demonstrated rate f_cell, redundancy reserve r, installed cells are approximated by:

N_inst = ceil(f_agg / f_cell) + r

Let m_cell be mass per firing cell, M_shared shared nozzle/shield/recovery/radiator/pulse-power mass, P_fusion required fusion source power, and alpha integrated source specific power [W/kg]. Then available source mass is:

M_source = P_fusion / alpha

Define the Hellard mass-repetition closure number:

M_H = M_source / (N_inst*m_cell + M_shared)

Criterion:

M_H >= 1  -> mass/repetition closure
M_H < 1   -> architecture cannot realize the claimed integrated specific power with that cell topology.

This is a bookkeeping identity under the declared architecture, not a fundamental law of nature.

R20 reference screen:
- directed jet power: 54.68 GW
- catalyzed-D-D neutron energy fraction: 0.383
- neutron recovery: 0.31
- nozzle efficiency: 0.90
- Q_eff: 60
- driver efficiency: 0.60
- auxiliaries: 1.5% fusion energy
- net fusion-to-jet fraction after recirculation: 0.623657
- fusion source power: 87.676 GW
- at 250 kW/kg integrated source specific power: M_source = 350.7 t

Examples at 120 Hz aggregate with +3 redundant cells:
- 2 Hz/cell -> 63 installed cells. If shared hardware is 100 t, max cell mass is 3.98 t.
- 3 Hz/cell -> 43 installed cells. If shared hardware is 100 t, max cell mass is 5.83 t.
- 4 Hz/cell -> 33 installed cells. If shared hardware is 100 t, max cell mass is 7.60 t.

Therefore the old >=2 Hz and <=5 t/cell development gates do not by themselves guarantee the R20 250-kW/kg integrated specific-power target. A practical R21 target is roughly 3-4 Hz/cell, 3-4 t/cell, with ~30-40 installed cells and shared hardware below about 100 t.

A 500,000-case reduced-order screen combining joint energy closure and mass/repetition closure gave survivor medians near:
- integrated specific power 236 kW/kg
- nozzle 89.8%
- neutron recovery 31.1%
- Q_eff 83
- driver efficiency 60.5%
- aggregate rate 114 Hz
- cell rate 3.68 Hz
- cell mass 3.83 t
- shared hardware 88.5 t
- installed cells 35

Design-space fractions are not probabilities of physical success.
