# Wide-binary action test: failure of universal diagonal MOND-like inertia

Current stationary action benchmark uses a diagonal nonlinear inertia branch plus a reciprocal quartic environmental interaction.

For a 1 Msun equal-order wide-binary scale and a_H = 1.12e-10 m/s^2, the diagonal equation

    a * mu(a/a_H) = g_N,
    mu(x)=x/sqrt(1+x^2)

already predicts large circular-speed enhancements before the quartic environmental term is included.

Representative circular-orbit results:

- 1 kAU: v/v_N ~ 1.000
- 3 kAU: v/v_N ~ 1.007
- 5 kAU: v/v_N ~ 1.044
- 10 kAU: v/v_N ~ 1.252
- 20 kAU: v/v_N ~ 1.686
- 30 kAU: v/v_N ~ 2.045

The reciprocal quartic environmental term only increases the enhancement for positive epsilon in the present sign convention; e.g. epsilon=1 gives v/v_N ~ 1.287 at 10 kAU and ~2.81 at 30 kAU.

Therefore the current action completion FAILS a Newtonian-leaning wide-binary interpretation independently of the Cassini result. The failure is caused by applying the same diagonal low-acceleration inertia law to every low-acceleration subsystem.

Required structural change:

1. Preserve the isolated/dominant-mode galaxy branch that yields the RAR/BTFR.
2. Suppress that diagonal modification for a low-acceleration subsystem embedded in a stronger slowly varying background.
3. Do this from a stationary reciprocal action, not by restoring an asymmetric hand-inserted frequency response.
4. Recompute Cassini after the new background-dependent diagonal term is derived.

This is a kill criterion, not a tuning request: a universal local-in-mode diagonal law a*mu(a/a_H)=g_N cannot be the final Hellard modified-inertia action if clean wide-binary data remain Newtonian.