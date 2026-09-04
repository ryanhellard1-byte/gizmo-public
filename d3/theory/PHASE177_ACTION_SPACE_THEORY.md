# Phase 177 — D3 Action-Space Jump Theory

## Verdict

**EXACT UNEQUAL-MASS JUMP THEOREM: DERIVED.**

**FINITE-JUMP ACTION-SPACE BOLTZMANN-POISSON FORMULATION: DEFINED.**

**COMMON-TEMPERATURE = COMMON-COMPOSITION SHORTCUT: REJECTED.**

**QUANTITATIVE 80-GYR HALO SOLUTION: NOT YET CLAIMED.**

This phase does not invent a new particle interaction. The D3/Yang-matched HH/LL/HL scattering laws remain the microscopic input. The new result is a cleaner kinetic statement of what unequal-mass elastic scattering must do in phase space, and what state variables are required once isotropic `f(E)` closures fail.

The old precision statement `C_HL ~= 0.9923` is not used. Phase 138 revoked that scalar number as a frozen prediction after the orbit-second-moment estimate proved horizon dependent. Phases 139–147 established that the physically relevant transport is nonlocal and eventually anisotropic. Phase 177 starts from that corrected frontier.

## 1. Exact event-level jump theorem

Let an H particle of mass `m_H` and an L particle of mass `m_L` collide elastically at the same position `x`. Define

```text
r = m_H/m_L.
```

The D3 center-of-mass scattering map has

```text
Delta v_H =  (m_L/(m_H+m_L)) Delta g
Delta v_L = -(m_H/(m_H+m_L)) Delta g
```

for the change `Delta g` of the relative-velocity vector. Therefore

```text
Delta v_L = -r Delta v_H.
```

For the frozen D3 mass ratio `r=3`,

```text
Delta v_L = -3 Delta v_H.
```

This is exact event by event and does not depend on the scattering angle, the Rutherford velocity scale, the halo profile, or a transport closure.

### Specific orbital energy

During the instantaneous collision the common gravitational potential is fixed, so for

```text
epsilon_a = v_a^2/2 + Phi(x)
```

pair energy conservation gives

```text
m_H Delta epsilon_H + m_L Delta epsilon_L = 0.
```

Hence

```text
Delta epsilon_L = -r Delta epsilon_H.
```

At `r=3`, the light particle receives three times the specific orbital-energy jump in the opposite direction.

### Specific angular momentum

For the specific angular-momentum vector

```text
ell_a = x cross v_a,
```

the common collision position gives

```text
Delta ell_L = x cross Delta v_L
            = -r x cross Delta v_H
            = -r Delta ell_H.
```

This statement applies to the vector increment. It must not be confused with the nonlinear change in the scalar magnitude `|ell|`.

### Exact second-jump asymmetry

Squaring any of the three exact vector/scalar jump identities gives, event by event,

```text
|Delta v_L|^2       = r^2 |Delta v_H|^2
(Delta epsilon_L)^2 = r^2 (Delta epsilon_H)^2
|Delta ell_L|^2     = r^2 |Delta ell_H|^2.
```

Thus at `r=3`, the raw specific second jump moments carry an exact factor

```text
r^2 = 9.
```

This is a kinematic statement before orbit averaging. It does **not** imply that the final diffusion coefficient of `J_r`, the density-profile response, or the 80-Gyr segregation amplitude is exactly nine times larger for L. The action map is nonlinear and the two species occupy different orbits as the halo evolves.

## 2. Why local equipartition does not end segregation

For an isotropic species in spherical hydrostatic balance,

```text
dP_a/dr = -rho_a dPhi/dr.
```

If H and L share the same local kinetic temperature `T(r)`, then

```text
P_a = n_a k T,
rho_a = m_a n_a.
```

Therefore

```text
d ln n_a/dr = -m_a Phi'(r)/(kT) - d ln T/dr.
```

Subtract the L equation from the H equation:

```text
d ln(n_H/n_L)/dr = -(m_H-m_L) Phi'(r)/(kT).
```

For ordinary attractive spherical gravity, `Phi'(r)>0`. If `m_H>m_L`, then

```text
 d ln(n_H/n_L)/dr < 0.
```

The heavy-to-light number ratio must increase inward on the common-temperature hydrostatic manifold.

This resolves an apparent puzzle exposed by Phase 142. The local H-L thermal exchange moment can approach zero near equipartition while the system still has a nonzero compositional/orbital relaxation problem. Equal temperature is only one equilibrium condition. It is not equal spatial composition.

This relation is standard kinetic/hydrostatic physics applied to the D3 two-species problem. It is not claimed as a new fundamental law.

## 3. The correct state is action-resolved

Phase 146 showed that forced spherical isotropic `f(E)` continuation leaves the realizable isotropic-DF manifold. Phase 147 crossed that false boundary by retaining angular momentum. Therefore the minimum reduced collisionless state is action-resolved:

```text
F_a(J,t),  a in {H,L}
J = (J_r,L)
```

for a spherical mean field, or an explicit phase-space ensemble when orbital phase cannot be consistently averaged out.

The instantaneous collision changes `(E,L)` and therefore changes `J_r(E,L;Phi)`. For a small jump in a fixed potential,

```text
dE = Omega_r dJ_r + Omega_phi dL,
```

so

```text
dJ_r = (dE - Omega_phi dL)/Omega_r.
```

The exact factor-three specific energy and angular-momentum-vector jumps therefore feed directly into the first and second action jump moments, but no exact factor-three rule is asserted for `Delta J_r` itself because the action map and orbital frequencies are nonlinear and orbit dependent.

## 4. Finite-jump orbit-averaged collision operator

A Fokker-Planck approximation is not required at the formal level. D3 can be written as a finite-jump master equation in actions.

Let

```text
W_Phi(J_H',J_L' | J_H,J_L)
```

be the orbit-averaged transition kernel for one H-L collision in the current potential. Schematically,

```text
W_Phi = integral dtheta_H dtheta_L dOmega
        delta^3[x_H(theta_H)-x_L(theta_L)]
        g (d sigma_HL/dOmega)
        delta[J_H' - J(x,v_H')]
        delta[J_L' - J(x,v_L')].
```

The post-collision velocities `(v_H',v_L')` are generated by the exact D3 unequal-mass Rutherford map. The orbit angles are integrated with the appropriate phase-volume/collision weighting.

The H marginal then obeys a gain-loss equation of the form

```text
partial_t F_H(J_H) = integral dJ_L dJ_H' dJ_L'
    [ W_Phi(J_H,J_L | J_H',J_L') F_H(J_H') F_L(J_L')
    - W_Phi(J_H',J_L' | J_H,J_L) F_H(J_H) F_L(J_L) ].
```

There is an analogous equation for L.

Self-gravity closes the system:

```text
n_a(r,t) = orbit_projection[F_a; Phi]

nabla^2 Phi = 4 pi G [m_H n_H + m_L n_L].
```

If actions are used as the slowly evolving coordinates, the collisionless part of the dynamics is absorbed into orbital averaging and the adiabatic invariance of the actions during sufficiently slow potential evolution. In a numerical implementation, the Phase-151/152 exact fixed-L radial-action inversion is the corresponding discrete remap contract.

## 5. Detailed-balance target in a fixed potential

For a closed system in a fixed external potential, elastic microscopic reversibility admits the Maxwell-Boltzmann stationary family

```text
f_a*(x,v) proportional to exp[-beta m_a (v^2/2 + Phi(x))].
```

Consequently

```text
n_a(r) proportional to exp[-beta m_a Phi(r)]
```

and

```text
n_H/n_L proportional to exp[-beta (m_H-m_L) Phi(r)].
```

This reproduces the hydrostatic ratio-gradient identity above.

A self-gravitating SIDM halo with escape and negative-heat-capacity gravothermal evolution need not reach this canonical fixed-potential state. The result is used as a detailed-balance direction/check, not as an 80-Gyr halo solution.

## 6. What is genuinely new in the project formulation

Mass segregation, orbit-averaged kinetic theory, and action-space Fokker-Planck methods are not new ideas by themselves. The project-specific synthesis is narrower:

1. use the frozen velocity-dependent, finite-angle D3/Yang SIDM differential laws;
2. retain exact unequal-mass H-L collision kinematics;
3. keep the finite action jumps instead of immediately forcing a diffusion limit;
4. couple the resulting H/L action distributions to common self-gravity;
5. test the resulting theory against the preregistered live-GIZMO SIDMx/SIDM2v/HL-off campaign with no post-output retuning.

A concise name for the candidate reduced theory is:

**D3 finite-jump action-space Boltzmann-Poisson renewal theory.**

That is an effective kinetic theory for a particular two-component SIDM model. It is not a theory of quantum gravity and is not comparable in scope to string theory.

## 7. Falsifiable predictions

Before viewing production outputs, the theory predicts the following qualitative signs for the unequal-mass H-L channel:

- local H-to-L energy transfer until the relevant thermal-exchange moment approaches equipartition;
- non-identical H/L action-space renewal even when that local thermal-exchange moment is small;
- dynamically generated species-dependent anisotropy rather than permanent isotropic `f(E)` evolution;
- heavy enrichment toward the inner halo and light enrichment toward larger actions/radii;
- declining H-L overlap can self-throttle the subsequent cross-collision rate;
- removing H-L collisions must remove the specifically cross-driven part of the signal.

The quantitative amplitudes, convergence, physical clock, and 80-Gyr profiles remain predictions to be measured by the frozen production campaign.

## 8. Phase-177 executable gate

`phase177_action_space_jump_theorem.py` samples the exact D3 Rutherford inverse-CDF and unequal-mass center-of-mass scattering rule and requires:

- pair momentum conservation better than `2e-12`;
- pair kinetic-energy conservation better than `2e-12`;
- the exact velocity-jump ratio;
- the exact specific-energy-jump ratio;
- the exact specific-angular-momentum-vector jump ratio;
- all three second jump-moment ratios equal `9` to `2e-12` fractional tolerance;
- a numerical consistency check of the common-temperature hydrostatic segregation identity.

Passing this gate proves the algebra/implementation-level theorem. It does not replace the live halo experiment.

## Claim boundary

The strongest defensible statement after Phase 177 is:

> The D3/Yang unequal-mass elastic collision law has an exact species-asymmetric jump structure. A self-consistent reduced description therefore belongs in action-resolved phase space, where local thermal equipartition and global compositional/orbital relaxation are distinct conditions. The resulting finite-jump action-space Boltzmann-Poisson equation is a falsifiable kinetic framework whose quantitative halo predictions remain subject to the frozen live-GIZMO production and blind convergence gates.

No dark-matter discovery or experimental confirmation is claimed by this derivation alone.
