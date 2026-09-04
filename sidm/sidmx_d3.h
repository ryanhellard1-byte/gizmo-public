#ifndef SIDMX_D3_H
#define SIDMX_D3_H

/* D3 / SIDMx interface.
 *
 * Species convention:
 *   Type 1 = H (heavy)
 *   Type 2 = L (light)
 *   m_H/m_L = 3
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
 */

#define SIDMX_D3_HH 0
#define SIDMX_D3_LL 1
#define SIDMX_D3_HL 2

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

/* Commissioning diagnostics. They are intentionally rank-local during the
 * run so the collision hot path never performs MPI collectives. The rank TSV
 * files are summed by the validator after execution. */
void sidmx_d3_audit_init(void);
void sidmx_d3_audit_flush(void);
void sidmx_d3_note_trial(int ch, double probability);
void sidmx_d3_note_collision(int ch);

/* Accepted-event identity audit. The unordered pair IDs, synchronized integer
 * time, D3 mode, and channel are hashed into commutative XOR+sum digests. This
 * lets commissioning compare event identity across MPI decompositions without
 * storing a huge per-collision log or adding collectives to the hot path. */
void sidmx_d3_event_audit_init(void);
void sidmx_d3_note_collision_event(int ch,
                                   unsigned long long id_i,
                                   unsigned long long id_j,
                                   unsigned long long ti,
                                   int mode);

#endif /* SIDMX_D3_H */
