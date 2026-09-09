# HELIOS-R30 Prompt Selectivity Correction

## Summary
R29 over-credited slow bounce-autoresonant cleanup as if it could reduce the prompt neutron fraction during the same hot dense fusion pulse. Published mirror autoresonance examples operate on millisecond timescales, whereas the secondary D-T burn window in the current HELIOS reduced model is tens of nanoseconds. Therefore slow autoresonant cleanup may be useful for between-pulse inventory management, but it must not appear in the prompt neutron-closure term.

## Prompt timing gate
Define

\[
\Pi_T = \frac{\tau_{\rm escape,T}}{\tau_{DT}}.
\]

Prompt tritium suppression requires

\[
\Pi_T \ll 1.
\]

For the current reduced HELIOS-R28 orbit point, \(\tau_{\rm escape,T}\sim0.24\,\rm ns\) and \(\tau_{DT}\sim40-50\,\rm ns\), giving \(\Pi_T\sim5\times10^{-3}\). Passive/mirror prompt escape therefore remains fast enough at reduced-order level.

## Cyclotron spectral-cleanup alternative
For a fundamental triton cyclotron drive, resonance of any species j occurs where

\[
\frac{q_j B_j}{m_j}=\frac{q_T B_T}{m_T},
\]

so

\[
B_j=\frac{q_T/m_T}{q_j/m_j}B_T.
\]

For He-3, \(B_{He}\approx B_T/2\). For deuterium, \(B_D\approx(2/3)B_T\). Thus if the mirror minimum field is \(B_{\min}\), a geometry-only fundamental-resonance exclusion of both D and He-3 is guaranteed when

\[
\boxed{1\le\beta_T\equiv B_T/B_{\min}<3/2.}
\]

The deuterium condition is the controlling one; it automatically puts the He-3 fundamental resonance below \(B_{\min}\).

Avoid operation near the triton second harmonic because \(2\Omega_T\approx\Omega_{He3}\) at the same field.

## Corrected prompt selective-escape law
The prompt low-neutron closure must use only loss fractions achieved on a timescale shorter than secondary D-T burn:

\[
f_{n,\rm eff}=\frac{2.45+14.1(1-L_T^{\rm prompt})}{7.30+17.6(1-L_T^{\rm prompt})+18.3(1-L_{He}^{\rm prompt})}.
\]

Slow post-pulse cleanup must not be inserted into \(L_T^{\rm prompt}\).

A corrected engineering closure stack is therefore:

\[
\kappa = r_{L,T}/r_{L,He}>1,
\]

\[
\chi_H=\sigma_{\rm fusion}/R\le\chi_{\rm crit},
\]

\[
\Pi_T=\tau_{\rm escape,T}/\tau_{DT}\ll1,
\]

\[
\mathcal S_H=f_{n,\max}/f_{n,\rm eff}\ge1.
\]

If an active *prompt* cyclotron-control term is later demonstrated, it must additionally satisfy both a timing condition \(\tau_{\rm control}\ll\tau_{DT}\) and the resonance-layer isolation condition above. Until then it is not credited in the prompt neutron budget.

## Claim boundary
This is a reduced-order engineering correction, not a fundamental law and not a self-consistent kinetic proof. A hybrid-PIC/PIC calculation with collisions, self-consistent fields, and realistic time-dependent topology remains required.
