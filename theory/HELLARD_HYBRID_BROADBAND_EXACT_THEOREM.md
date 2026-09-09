# Hellard Exact Broadband Hybrid Resource Theorem

## Setup
Let Q(ω)=S0(ω)^†S(ω) be the passive scattering operator relative to a unitary reference, and D(ω)=I−Q(ω). Assume N orthonormal power-normalized incident channels, pointwise passivity ||Q(ω)||2≤1, active correction A(ω) with rank(A(ω))≤r<N, weighted total active budget

PΩ = ∫Ω w(ω)||A(ω)||F² dω,

and weighted passive extinction lower bound

LΩ ≤ ∫Ω w(ω) Σa Xa(ω)dω.

Let

W = ∫Ω w(ω)dω,
L̄ = LΩ/W,
B̄ = sqrt(PΩ/W).

Define the single-frequency exact Hellard value function EH(N,r,L,B) as follows. Set s=L/2 and

mmin=max(rs/N, s−2(N−r), 0),
mmax=min(s,2r).

If s≤B sqrt(r), let mhat=s. Otherwise let

mhat=[rs+(N−r)B sqrt(r)]/N.

Let m*=clip(mhat,mmin,mmax). Then

EH(N,r,L,B)=[m*/sqrt(r)−B]_+² + (L/2−m*)²/(N−r).

## Exact broadband bound
Under only the assumptions above,

EΩ ≡ ∫Ω w(ω)||D(ω)+A(ω)||F²dω

obeys

EΩ ≥ W EH(N,r,L̄,B̄).

Equivalently,

EΩ ≥ W EH(N,r,LΩ/W,sqrt(PΩ/W)).

## Why this is exact
At each frequency, passivity and extinction imply a singular-value mass constraint on D. Introducing s(ω)=L(ω)/2, controllable singular-value mass m(ω), and b(ω)=||A(ω)||F reduces the pointwise optimum to

F(s,m,b)=[m/sqrt(r)−b]_+²+(s−m)²/(N−r)

subject to linear feasibility constraints

m≥rs/N,
m≥s−2(N−r),
m≤s,
m≤2r,
s≥0,
b≥0.

F is jointly convex in (s,m,b). Weighted Jensen therefore implies

∫wF ≥ W F(s̄,m̄,b̄),

while Cauchy-Schwarz gives

b̄ ≤ sqrt(PΩ/W).

Since F is nonincreasing in b, the best allowed average correction strength is B̄=sqrt(PΩ/W). Minimizing over the averaged feasible m then gives the same scalar minimization that defines EH.

Equality is attainable in the abstract pointwise-passive model by choosing frequency-independent extremizing singular-value distributions and constant correction strength across the weighted band. Hence the broadband bound is sharp under the stated assumptions.

## Perfect-cancellation feasibility
The exact broadband abstract model permits zero residual only if

LΩ ≤ 4rW

and

PΩ ≥ LΩ²/(4rW).

Equivalently,

4rW/LΩ ≥ 1

and

4rWPΩ/LΩ² ≥ 1.

## Special cases
1. Unlimited active energy recovers the sharp rank-only broadband bound

EΩ ≥ [LΩ−4rW]_+²/[4(N−r)W].

2. When the singular-value cap is inactive,

EΩ ≥ [LΩ−2sqrt(rWPΩ)]_+²/(4NW).

3. Setting W=1 recovers the exact single-frequency theorem.

## Scope
This theorem closes the abstract finite-dimensional broadband problem under pointwise passivity, aggregate extinction information, pointwise active-rank limit, and integrated active-strength budget. It does not impose active-system causality, stability, sensor noise, finite preview, geometry, material dispersion, or a specific passive-cloak model. Those additional physical constraints can only raise the realizable residual or determine the value of LΩ.
