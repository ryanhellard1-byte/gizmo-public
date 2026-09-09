# Hellard Physical Normalization and Hardware-Coupling Bridge

Date: 2026-09-09

## 1. Why the reference operator must be physically fixed

Let `S0` denote a **fixed, physically specified, lossless background propagation operator** and let `S` denote the passive system with the object/device present. Assume power-normalized channels and

\[
S_0^\dagger S_0=I,
\qquad
S^\dagger S\preceq I.
\]

Define

\[
Q=S_0^\dagger S,
\qquad
D=I-Q.
\]

Because `S0` is unitary,

\[
S-S_0=S_0(Q-I)=-S_0D.
\]

For an incident vector `x`, the background-relative output deviation power is therefore

\[
P_{\rm dev}(x)
=\|(S-S_0)x\|^2
=\|Dx\|^2.
\]

The passive absorbed/unreturned power is

\[
P_{\rm abs}(x)
=\|x\|^2-\|Sx\|^2
=\|x\|^2-\|Qx\|^2
\ge0.
\]

Using `Q=I-D`,

\[
\|Qx\|^2
=\|x\|^2-2\operatorname{Re}\langle x,Dx\rangle+\|Dx\|^2.
\]

Hence

\[
\boxed{
P_{\rm dev}(x)+P_{\rm abs}(x)
=2\operatorname{Re}\langle x,Dx\rangle
\equiv X(x).
}
\]

Thus the Hellard burden functional is exactly a power-balance quantity: background-relative scattered/deviation power plus passive absorption.

For a free-space/no-object reference, this is the natural operator form of extinction relative to that background. For a more general fixed unitary background, it is a reference-relative extinction/mismatch burden.

### Critical qualification

`S0` must be selected from the physical problem **before** examining or optimizing `S`. An arbitrary a-posteriori choice such as `S0=S` would make `D=0` and trivialize the quantity. Any experimental or numerical claim must therefore specify the background reference and channel normalization explicitly.

---

## 2. Complete-channel requirement

The identity above assumes that `S` and `S0` act on the same complete set of propagating power channels used in the power balance. If propagating output channels are omitted, apparent missing power can be confused with absorption and the deviation norm can underestimate total visibility.

A practical computation should either:

1. include every relevant propagating channel to a verified truncation tolerance, or
2. use a rigorous tail estimate such as the separate tail-robust Hellard channel corollary.

---

## 3. From abstract correction norm to a controller norm

The theorem constrains an **effective channel-to-channel correction operator** `A` by

\[
\operatorname{rank}(A)\le r,
\qquad
\|A\|_F\le B.
\]

To connect this to hardware, suppose the active system factors as

\[
\boxed{A=GKH,}
\]

where

- `H` maps incident power-normalized channels into measured/controller input coordinates,
- `K` is the controller/actuator command map,
- `G` maps actuator commands into outgoing power-normalized electromagnetic channels.

Then

\[
\operatorname{rank}(A)
\le
\min\{\operatorname{rank}G,\operatorname{rank}K,\operatorname{rank}H\}.
\]

Also, by submultiplicativity,

\[
\boxed{
\|A\|_F
\le
\|G\|_2\,\|H\|_2\,\|K\|_F.
}
\]

Define the channel-coupling gain

\[
\kappa=\|G\|_2\|H\|_2.
\]

If the controller has the quadratic command budget

\[
\|K\|_F^2\le P_K,
\]

then every realizable effective correction satisfies

\[
\boxed{B_{\rm eff}\le\kappa\sqrt{P_K}.}
\]

---

## 4. Necessary controller-resource condition

The Hellard class-envelope strength threshold for zero residual is

\[
B\ge\frac{L}{2\sqrt r}.
\]

Therefore a hardware factorization `A=GKH` cannot reach the zero-residual class envelope unless

\[
\kappa\sqrt{P_K}
\ge
\frac{L}{2\sqrt r}.
\]

Equivalently,

\[
\boxed{
P_K
\ge
\frac{L^2}{4r\kappa^2}.
}
\]

This is accompanied by the independent effective-rank requirement

\[
\boxed{
r\ge L/4.}
\]

These are necessary best-case conditions. They are not sufficient for a fixed physical layout because singular-vector reachability, directivity, mutual coupling, causality, stability, sensing noise, latency and frequency response can all make the actual system harder to control.

---

## 5. Spherical specialization

For a homogeneous Lorenz-Mie sphere with size parameter `x=ka`,

\[
L=2x^2Q_{\rm ext}.
\]

The hardware-controller necessary conditions become

\[
\boxed{
r\ge\frac{x^2Q_{\rm ext}}{2},}
\]

and

\[
\boxed{
P_K
\ge
\frac{x^4Q_{\rm ext}^2}{r\kappa^2}.
}
\]

At the continuous minimum-rank threshold

\[
r=\frac{x^2Q_{\rm ext}}{2},
\]

this reduces to

\[
\boxed{
P_K\ge\frac{2x^2Q_{\rm ext}}{\kappa^2}.
}
\]

For electrically large spheres, `Q_ext -> 2`, giving the asymptotic best-case scaling

\[
\boxed{r\gtrsim(ka)^2,}
\]

\[
\boxed{P_K\gtrsim\frac{4(ka)^2}{\kappa^2}.}
\]

The quantity `P_K` is a squared norm of the controller map in the chosen normalization. It should **not** be labeled watts, joules, amplifier power or electrical energy until `G`, `H`, and `K` are normalized to a specific hardware implementation and the conversion is derived.

---

## 6. Interpretation

The factorization exposes three independent barriers to perfect active correction:

1. **passive extinction burden** `L` imposed by the object/background problem;
2. **control dimensionality** `r` imposed by the number of independently reachable channel directions;
3. **coupling-weighted controller strength** `kappa sqrt(P_K)`.

Increasing controller command magnitude cannot repair missing channel rank. Increasing actuator count cannot repair arbitrarily poor channel coupling. Both resources must clear their respective Hellard thresholds.

## Status

The power identity and norm inequalities in this note are elementary exact consequences of the stated operator normalization. The use of these identities as a physical bridge for the Hellard resource theorem is part of the current research program and requires external novelty review.
