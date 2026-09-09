# Hellard Law Broadband Physical Validation: Exact 2-D PEC Cylinder

## Model
Use the exact 2-D PEC-cylinder partial-wave scattering eigenvalues

S_m(ka) = -H_m^(2)(ka)/H_m^(1)(ka),
D_m = 1-S_m,
X_m = 2 Re(D_m)=|D_m|^2.

For each frequency sample, sort |D_m| and split the modal energy into a controllable head of rank r and an uncontrollable tail.

## Exact active-energy allocation across frequency
Let h_j be the Frobenius norm of the controllable rank-r head at frequency sample j. Given total active-energy budget

P = sum_j b_j^2,

the exact minimizer of

sum_j (h_j-b_j)^2

subject to the quadratic budget is

b_j = alpha h_j,
alpha = sqrt(P / sum_j h_j^2),

provided P does not exceed the total head energy. Therefore the exact physical residual is

E_actual = (1-alpha)^2 sum_j h_j^2 + sum_j T_j,

where T_j is the uncontrollable tail energy.

## Campaign
Bands in electrical size ka:
- 0.5 to 1.5
- 1 to 3
- 2 to 5
- 4 to 8

Each band used 41 uniformly spaced samples. Three active-rank fractions were tested per band, for 12 broadband cases total. The total active-energy budget was set to 35% of the energy required to cancel all controllable modal heads.

## Result
- Broadband physical cases: 12
- Hellard broadband-bound violations: 0
- Smallest observed physical-minus-bound margin: 40.28249084641042

The exact physical PEC-cylinder broadband residual stayed above

E_Omega >= W E_H(N,r,L_Omega/W,sqrt(P_Omega/W))

in every tested case.

## Interpretation
This directly tests the exact broadband Hellard value function against a dispersive Maxwell scattering spectrum and an exactly optimized cross-frequency active-energy allocation. The physical cylinder lies strictly above the universal resource envelope, as expected for a specific non-extremizing modal distribution.
