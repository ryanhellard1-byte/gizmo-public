# Hellard Hybrid Electromagnetic Resource Law
## Formal theorem statement and proof skeleton

Let Q=S0^†S and D=I−Q on an N-dimensional power-normalized incident-channel space, with S0 unitary and Q contractive. For orthonormal channels xa define Xa=2 Re<xa,Dxa> and suppose sum_a Xa>=L. Let an active correction A satisfy rank(A)<=r and ||A||F<=B, where 0<=r<=N.

Passivity gives ||D||2<=2. Also

L/2 <= Re tr(D) <= |tr(D)| <= ||D||*,

so the singular values tau_i of D obey sum_i tau_i>=L/2 and tau_i<=2.

For 0<r<N let m denote the singular-value mass assigned to the r controllable directions. At fixed m, convexity implies the minimum residual occurs when the first r singular values are equal to m/r and the remaining N-r are equal to (L/2-m)/(N-r). The feasible interval is

m_min=max(rL/(2N), L/2-2(N-r), 0),
m_max=min(L/2,2r).

For fixed m,

F(m)=[m/sqrt(r)-B]_+^2+(L/2-m)^2/(N-r).

The unconstrained minimizer is

m_hat=L/2, if L/2<=B sqrt(r),

m_hat=[rL/2+(N-r)B sqrt(r)]/N otherwise.

Let m_star=clip(m_hat,m_min,m_max). Then

E_H(N,r,L,B)=[m_star/sqrt(r)-B]_+^2+(L/2-m_star)^2/(N-r).

Boundary cases:

E_H(N,0,L,B)=L^2/(4N),

E_H(N,N,L,B)=[L/(2sqrt(N))-B]_+^2.

Under the assumptions above,

E_min = inf ||D+A||F^2 = E_H(N,r,L,B).

The result is sharp: equality is attained by a diagonal passive deviation operator with the equalized singular-value spectrum implied by m_star and an aligned optimal active correction.

Perfect-cancellation feasibility:

For 0<r<N, E_H=0 iff L<=4r and B>=L/(2sqrt(r)).
For r=N, E_H=0 iff B>=L/(2sqrt(N)).
For r=0, E_H=0 iff L=0.

Broadband corollary:

Let W=integral_Omega w(omega)domega, L_Omega<=integral w sum_a Xa domega, and P_Omega=integral w ||A||F^2 domega. Under pointwise passivity and pointwise rank(A)<=r,

E_Omega>=W E_H(N,r,L_Omega/W,sqrt(P_Omega/W)).

The broadband bound is sharp in the abstract pointwise-passive model.

Independent electromagnetic validation performed so far includes 2-D PEC-cylinder partial waves, broadband PEC-cylinder scattering, lossy dielectric-cylinder scattering, passive multilayer cylindrical cloak plus active correction, and 3-D Lorenz-Mie sphere scattering with both electric and magnetic multipoles and all 2l+1 azimuthal degeneracies. No tested Maxwell case violated the theorem.

Scope: this is an exact finite-dimensional resource theorem under the stated assumptions. It does not by itself prove the existence of a practical invisibility cloak or historical novelty. Geometry, passive-cloak lower bounds, causality, dispersion, stability, sensing, latency, noise, and hardware constraints may add further penalties.

Falsifiability: if a consistently normalized experiment or full-wave calculation obeying all assumptions produces ||D+A||F^2<E_H(N,r,L,B), then either the theorem or an assumed mapping/normalization is wrong.
