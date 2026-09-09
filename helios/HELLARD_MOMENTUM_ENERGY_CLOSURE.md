# Hellard Momentum-Energy Closure

## Purpose

This note corrects an important ambiguity in earlier HELIOS reduced-order studies: published magnetic-nozzle `momentum efficiency` is not the same quantity as energy-conversion efficiency.

Historical NASA/Los Alamos work describes ~80% nozzle efficiency as conversion of spherically radial plasma momentum into axial impulse. Modern 2026 experiments likewise report momentum efficiency from measured impulse.

## Definitions

Let

- `psi` = actual axial momentum flux divided by the maximum momentum flux consistent with the remaining exhaust kinetic power,
- `eta_K` = fraction of usable post-recovery plasma energy retained as exhaust kinetic/enthalpy energy that can be converted by the nozzle,
- `f_n` = neutron-energy fraction of fusion output,
- `C_n` = neutron-energy recovery fraction into useful plasma,
- `Q_eff` = degraded/effective fusion gain,
- `eta_d` = electrical driver efficiency,
- `a` = auxiliary electrical demand as a fraction of fusion energy,
- `eta_R` = plasma-to-electric recovery efficiency,
- `eta_min(alpha)` = minimum directed propulsive efficiency required by the mission at integrated source specific power `alpha`.

Available useful plasma-energy fraction before electrical extraction:

`U = 1 - f_n(1-C_n)`

Electrical energy that must be extracted from the plasma per unit fusion energy:

`E_extract/E_f = (1/(Q_eff*eta_d) + a)/eta_R`

Remaining usable exhaust-energy fraction:

`R = U - (1/(Q_eff*eta_d) + a)/eta_R`

For mass flow `mdot` and exhaust kinetic power `P_K`, the maximum momentum flux allowed by energy conservation is

`F_max = sqrt(2*mdot*P_K)`.

Define

`psi = F/F_max`.

Then the directed-equivalent jet power represented by thrust is

`P_dir = F^2/(2*mdot) = psi^2 P_K`.

Therefore the corrected reduced-order closure number is

`H_PM = psi^2 * eta_K * R / eta_min(alpha)`.

The propulsion side closes only when

`H_PM >= 1`.

## R22 reference consequence

Using catalyzed D-D values near

- `f_n = 0.383`,
- `C_n = 0.31`,
- `Q_eff = 80`,
- `eta_d = 0.60`,
- `a = 0.015`,
- `eta_R = 0.80`,
- `alpha = 250 kW/kg`,

we obtain

`R ~= 0.69094`.

At perfect `eta_K=1`, closure requires approximately

`psi >= 0.936`.

At `eta_K=0.95`, the required momentum efficiency rises to approximately

`psi >= 0.955`.

At `eta_K=0.90`, it rises to approximately

`psi >= 0.986`.

Thus an 80% momentum-efficiency nozzle is nowhere near adequate for the current 30-day R22 mission point under this definition. The historical 80% figure cannot be reused as an 80% energy multiplier.

## Claim boundary

This is a reduced-order conservation screen, not a validated magnetic-nozzle model. Real plasma flow can redistribute thermal, magnetic, and kinetic energy, and the exact relation between measured impulse efficiency and downstream directed kinetic energy must be extracted from experiment or full MHD/PIC simulation.

The key correction is definitional and unavoidable: momentum efficiency and energy efficiency must be tracked separately.
