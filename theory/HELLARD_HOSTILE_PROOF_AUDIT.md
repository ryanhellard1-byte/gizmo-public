# Hellard Hybrid Electromagnetic Resource Theorem — Hostile Proof Audit

This audit treats the theorem as if the goal were to reject it. The strongest corrected formulation uses an N-dimensional incident projector P and allows output leakage into a larger scattering space.

## Strengthened setup
Let S0 be unitary, S passive, Q=S0^†S, D=I-Q, and let P project onto an N-dimensional orthonormal power-normalized incident subspace. Define T=DP. Let

X_a=2 Re <x_a,Dx_a>

for an orthonormal basis of ran(P), with sum_a X_a >= L. Let the active correction satisfy rank(AP)<=r and ||AP||_F<=B. The residual is

E=||(D+A)P||_F^2.

## Extinction bridge
Because

sum_a X_a = 2 Re tr(PDP),

we obtain

L/2 <= |tr(PDP)| <= ||PDP||_* <= ||DP||_* = ||T||_*.

Passivity gives ||Q||_2<=1, hence ||D||_2<=2 and therefore ||T||_2<=2. Since T has at most N nonzero singular values tau_i,

sum_i tau_i >= L/2,  0<=tau_i<=2.

## Exact optimization
At the optimum the total singular-value mass can be taken equal to s=L/2. Let m be the mass assigned to the top r controllable singular directions. The exact feasible interval is

m_min=max(r s/N, s-2(N-r), 0),
m_max=min(s,2r).

At fixed m, Cauchy-Schwarz shows the optimum equalizes the head and tail singular values, giving

F(m)=[m/sqrt(r)-B]_+^2 + (s-m)^2/(N-r).

For 0<r<N the unconstrained minimizer is

m_hat=s  if s<=B sqrt(r),

m_hat=[r s+(N-r)B sqrt(r)]/N otherwise.

Let m_star=clip(m_hat,m_min,m_max). Then

E_H(N,r,L,B)=[m_star/sqrt(r)-B]_+^2+(L/2-m_star)^2/(N-r).

Boundary ranks:

E_H(N,0,L,B)=L^2/(4N),

E_H(N,N,L,B)=[L/(2 sqrt(N))-B]_+^2.

## Strengthened theorem
For any passive S relative to unitary S0, any N-dimensional incident projector P, and any active correction A satisfying rank(AP)<=r and ||AP||_F<=B, if

L <= 2 Re tr(PDP),

then

||(D+A)P||_F^2 >= E_H(N,r,L,B).

The bound is sharp over the abstract class of contractive Q.

## Sharpness
Choose T positive diagonal on ran(P) with the equalized extremizing singular spectrum and extend D by zero outside ran(P). Since each d_i lies in [0,2], Q=I-D has diagonal entries in [-1,1] and is contractive. Choose AP aligned with the first r singular directions using the optimal Frobenius-ball projection. Equality is attained in every step.

## Hostile findings
1. Square-matrix-only wording: CLOSED by T=DP formulation; output leakage is allowed.
2. Extinction is only a lower bound: CLOSED; minimum occurs at the minimum allowed singular-value burden.
3. Nonnormal D: CLOSED; only trace <= nuclear norm is used, with sharpness supplied by a separate diagonal construction.
4. Active orientation: CLOSED by unitary invariance and Eckart-Young-Mirsky/von Neumann structure.
5. Singular-value cap: CLOSED from ||D||_2<=||I||+||Q||<=2.
6. Passive extremizer: CLOSED in the abstract contractive class.
7. Reciprocity/locality/causality/geometry: SCOPE LIMITATIONS, not proof failures. Imposing them can only restrict realizability further.
8. Calling it a new law of nature: NOT YET JUSTIFIED. The defensible name today is Hellard Hybrid Electromagnetic Resource Theorem pending specialist novelty review and external peer validation.

## Prior-art snapshot
Targeted searches found neighboring work on passive integrated-extinction limits, absorption/scattering tradeoffs, finite-source active cloaks, SVD-based active field control, scattering-matrix singular values, and classical low-rank approximation. No targeted search result located the same exact extinction-to-rank-and-Frobenius-budget value function. This is encouraging but is not a novelty certificate.
