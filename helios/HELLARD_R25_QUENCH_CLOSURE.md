# HELIOS-R25 breeder quench closure

## Scope
Reduced-order systems result only. This is not a validated burn simulation or hardware design.

## Problem
R25 requires the D-D breeder pulse to disassemble before freshly produced tritium undergoes substantial secondary D-T burn.

Use the inertial disassembly estimate

\[\tau_H \sim R/c_s\]

and a secondary D-T characteristic burn time \(\tau_{DT}\).

For the current screening point, a millimeter-scale hot breeder at about 150 keV gives a hydrodynamic disassembly time of order 0.4-0.6 ns, while the secondary D-T burn-time screen is about 45 ns.

The fraction of breeder-produced tritium that burns before disassembly is approximated by

\[x_T = 1-\exp(-\tau_H/\tau_{DT}).\]

The staged-cycle neutron fraction including this leakage is approximated by

\[f_n(\tau_H)=\frac{2.45+14.1x_T}{25.60+17.6x_T}.\]

At \(\tau_H=0.5\) ns and \(\tau_{DT}=45\) ns:

- secondary D-T burn fraction: about 1.10%
- staged-cycle neutron fraction: about 10.10%

Even at 1 ns, neutron fraction is only about 10.62% in this screen.

## Corrected momentum-energy closure
Using the R25 momentum-energy closure

\[\mathcal H_{PM}=\frac{\psi^2\eta_K\left[1-f_n(1-C_n)-\frac{1/(Q\eta_d)+a}{\eta_R}\right]}{\eta_{min}(\alpha)}\]

with the reference values

- specific power: 250 kW/kg
- momentum collimation \(\psi=0.90\)
- exhaust-energy retention \(\eta_K=0.95\)
- neutron recovery \(C_n=0.31\)
- effective gain \(Q=80\)
- driver efficiency \(\eta_d=0.60\)
- auxiliary fraction \(a=0.015\)
- electrical-recovery efficiency \(\eta_R=0.75\)

we obtain approximately:

- \(\tau_H=0.5\) ns: \(\mathcal H_{PM}\approx1.139\)
- \(\tau_H=1.0\) ns: \(\mathcal H_{PM}\approx1.135\)
- \(\tau_H=5.0\) ns: \(\mathcal H_{PM}\approx1.102\)

Thus the R25 breeder-quench condition is not the dominant systems-level blocker in this reduced-order model.

## AWS stress test
A 400,000-case deterministic AWS sweep varied:

- disassembly time: 0.3-3 ns
- specific power: 200-250 kW/kg
- momentum collimation: 0.84-0.94
- exhaust-energy retention: 0.90-0.98
- effective gain: 60-110
- driver efficiency: 0.55-0.65
- electrical-recovery efficiency: 0.60-0.85
- neutron recovery: 0.20-0.35
- auxiliaries: 1-2.5%

Result:

- pass fraction of sampled design space: about 72.9%
- median surviving disassembly time: about 1.61 ns
- median surviving neutron fraction: about 11.23%
- median surviving momentum collimation: about 90.35%
- median surviving effective gain: about 85.8
- median closure number: about 1.086

These are design-space fractions, not probabilities of physical success.

## Verdict
At reduced-order level, natural hydrodynamic disassembly is fast enough to suppress most secondary D-T burn in the breeder. R25 therefore survives the breeder-quench gate.

The next hard gate is no longer quench timing. It is whether a D-D breeder pulse can achieve the required He-3 production at acceptable gain while remaining weakly tamped enough to disassemble this rapidly, and whether post-pulse fuel processing can recover the He-3 at the required throughput.
