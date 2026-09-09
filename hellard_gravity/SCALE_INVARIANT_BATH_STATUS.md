# Scale-invariant bath completion status

## Result

A finite set of linear causal memory variables with constant relaxation rates cannot realize an exactly scale-free Hellard memory law without introducing new dimensional time scales. A continuum of scales is required unless the rates are themselves generated dynamically from the trajectory.

The causal continuum construction used in this branch is

\[
\dot m_\lambda+\lambda m_\lambda=\lambda a(t),\qquad \lambda>0,
\]

with scale-invariant measure \(d\ln\lambda\).

For a harmonic acceleration \(a=Ae^{i\omega t}\),

\[
m_\lambda=A\frac{\lambda}{\lambda+i\omega}e^{i\omega t}.
\]

Defining

\[
q_\lambda=\partial_{\ln\lambda}m_\lambda,
\]

gives

\[
|q_\lambda|^2=|A|^2\frac{\omega^2\lambda^2}{(\lambda^2+\omega^2)^2},
\]

and the exact identity

\[
2\int_0^\infty |q_\lambda|^2\,d\ln\lambda=|A|^2.
\]

Thus the continuum reconstructs harmonic acceleration power without a preferred clock.

A higher-order causal band

\[
b_\lambda=(\partial_{\ln\lambda}^2-\partial_{\ln\lambda})m_\lambda
\]

has normalized power kernel

\[
K_2(x)=\frac{4x^4}{(1+x^2)^3},\qquad x=\lambda/\omega,
\]

with

\[
\int_0^\infty K_2(x)\,d\ln x=1.
\]

For contamination of a slow mode by a fast mode with frequency ratio \(R=\omega_f/\omega_s\gg1\),

\[
K_2(1/R)\sim4R^{-4}.
\]

This supplies a parameter-free high-frequency effacement mechanism.

## Literature boundary

Scale-invariant environments and continuum baths are not a novel Hellard claim. Contemporary open-system work studies scale-invariant baths and their non-Markovian kernels. The Hellard-specific research target is narrower:

1. couple a scale-free causal memory continuum to modified inertia;
2. preserve the isolated low-acceleration law;
3. obtain high-frequency composite-body effacement;
4. derive a distinctive wide-binary/galaxy phenomenology from the same coupling;
5. embed the response in a conservative parent theory or Schwinger-Keldysh / doubled-history formulation.

## Remaining parent-theory issue

The first-order memory equations above are causal but dissipative when treated alone. A fundamental completion therefore requires either:

- a positive-energy continuum bath whose retarded equations reduce to the memory system after the bath is integrated out, or
- an in-in/doubled-history effective action appropriate to an initial-value problem.

No claim of a completed conservative microscopic theory is made yet.
