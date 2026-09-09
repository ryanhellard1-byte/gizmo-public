# HELIOS-R32 — MHD E-fold Stability Closure

## Purpose

Extend the Hellard Prompt-Selective Closure Law with an explicit instability-growth budget. Species-selective escape can tolerate finite magnetic perturbation growth; the requirement is not zero instability, but that the magnetic disorder remain below the orbit-containment ceiling during the relevant hot phase.

## Magnetic-disorder ceiling

For conservative He-3 retention,

\[
\frac{2\rho_{He}}{1-\delta_B}+\sigma_{\rm fusion}<R,
\]

so

\[
\boxed{\delta_{B,\max}=1-\frac{2\rho_{He}}{R-\sigma_{\rm fusion}}}.
\]

Define hotspot compactness

\[
\chi_H=\frac{\sigma_{\rm fusion}}{R}.
\]

At the R31 reference point \(R=1.9\,\mathrm{mm}\), \(B_0\approx140\,\mathrm T\), and the previously inferred He-3 gyroradius, representative limits are:

| \(\chi_H\) | \(\delta_{B,\max}\) |
|---:|---:|
| 0.05 | 10.6% |
| 0.08 | 7.7% |
| 0.10 | 5.65% |
| 0.12 | 3.50% |

## E-fold growth law

Let the net magnetic perturbation during the relevant interval be

\[
\delta_B(t)=\delta_{B0}\exp(N_{\rm net}),
\]

where

\[
N_{\rm net}=\int \max[\gamma_{\rm drive}(t)-\gamma_{\rm damp}(t),0]dt
\]

is the accumulated positive instability growth measured in e-folds.

Selective-escape stability requires

\[
\boxed{N_{\rm net}\le \ln\!\left(\frac{\delta_{B,\max}}{\delta_{B0}}\right)}.
\]

Define the Hellard MHD stability number

\[
\boxed{\mathcal A_{\rm MHD}=\frac{\ln(\delta_{B,\max}/\delta_{B0})}{\max(N_{\rm net},\epsilon)}}.
\]

Closure requires

\[
\boxed{\mathcal A_{\rm MHD}\ge1}.
\]

## Reference margins at \(\chi_H=0.08\)

With \(\delta_{B,\max}=7.7\%\):

| initial \(\delta_{B0}\) | allowed net e-folds |
|---:|---:|
| 0.05% | 5.04 |
| 0.10% | 4.34 |
| 0.25% | 3.43 |
| 0.50% | 2.73 |
| 1.00% | 2.04 |

Thus the architecture does not require perfectly quiescent plasma. It tolerates several net e-folds if the initial perturbation level is kept small.

Examples of minimum stabilization needed at \(\chi_H=0.08\):

- If \(\delta_{B0}=0.1\%\) and gross growth is 5 e-folds, suppress at least 0.66 e-fold.
- If \(\delta_{B0}=0.5\%\) and gross growth is 4 e-folds, suppress at least 1.27 e-folds.
- If \(\delta_{B0}=1.0\%\) and gross growth is 5 e-folds, suppress at least 2.96 e-folds.

## Reduced robustness sweep

A 300,000-case deterministic reduced sweep varied:

- \(\chi_H=0.05\) to 0.12,
- initial magnetic perturbation about 0.05% to 1%,
- gross instability growth 0 to 5 e-folds,
- stabilizing contribution 0 to 3 e-folds.

Within that assumed hypercube, 88.9% remained below the orbit-disorder ceiling. This is a design-space fraction, not a probability of hardware success.

Surviving medians were approximately:

- \(\chi_H\approx0.085\),
- \(\delta_{B0}\approx0.195\%\),
- gross growth \(\approx2.20\) e-folds,
- stabilization \(\approx1.62\) e-folds,
- net growth \(\approx0.70\) e-fold,
- final \(\delta_B/B\approx0.58\%\),
- allowable \(\delta_B/B\approx7.2\%\).

## Full Hellard closure stack update

The current reduced engineering criterion becomes

\[
\boxed{
\mathscr H_{\rm Hellard}=\min\left[
\frac{\kappa}{\kappa_{\min}},
\frac{\chi_{\rm crit}}{\chi_H},
\frac{\Pi_{\rm crit}}{\Pi_T},
\mathcal A_\Phi,
\mathcal A_B,
\mathcal A_{\rm MHD},
\mathcal S_H,
\mathcal H_{PM}
\right]
}
\]

and reduced-order closure requires

\[
\boxed{\mathscr H_{\rm Hellard}\ge1}.
\]

## Claim boundary

This is a derived engineering closure relation, not a demonstrated universal physical law. The MHD term is intentionally solver-agnostic: a future hybrid-MHD/PIC calculation or experiment should supply \(\gamma_{\rm drive}\), \(\gamma_{\rm damp}\), and the initial perturbation spectrum. The criterion then predicts whether the resulting magnetic disorder is compatible with selective product escape.

Current experimental and simulation literature shows both that FRCs can exhibit finite-Larmor-radius/fast-ion stabilization and that rotational/tearing-like perturbations remain real threats. The law therefore does not assume stability; it specifies the allowable instability budget.
