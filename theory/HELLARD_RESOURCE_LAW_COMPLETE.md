# Hellard Hybrid Electromagnetic Resource Law — Complete Finite-Dimensional Form

## Setup
Let Q=S0^†S and D=I−Q, where S0 is unitary and Q is contractive. Consider N orthonormal power-normalized incident channels and suppose total normalized extinction obeys sum_a X_a >= L. Let active correction A satisfy rank(A)<=r and ||A||_F<=B, with 0<=r<=N. Passivity implies 0<=L<=4N.

Define E_min = inf ||D+A||_F^2 over all admissible passive Q and admissible active corrections A.

## Complete exact value function

### r=0
E_H(N,0,L,B)=L^2/(4N).

### 0<r<N
Set s=L/2.

m_min=max(rs/N, s-2(N-r), 0)
m_max=min(s,2r)

If s<=B sqrt(r), set m_hat=s. Otherwise
m_hat=[rs+(N-r)B sqrt(r)]/N.

Let m_star=clip(m_hat,m_min,m_max). Then

E_H(N,r,L,B)=[m_star/sqrt(r)-B]_+^2 + (L/2-m_star)^2/(N-r).

### r=N
E_H(N,N,L,B)=[L/(2 sqrt(N))-B]_+^2.

## Perfect-cancellation feasibility
For 0<r<N, perfect cancellation is possible in the abstract model iff
L<=4r
and
B>=L/(2 sqrt(r)).

For r=N, the rank obstruction disappears and the condition is
B>=L/(2 sqrt(N)).

For r=0, perfect cancellation is possible only when L=0.

## Broadband master law
Let
W=integral_Omega w(omega)domega,
L_Omega <= integral_Omega w(omega) sum_a X_a(omega)domega,
and
P_Omega=integral_Omega w(omega)||A(omega)||_F^2 domega.

Then, under pointwise passivity and pointwise rank limit r,

E_Omega >= W E_H(N,r,L_Omega/W,sqrt(P_Omega/W)).

This includes r=0 and r=N without ambiguity.

## Interpretation
The law is a best-case electromagnetic resource envelope. Passive theory supplies the unavoidable extinction burden L or L_Omega. The Hellard value function returns the exact minimum residual compatible with that burden, the number of active control dimensions, and the active correction budget.

The result is sharp under the abstract assumptions. Geometry, material dispersion, stability, sensing, noise, preview/latency, and causal controller realizability can only add further constraints.

## Falsifiability
If an experiment using the same channel normalization, passive-extinction definition, rank definition, and Frobenius active budget produces a residual strictly below E_H, then at least one theorem assumption or the theorem itself is wrong.
