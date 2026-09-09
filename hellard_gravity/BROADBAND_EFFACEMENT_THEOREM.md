# Hellard broadband composite-effacement theorem

## Statement

Let a composite system have a slow center-of-mass (COM) dynamical scale lambda_s and an internal displacement spectrum xi(omega) supported on fast frequencies omega >= Omega with Omega >> lambda_s. Let the Hellard causal memory construction use the normalized higher-order band

    K_2(x) = 4 x^4 / (1 + x^2)^3.

Then the contamination of the slow-band acceleration power by the fast internal spectrum obeys

    P_leak(lambda_s)
      <= 4 lambda_s^4 \int_{Omega}^infinity |xi(omega)|^2 d ln omega.

If the characteristic slow COM displacement scale is L, so that its slow-band acceleration power is of order lambda_s^4 L^2, then the fractional contamination satisfies

    epsilon_CM
      <= 4 <xi^2>_ln / L^2,

where

    <xi^2>_ln = \int |xi(omega)|^2 d ln omega

is the logarithmic-frequency RMS internal displacement power over the fast support.

Thus the asymptotic effacement criterion is geometric: the internal RMS displacement scale must be small compared with the COM trajectory scale. Large internal accelerations do not by themselves spoil slow COM dynamics.

## Proof

For x >= 0,

    K_2(x) = 4 x^4/(1+x^2)^3 <= 4 x^4.

At the slow analysis scale lambda_s, a fast acceleration component at omega contributes

    dP_leak <= K_2(lambda_s/omega) |a_int(omega)|^2 d ln omega.

Using the bound above,

    dP_leak
      <= 4 (lambda_s/omega)^4 |a_int(omega)|^2 d ln omega.

For an internal displacement Fourier amplitude xi(omega),

    |a_int(omega)|^2 = omega^4 |xi(omega)|^2.

Therefore

    dP_leak <= 4 lambda_s^4 |xi(omega)|^2 d ln omega.

Integrating over the entire fast internal spectrum gives

    P_leak(lambda_s)
      <= 4 lambda_s^4 \int |xi(omega)|^2 d ln omega.

If the COM displacement amplitude at the slow scale is L, then

    P_CM ~ lambda_s^4 L^2,

so

    epsilon_CM = P_leak/P_CM
      <= 4 <xi^2>_ln/L^2.

QED within the stated scale-separated spectral assumptions.

## Relation to the single-harmonic result

For one internal harmonic of displacement amplitude ell, the spectral integral reduces to ell^2 and the theorem recovers

    epsilon_CM <= 4 (ell/L)^2.

## Scope and caveats

This theorem assumes:

1. the internal spectrum is supported well above the slow COM scale;
2. the relevant internal displacement spectrum is square-integrable in d ln omega;
3. no strong resonance lies near the slow COM band;
4. comparison of slow COM power uses the same causal band normalization.

The theorem does not cover comparable-frequency resonances or a divergent scale-free internal displacement spectrum extending to the slow band. Those cases require the exact K_2 kernel rather than the fast-tail bound.
