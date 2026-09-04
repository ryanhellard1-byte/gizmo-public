#ifndef D3_SIDMX_KERNEL_INLINE_H
#define D3_SIDMX_KERNEL_INLINE_H

#include <math.h>

/*
 * First-pass D3/SIDMx scaffold for GIZMO-public.
 *
 * Routing convention:
 *   Particle Type 2 -> heavy species H
 *   Particle Type 3 -> light species L
 *
 * This is intentionally header-only for first integration so the GIZMO
 * Makefile does not need surgery. The stock DM_SIDM machinery still owns
 * neighbor search, timestep limiting, wakeup, and collision bookkeeping.
 */

#define D3_SPECIES_NONE 0
#define D3_SPECIES_H    1
#define D3_SPECIES_L    2

#define D3_CHANNEL_NONE 0
#define D3_CHANNEL_HH   1
#define D3_CHANNEL_LL   2
#define D3_CHANNEL_HL   3

#define D3_TYPE_H 2
#define D3_TYPE_L 3

#define D3_SIGMA_HH_OVER_MH 6.89
#define D3_SIGMA_LL_OVER_ML 2.2966666667
#define D3_SIGMA_HL_OVER_MH 1.125
#define D3_SIGMA_HL_OVER_ML 3.375

#define D3_W_HH_KMS 275.0
#define D3_W_LL_KMS 825.0
#define D3_W_HL_KMS 2200.0

static inline int d3_species_from_type(int type)
{
    if(type == D3_TYPE_H) {return D3_SPECIES_H;}
    if(type == D3_TYPE_L) {return D3_SPECIES_L;}
    return D3_SPECIES_NONE;
}

static inline int d3_channel_from_species(int si, int sj)
{
    if(si == D3_SPECIES_H && sj == D3_SPECIES_H) {return D3_CHANNEL_HH;}
    if(si == D3_SPECIES_L && sj == D3_SPECIES_L) {return D3_CHANNEL_LL;}
    if((si == D3_SPECIES_H && sj == D3_SPECIES_L) || (si == D3_SPECIES_L && sj == D3_SPECIES_H)) {return D3_CHANNEL_HL;}
    return D3_CHANNEL_NONE;
}

static inline double d3_velocity_suppression(double vrel, double w)
{
    if(w <= 0.0) {return 1.0;}
    double x = vrel / w;
    double x2 = x*x;
    return 1.0 / (1.0 + x2*x2);
}

static inline double d3_sigma_over_mass_for_pair(int si, int sj, double vrel)
{
    int ch = d3_channel_from_species(si, sj);
    if(ch == D3_CHANNEL_HH) {return D3_SIGMA_HH_OVER_MH * d3_velocity_suppression(vrel, D3_W_HH_KMS);}
    if(ch == D3_CHANNEL_LL) {return D3_SIGMA_LL_OVER_ML * d3_velocity_suppression(vrel, D3_W_LL_KMS);}
    if(ch == D3_CHANNEL_HL)
    {
        /* Symmetric event probability for the pair. The H/L values encode the same
         * channel with per-species normalization; average for the pair-level event.
         */
        return 0.5 * (D3_SIGMA_HL_OVER_MH + D3_SIGMA_HL_OVER_ML) * d3_velocity_suppression(vrel, D3_W_HL_KMS);
    }
    return 0.0;
}

static inline double d3_prob_of_interaction(double mi, double mj, double r, double h_si, double dV[3], double dt, int si, int sj)
{
    int ch = d3_channel_from_species(si, sj);
    if(ch == D3_CHANNEL_NONE) {return 0.0;}
    if(h_si <= 0.0 || dt <= 0.0) {return 0.0;}

    double dVmag = sqrt(dV[0]*dV[0] + dV[1]*dV[1] + dV[2]*dV[2]) / All.cf_atime;
    double rho_eff = (0.5 * (mi + mj)) / (h_si*h_si*h_si) * All.cf_a3inv;
    double sigma_over_mass = d3_sigma_over_mass_for_pair(si, sj, dVmag);
    double cx_eff = sigma_over_mass * g_geo(r/h_si);
    double units = UNIT_SURFDEN_IN_CGS;

    return rho_eff * cx_eff * dVmag * dt * units;
}

static inline void d3_calculate_interact_kick_from_unit(double dV[3], double mi, double mj, double nhat[3], double kick_i[3], double kick_j[3])
{
    int k;
    double mtot = mi + mj;
    double vcm[3];
    double vi_old[3];
    double vj_old[3];
    double vrel_mag = sqrt(dV[0]*dV[0] + dV[1]*dV[1] + dV[2]*dV[2]);

    if(mtot <= 0.0)
    {
        for(k=0;k<3;k++) {kick_i[k] = 0.0; kick_j[k] = 0.0;}
        return;
    }

    /* Work in a frame where v_i - v_j = dV and total momentum is zero. */
    for(k=0;k<3;k++)
    {
        vi_old[k] = (mj/mtot) * dV[k];
        vj_old[k] = -(mi/mtot) * dV[k];
        vcm[k] = 0.0;
    }

    for(k=0;k<3;k++)
    {
        double vi_new = vcm[k] + (mj/mtot) * vrel_mag * nhat[k];
        double vj_new = vcm[k] - (mi/mtot) * vrel_mag * nhat[k];
        kick_i[k] = vi_new - vi_old[k];
        kick_j[k] = vj_new - vj_old[k];
    }
}

#endif /* D3_SIDMX_KERNEL_INLINE_H */
