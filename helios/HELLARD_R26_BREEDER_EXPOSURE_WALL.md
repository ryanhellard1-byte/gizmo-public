# HELIOS-R26 Breeder Exposure Wall

## Result

The short-lived D-D breeder concept does not remain low-neutron and high-gain at the same time once the same density-time exposure is applied consistently to D-D production and secondary D-T burn.

The relevant dimensionless exposure is

x = n_D <sigma v>_DD tau.

Because <sigma v>_DT / <sigma v>_DD is much larger than unity over the 50-500 keV range, increasing n*tau to make useful D-D also makes the freshly produced tritium burn rapidly.

Using NRL 2023 tabulated Maxwellian reactivities in a normalized 0-D reaction network, followed by a later idealized burn of all surviving He3 with deuterium, the optimistic Pareto frontier is approximately:

- cycle neutron fraction <= 12%: Q_cycle <= 0.21
- <= 15%: Q_cycle <= 0.41
- <= 20%: Q_cycle <= 1.12
- <= 25%: Q_cycle <= 2.02
- <= 30%: Q_cycle <= 3.25

These Q values are intentionally optimistic upper bounds. The breeder driver is charged only the ideal fully ionized thermal inventory and the later D-He3 stage is assigned Q=80. Compression, transport, radiation, mix, driver inefficiency, and separation losses are omitted, so a real system would perform worse.

## Interpretation

Natural hydrodynamic disassembly can be much faster than a nominal D-T secondary-burn clock time at one fixed density, but raising density to restore D-D productivity raises both D-D and D-T reaction rates. The key variable is n*tau, not clock time alone.

Therefore HELIOS-R26 cannot use a low-neutron, thermally driven D-D breeder as a propulsion-scale onboard He3 factory while also preserving the high effective gain required by the 30-day architecture.

## Status

R26 low-neutron breeder fuel-factory branch: REJECTED at reduced-order level.

This does not prove that all possible nonthermal or species-selective D-D breeding mechanisms are impossible. It rejects the present homogeneous thermal-plasma breeder model.
