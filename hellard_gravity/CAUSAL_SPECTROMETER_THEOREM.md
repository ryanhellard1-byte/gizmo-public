# Hellard causal spectrometer theorem

## Construction

For every relaxation rate lambda>0, introduce a causal memory state

    dot m_lambda + lambda m_lambda = lambda a(t).

Define its logarithmic scale derivative

    q_lambda = partial m_lambda / partial ln(lambda).

To estimate power causally, introduce

    dot e_lambda + 2 lambda e_lambda = 2 lambda q_lambda^2.

All equations are local in time and require only initial data. There is no preferred relaxation rate because the continuum covers lambda>0 and the natural scale measure is d ln(lambda).

## Harmonic theorem

For

    a(t)=A cos(omega t)

after transients, the complex transfer function of q is

    q/A = i omega lambda / (lambda+i omega)^2.

Therefore the time-averaged power estimator satisfies

    4 <e_lambda>
      = 2 A^2 omega^2 lambda^2/(lambda^2+omega^2)^2
      = A^2 K(ln(lambda/omega)),

where

    K(u)=1/(2 cosh^2 u).

Since

    integral_{-infinity}^{infinity} K(u) du = 1,

we have the exact reconstruction identity

    4 integral_0^infinity <e_lambda> d ln(lambda) = A^2.

Thus the causal auxiliary continuum acts as a normalized spectrometer on logarithmic frequency scale.

## Mode separation

For a second harmonic whose frequency differs by a factor R, the kernel leakage at the other mode's center is

    K(ln R)=1/[2 cosh^2(ln R)].

For R>>1,

    K(ln R) ~ 2/R^2.

Hence widely separated dynamical modes are automatically distinguished without inserting a preferred time scale or an arbitrary power-law spectral cutoff.

## Interpretation and limitation

For sums of sufficiently separated stationary harmonics, long-time averaged cross terms vanish and the measured scale-energy field is the convolution of the line-power spectrum with K in log frequency. This gives a causal route to the spectral-dominance variables used in the reduced Hellard phenomenology.

This theorem does not by itself provide the final fundamental gravity action. The e_lambda dynamics are dissipative effective variables; a closed fundamental completion would require an explicit bath, doubled Galley action, or Schwinger-Keldysh/in-in construction.
