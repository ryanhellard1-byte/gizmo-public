# Hellard Law Physical Validation: Exact 2-D PEC Cylinder

## Purpose
This test replaces the abstract extinction input L with a concrete electromagnetic scattering model and asks whether an optimized finite-rank active correction can beat the Hellard resource bound.

## Exact passive scattering model
For a perfectly conducting circular cylinder in 2-D, using cylindrical partial-wave channels m=-M,...,M,

S_m(ka) = - H_m^(2)(ka) / H_m^(1)(ka).

For a lossless PEC cylinder, |S_m|=1. Taking the reference propagation as S0=I,

D_m = 1 - S_m.

The normalized extinction for each unit-power channel is

X_m = 2 Re(D_m).

Because |S_m|=1,

X_m = |D_m|^2

exactly. Therefore the physical aggregate extinction burden used in the Hellard theorem is

L = sum_m X_m.

## Active correction
For each physical cylinder case, the active correction is allowed rank r and Frobenius budget B. Since D is diagonal in the cylindrical-wave basis, the best physical rank-r correction attacks the r channels with largest |D_m|. If h is the vector of those r magnitudes and t is the remaining tail, the actual best residual for that fixed cylinder is

E_actual = [||h||_2 - B]_+^2 + ||t||_2^2.

This is then compared against the universal Hellard value function E_H(N,r,L,B), which optimizes over all passive scattering operators having the same aggregate extinction L.

## Numerical campaign
Tested electrical sizes:

ka = 0.5, 1, 2, 3, 5, 8.

For each ka, the cylindrical channel truncation was

M = ceil(ka + 6),
N = 2M + 1.

Four rank fractions were tested per electrical size, giving 24 physical cases total. The active strength B was set to 50% of the Frobenius strength required to cancel the selected top-r physical channels.

## Results
- Physical cases tested: 24
- Hellard-bound violations: 0
- Smallest observed E_actual - E_H margin: 0.8696027077440119
- Maximum numerical | |S_m| - 1 | error: 2.22e-16
- Maximum numerical |X_m - |D_m|^2| error: 8.88e-16

The physical PEC cylinder always remained above the abstract Hellard lower envelope, as expected. The theorem is a best-case resource bound over all passive operators with the same aggregate extinction; a specific scatterer generally has a non-optimal modal distribution and therefore sits strictly above the envelope.

## Interpretation
This is the first direct electromagnetic validation loop in which L is computed from a physical Maxwell scattering solution rather than inserted symbolically. It does not prove historical novelty and it does not yet validate arbitrary 3-D geometries, material dispersion, or a full-wave finite-element cloak. It does show that an exact canonical electromagnetic scatterer obeys the Hellard resource inequality over the tested channel/rank/resource cases.

## Next falsification targets
1. Dielectric and lossy cylinders, so Q is contractive but not unitary.
2. Passive multilayer cylindrical cloaks, not only a bare PEC target.
3. Frequency-integrated campaigns testing the broadband Hellard theorem.
4. Independent FDTD/FEM reproduction in a solver that does not use the same partial-wave diagonalization.
