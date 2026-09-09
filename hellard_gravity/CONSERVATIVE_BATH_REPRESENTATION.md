# Conservative-bath representation of the causal memory channels

The effective Hellard memory bank uses causal relaxors

\[
\dot m_\lambda+\lambda m_\lambda=\lambda a(t),\qquad \lambda>0.
\]

A single first-order relaxor is dissipative if treated as a fundamental isolated degree of freedom. However its causal exponential kernel has the exact positive cosine-spectrum representation

\[
\boxed{
e^{-\lambda t}
=
\frac{2\lambda}{\pi}
\int_0^\infty
\frac{\cos(\Omega t)}{\lambda^2+\Omega^2}\,d\Omega
},\qquad t\ge0.
\]

This follows from

\[
\int_0^\infty\frac{\cos(\Omega t)}{\Omega^2+\lambda^2}\,d\Omega
=\frac{\pi}{2\lambda}e^{-\lambda t}.
\]

Therefore each causal relaxor kernel can be synthesized from a continuum of ordinary oscillatory bath modes with nonnegative spectral weight

\[
\boxed{
\rho_\lambda(\Omega)=
\frac{2\lambda}{\pi(\lambda^2+\Omega^2)}\ge0.
}
\]

## Constructive parent class

A Caldeira-Leggett-type parent Hamiltonian can be written schematically as

\[
H=H_{\rm sys}+\int_0^\infty d\Omega\left[
\frac{p_\Omega^2}{2}
+\frac{\Omega^2}{2}\left(q_\Omega-\frac{c(\Omega)X}{\Omega^2}\right)^2
\right],
\]

with a counterterm included by the completed square. For nonnegative \(c(\Omega)^2\), the bath energy is bounded below. Eliminating the bath with retarded boundary/initial conditions produces a causal memory kernel whose spectral density is controlled by \(c(\Omega)^2\).

Choosing a Lorentzian positive spectral density proportional to \(\rho_\lambda\) reproduces the exponential response channel above at linear-response level. Integrating these channels over the scale-invariant measure \(d\ln\lambda\) gives a conservative-parent route to the scale-free Hellard memory continuum.

## What is proved

1. The exponential causal kernel has an exact positive oscillator-spectrum representation.
2. The spectral weight is nonnegative for all \(\Omega,\lambda>0\).
3. Therefore there exists a positive-energy oscillator-bath parent class capable of reproducing the linear causal memory channels by dephasing/retarded elimination.
4. The scale-free continuum over \(\lambda\) need not introduce a preferred clock if the measure/couplings depend only on dimensionless ratios and \(d\ln\lambda\).

## What is not yet proved

This note does **not** yet derive the full nonlinear Hellard inertial law from a unique microscopic bath Hamiltonian. In particular, the precise nonlinear coupling that must generate the low-acceleration spectral-dominance response while preserving the weak-equivalence and high-acceleration limits remains to be constructed. The result here removes the narrower objection that causal exponential memory necessarily requires fundamental negative-energy or explicitly dissipative degrees of freedom.