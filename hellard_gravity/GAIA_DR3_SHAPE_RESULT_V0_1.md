# Hellard v0.1 first real Gaia DR3 wide-binary shape test

## Data

Public statistically pure Gaia DR3 MS-MS wide-binary sample from Zenodo record 10062232.

Catalog rows read: 2463
Systems surviving the scripted quality cuts: 1494

Observed dimensionless transverse velocity:

    u_perp = v_perp,rel / sqrt(G M_tot / r_proj)

Six geometric separation bins span 0.2-30 kAU. A common model normalization is calibrated only on the inner two, high-acceleration bins. The comparison statistic uses the outer four bins, so the test is primarily sensitive to separation-dependent shape rather than absolute mass/projection normalization.

## Result

Binned observed medians and bootstrap standard errors from CI run 34391960893:

| rmid (kAU) | N | observed u_perp | Newtonian | Hellard v0.1 |
|---:|---:|---:|---:|---:|
| 0.304 | 359 | 0.5460 +/- 0.0176 | 0.5423 | 0.5440 |
| 0.700 | 428 | 0.5098 +/- 0.0240 | 0.5170 | 0.5137 |
| 1.613 | 310 | 0.5259 +/- 0.0202 | 0.5056 | 0.5027 |
| 3.719 | 221 | 0.5581 +/- 0.0260 | 0.5018 | 0.5050 |
| 8.572 | 119 | 0.6656 +/- 0.0433 | 0.4921 | 0.4981 |
| 19.760 | 57 | 0.5662 +/- 0.0501 | 0.4936 | 0.4960 |

Inner calibration scale:

    Newtonian = 1.0226
    Hellard = 1.0203

Outer four-bin shape chi-square:

    chi2_Newton = 23.890
    chi2_Hellard = 22.463
    Delta chi2 (Hellard - Newton) = -1.427

Thus the frozen v0.1 quasi-Kepler comparator fits the outer-bin shape slightly better than the Newtonian comparator in this diagnostic, but the difference is small and is not evidence for discovery.

## Interpretation

PASS as a survival test, NOT a detection claim.

Reasons this is not a final gravity likelihood:

1. the Hellard orbital response is approximated by a local quasi-Kepler velocity rescaling using the frozen reduced spectral-dominance closure;
2. unresolved hierarchical triples and detailed contamination are not fully marginalized;
3. masses, parallaxes and proper-motion covariance are not sampled jointly from their measurement distributions;
4. the catalog eccentricity proxy is used rather than a hierarchical eccentricity population model;
5. Galactic external-field variation with sky position and orbit history is not yet propagated;
6. bin covariances are not included;
7. only transverse motion is used here.

The important result is narrower: the current Hellard v0.1 candidate was confronted with real Gaia DR3 rows without refitting a_H, p or beta to the outer data, and it was not rejected by this first shape diagnostic.
