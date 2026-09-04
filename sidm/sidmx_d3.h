#ifndef SIDMX_D3_H
#define SIDMX_D3_H

/* D3 / SIDMx interface.
 *
 * Species convention:
 *   Type 1 = H (heavy)
 *   Type 2 = L (light)
 *   m_H/m_L = 3 for frozen D3 sentinel modes
 *
 * Negative DM_InteractionCrossSection values select the frozen D3 branches:
 *   -1 full SIDM2v (HH+LL+HL)
 *   -2 SIDMx (HL only)
 *   -3 HL_off (HH+LL)
 *   -4 HH_only
 *   -5 LL_only
 *   -6 HL_HH
 *   -7 HL_LL
 *   -8 constant SIDM2c benchmark
 *   -9 zero-scattering null
 *
 * Positive/zero values retain upstream GIZMO SIDM behavior.
 *
 * SIDMX_STANDARD_SIDM_AUDIT_MODE=10 is NOT a runtime interaction mode or
 * DM_InteractionCrossSection sentinel. It is only a tag on live audit lines
 * emitted while the untouched upstream positive-cross-section SIDM path runs.
 */

#define SIDMX_D3_HH 0
#define SIDMX_D3_LL 1
#define SIDMX_D3_HL 2
#define SIDMX_STANDARD_SIDM_AUDIT_MODE 10

int sidmx_d3_runtime_mode(void);
int sidmx_d3_channel(int type_i, int type_j);
int sidmx_d3_channel_enabled(int mode, int ch);
double sidmx_d3_moller_total(double v_km_s, double sigma0, double w_km_s);
double sidmx_d3_rutherford_total(double v_km_s, double sigma0, double w_km_s);
double sidmx_d3_sigma_total_per_mass(int mode, int ch, double v_km_s);
double sidmx_d3_moller_cdf(double mu, double z);
double sidmx_d3_sample_mu_from_u(int mode, int ch, double v_km_s, double u);
double sidmx_d3_pair_uniform(unsigned long long id_i, unsigned long long id_j,
                             unsigned long long ti, int mode, int stream);
double sidmx_d3_basis_macro_mass(int ch, int type_i, int type_j,
                                 double mass_i, double mass_j);
double sidmx_d3_probability(int mode, int ch,
                            int type_i, int type_j,
                            double mass_i, double mass_j,
                            double r, double h_si,
                            const double dV[3], double dt);
void sidmx_d3_scatter_deltas(int mode, int ch,
                             const double dV[3],
                             double mass_i, double mass_j,
                             double u_mu, double u_phi,
                             double delta_i[3], double delta_j[3]);

/* Live-engine commissioning/production audit. These diagnostics do not alter
 * any probability, random draw, or kick; they only accumulate the exact
 * probabilities seen by the neighbor walk and conservation residuals of
 * accepted events. */
void sidmx_d3_audit_reset(void);
void sidmx_d3_audit_probability(int mode, int ch, double prob);
void sidmx_d3_audit_collision(int mode, int ch, const double dV[3],
                              double mass_i, double mass_j,
                              const double delta_i[3], const double delta_j[3]);
void sidmx_d3_audit_flush(void);

#endif /* SIDMX_D3_H */
