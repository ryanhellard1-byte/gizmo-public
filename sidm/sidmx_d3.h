#ifndef SIDMX_D3_H
#define SIDMX_D3_H

/*
 * D3 / SIDMx two-component extension for the public GIZMO SIDM engine.
 *
 * Species convention (frozen by the Phase-165 manifest):
 *   particle Type 1 = H (heavy)
 *   particle Type 2 = L (light)
 *   m_H / m_L = 3
 *
 * Runtime branch selection deliberately uses NEGATIVE values of the existing
 * DM_InteractionCrossSection parameter. Positive/zero values retain the
 * upstream GIZMO SIDM implementation unchanged.
 *
 *   -1  full SIDM2v: HH + LL + HL
 *   -2  SIDMx:       HL only
 *   -3  HL_off:      HH + LL
 *   -4  HH_only
 *   -5  LL_only
 *   -6  HL_HH
 *   -7  HL_LL
 *   -8  constant SIDM2c benchmark (HH=2.25, LL=0.75, HL=1.125 cm^2/g)
 *   -9  zero-scattering/CDM null while keeping the same DM_SIDM executable
 *
 * Frozen D3 differential laws:
 *   HH Moller:     sigma0/m_H = 6.89 cm^2/g,       w = 275 km/s
 *   LL Moller:     sigma0/m_L = 6.89/3 cm^2/g,     w = 825 km/s
 *   HL Rutherford: sigma0/m_H = 1.125 cm^2/g,      w = 2200 km/s
 *
 * The event probability keeps GIZMO's validated overlap factor g_geo(r/h)
 * and unit conversion, but replaces the single global cross section by the
 * exact channel-dependent total cross section and the correct macro-particle
 * mass basis. Accepted events sample the full differential angular law and
 * apply exact unequal-mass elastic COM kinematics.
 */

#include <math.h>
#include <gsl/gsl_rng.h>
#include "../allvars.h"
#include "../proto.h"

enum {
    SIDMX_D3_HH = 0,
    SIDMX_D3_LL = 1,
    SIDMX_D3_HL = 2
};

static inline int sidmx_d3_runtime_mode(void)
{
    const double x = All.DM_InteractionCrossSection;
    if(x >= 0.0) return 0; /* upstream/legacy GIZMO SIDM */
    {
        const int mode = (int) floor(-x + 0.5);
        if(mode < 1 || mode > 9 || fabs(x + (double) mode) > 1.0e-10)
        {
            if(ThisTask == 0)
                fprintf(stderr, "SIDMx-D3: invalid negative DM_InteractionCrossSection=%g; expected integer sentinel -1..-9\n", x);
            endrun(171201);
        }
        return mode;
    }
}

static inline int sidmx_d3_channel(int type_i, int type_j)
{
    if(type_i == 1 && type_j == 1) return SIDMX_D3_HH;
    if(type_i == 2 && type_j == 2) return SIDMX_D3_LL;
    if((type_i == 1 && type_j == 2) || (type_i == 2 && type_j == 1)) return SIDMX_D3_HL;
    return -1;
}

static inline int sidmx_d3_channel_enabled(int mode, int ch)
{
    switch(mode)
    {
        case 1: return 1;                         /* full SIDM2v */
        case 2: return ch == SIDMX_D3_HL;        /* SIDMx */
        case 3: return ch != SIDMX_D3_HL;        /* HL_off */
        case 4: return ch == SIDMX_D3_HH;
        case 5: return ch == SIDMX_D3_LL;
        case 6: return ch == SIDMX_D3_HL || ch == SIDMX_D3_HH;
        case 7: return ch == SIDMX_D3_HL || ch == SIDMX_D3_LL;
        case 8: return 1;                         /* constant SIDM2c */
        case 9: return 0;                         /* zero-scattering null */
        default: return 0;
    }
}

static inline double sidmx_d3_moller_total(double v_km_s, double sigma0, double w_km_s)
{
    /* Exact integral over mu of the frozen Moller d(sigma/m)/dmu law.
     * z=(v/w)^2.  The low-z series avoids catastrophic cancellation and
     * correctly tends to sigma0/2, the convention frozen by Phase 139. */
    const double x = v_km_s / w_km_s;
    const double z = x*x;
    if(z < 1.0e-5)
    {
        const double z2 = z*z, z3 = z2*z, z4 = z3*z;
        return sigma0 * (0.5 - 0.5*z + (7.0/12.0)*z2 - (2.0/3.0)*z3 + (11.0/15.0)*z4);
    }
    {
        const double y = z / (z + 2.0);
        return sigma0 * (1.0/(1.0+z) - 2.0*atanh(y)/(z*(z+2.0)));
    }
}

static inline double sidmx_d3_rutherford_total(double v_km_s, double sigma0, double w_km_s)
{
    const double x = v_km_s / w_km_s;
    return sigma0 / (1.0 + x*x);
}

static inline double sidmx_d3_sigma_total_per_mass(int mode, int ch, double v_km_s)
{
    if(mode == 8)
    {
        if(ch == SIDMX_D3_HH) return 2.25;
        if(ch == SIDMX_D3_LL) return 0.75;
        return 1.125;
    }

    if(ch == SIDMX_D3_HH) return sidmx_d3_moller_total(v_km_s, 6.89, 275.0);
    if(ch == SIDMX_D3_LL) return sidmx_d3_moller_total(v_km_s, 6.89/3.0, 825.0);
    return sidmx_d3_rutherford_total(v_km_s, 1.125, 2200.0);
}

static inline double sidmx_d3_moller_antiderivative(double mu, double z)
{
    /* Integral of the normalized-shape factor.  y=sqrt(t)=z/(z+2). */
    const double y = z/(z+2.0);
    const double t = y*y;
    if(y < 1.0e-7) return mu;
    return 2.0*mu/(1.0-t*mu*mu) - atanh(y*mu)/y;
}

static inline double sidmx_d3_moller_cdf(double mu, double z)
{
    if(z < 1.0e-5) return 0.5*(mu+1.0);
    {
        const double am = sidmx_d3_moller_antiderivative(-1.0, z);
        const double ap = sidmx_d3_moller_antiderivative( 1.0, z);
        const double ax = sidmx_d3_moller_antiderivative(mu, z);
        return (ax-am)/(ap-am);
    }
}

static inline double sidmx_d3_sample_mu(int mode, int ch, double v_km_s)
{
    const double u = gsl_rng_uniform(random_generator);
    if(mode == 8) return 2.0*u - 1.0; /* constant benchmark: isotropic */

    if(ch == SIDMX_D3_HL)
    {
        /* Exact inverse CDF of the frozen Rutherford differential law. */
        const double x = v_km_s/2200.0;
        const double z = x*x;
        double mu = 1.0 - 2.0*(1.0-u)/(1.0 + u*z);
        if(mu > 1.0) mu = 1.0;
        if(mu < -1.0) mu = -1.0;
        return mu;
    }
    else
    {
        /* Moller inverse CDF.  Bisection is only paid on accepted rare events,
         * not on every candidate neighbor pair. */
        const double w = (ch == SIDMX_D3_HH) ? 275.0 : 825.0;
        const double x = v_km_s/w;
        const double z = x*x;
        double lo=-1.0, hi=1.0;
        int n;
        if(z < 1.0e-5) return 2.0*u - 1.0;
        for(n=0; n<48; n++)
        {
            const double mid = 0.5*(lo+hi);
            if(sidmx_d3_moller_cdf(mid,z) < u) lo=mid; else hi=mid;
        }
        return 0.5*(lo+hi);
    }
}

static inline double sidmx_d3_basis_macro_mass(int ch, int type_i, int type_j,
                                                double mass_i, double mass_j)
{
    if(ch == SIDMX_D3_HH || ch == SIDMX_D3_LL)
        return 0.5*(mass_i+mass_j);

    /* HL is stored on the physical m_H basis.  The frozen numerical mass ratio
     * is also 3:1, so multiplying by the H macro-particle mass gives the same
     * conditional pair probability from either side. */
    {
        const double mH = (type_i == 1) ? mass_i : mass_j;
        const double mL = (type_i == 2) ? mass_i : mass_j;
        const double ratio = mH/mL;
        if(fabs(ratio-3.0) > 3.0e-6)
        {
            if(ThisTask == 0)
                fprintf(stderr, "SIDMx-D3: fatal H/L macro-mass ratio %.17g (required 3)\n", ratio);
            endrun(171202);
        }
        return mH;
    }
}

static inline double sidmx_d3_probability(int mode, int ch,
                                           int type_i, int type_j,
                                           double mass_i, double mass_j,
                                           double r, double h_si,
                                           const double dV[3], double dt)
{
    double v_phys, rho_eff, sigma_per_mass, basis_mass;
    if(!sidmx_d3_channel_enabled(mode,ch)) return 0.0;
    if(h_si <= 0.0 || dt <= 0.0) return 0.0;

    v_phys = sqrt(dV[0]*dV[0] + dV[1]*dV[1] + dV[2]*dV[2]) / All.cf_atime;
    sigma_per_mass = sidmx_d3_sigma_total_per_mass(mode,ch,v_phys);
    basis_mass = sidmx_d3_basis_macro_mass(ch,type_i,type_j,mass_i,mass_j);
    rho_eff = basis_mass/(h_si*h_si*h_si) * All.cf_a3inv;

    return rho_eff * sigma_per_mass * g_geo(r/h_si) * v_phys * dt * UNIT_SURFDEN_IN_CGS;
}

static inline void sidmx_d3_scatter_deltas(int mode, int ch,
                                            const double dV[3],
                                            double mass_i, double mass_j,
                                            double delta_i[3], double delta_j[3])
{
    double speed = sqrt(dV[0]*dV[0] + dV[1]*dV[1] + dV[2]*dV[2]);
    double n[3], a[3], e1[3], e2[3], nhat[3], drel[3];
    double e1norm, mu, sint, phi, mt;
    int k;

    for(k=0;k<3;k++) {delta_i[k]=0.0; delta_j[k]=0.0;}
    if(speed <= 0.0) return;

    for(k=0;k<3;k++) n[k]=dV[k]/speed;
    if(fabs(n[0]) < 0.8) {a[0]=1.0; a[1]=0.0; a[2]=0.0;}
    else                 {a[0]=0.0; a[1]=1.0; a[2]=0.0;}

    e1[0]=n[1]*a[2]-n[2]*a[1];
    e1[1]=n[2]*a[0]-n[0]*a[2];
    e1[2]=n[0]*a[1]-n[1]*a[0];
    e1norm=sqrt(e1[0]*e1[0]+e1[1]*e1[1]+e1[2]*e1[2]);
    for(k=0;k<3;k++) e1[k]/=e1norm;
    e2[0]=n[1]*e1[2]-n[2]*e1[1];
    e2[1]=n[2]*e1[0]-n[0]*e1[2];
    e2[2]=n[0]*e1[1]-n[1]*e1[0];

    mu = sidmx_d3_sample_mu(mode,ch,speed/All.cf_atime);
    if(mu > 1.0) mu=1.0; if(mu < -1.0) mu=-1.0;
    sint=sqrt(DMAX(0.0,1.0-mu*mu));
    phi=2.0*M_PI*gsl_rng_uniform(random_generator);
    for(k=0;k<3;k++)
        nhat[k]=mu*n[k] + sint*(cos(phi)*e1[k] + sin(phi)*e2[k]);

    mt=mass_i+mass_j;
    for(k=0;k<3;k++)
    {
        drel[k]=speed*nhat[k]-dV[k];
        delta_i[k]=(mass_j/mt)*drel[k];
        delta_j[k]=-(mass_i/mt)*drel[k];
    }
}

#endif /* SIDMX_D3_H */
