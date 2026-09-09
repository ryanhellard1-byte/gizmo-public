# Boost-covariant first-order velocity-memory construction

## Motivation

A fundamental local completion should not need acceleration itself as the primitive variable. Direct acceleration couplings in an ordinary local action can introduce higher-derivative issues. A cleaner causal realization uses a continuum of velocity-tracking states.

For each positive memory rate lambda define

    du_lambda/dt + lambda u_lambda = lambda v(t).

Under a Galilean boost by constant V,

    v -> v + V,
    u_lambda -> u_lambda + V,

so the equation is covariant and the lag variable v-u_lambda is boost invariant.

Define the logarithmic-scale derivative

    q_lambda = d u_lambda / d ln(lambda)

and the acceleration-band variable

    c_lambda = d q_lambda / dt.

For a harmonic velocity v(t)=V exp(i omega t),

    u_lambda/V = lambda/(lambda+i omega),

therefore

    q_lambda/V = i omega lambda/(lambda+i omega)^2,

and

    c_lambda/V = -omega^2 lambda/(lambda+i omega)^2.

Since the physical acceleration amplitude is A=i omega V,

    |c_lambda|^2/|A|^2
      = omega^2 lambda^2/(lambda^2+omega^2)^2.

This is exactly the first-order causal acceleration-power band obtained previously from an acceleration-driven relaxation bank.

Consequently

    2 int_0^infinity |c_lambda|^2 d ln(lambda) = |A|^2.

Thus the scale-free causal spectrometer can be implemented using only first-order velocity-memory dynamics. No preferred clock is introduced when the continuum is integrated with d ln(lambda).

## What this proves

1. The causal band construction has a Galilean-covariant primitive representation.
2. Primitive acceleration coupling is not necessary.
3. The local auxiliary equations are first order in time.
4. The exact normalized single-frequency acceleration-power identity is retained.

## What this does not prove

The relaxation equations by themselves are an effective dissipative representation. A conservative microscopic parent still requires either a positive-energy continuum bath whose retarded elimination gives these equations, or an in-in/doubled-history formulation. The nonlinear MOND-like amplitude dependence also cannot arise from a purely Gaussian bath with only linear system-bath coupling.
