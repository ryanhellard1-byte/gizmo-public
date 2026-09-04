#ifndef D3_SIDMX_KERNEL_INLINE_H
#define D3_SIDMX_KERNEL_INLINE_H

#include <math.h>

/* Frozen D3/SIDMx microscopic kernel helpers.
 * Particle Type 2 -> heavy H; Particle Type 3 -> light L.
 * Velocity arguments are expected in km/s, matching the frozen w parameters.
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
    if(type == D3_TYPE_H) return D3_SPECIES_H;
    if(type == D3_TYPE_L) return D3_SPECIES_L;
    return D3_SPECIES_NONE;
}

static inline int d3_channel_from_species(int si, int sj)
{
    if(si == D3_SPECIES_H && sj == D3_SPECIES_H) return D3_CHANNEL_HH;
    if(si == D3_SPECIES_L && sj == D3_SPECIES_L) return D3_CHANNEL_LL;
    if((si == D3_SPECIES_H && sj == D3_SPECIES_L) || (si == D3_SPECIES_L && sj == D3_SPECIES_H)) return D3_CHANNEL_HL;
    return D3_CHANNEL_NONE;
}

/* Rutherford differential law, d(sigma/m)/dmu. */
static inline double d3_rutherford_dsigma_dmu(double sigma0_over_m, double v, double w, double mu)
{
    double den = w*w + 0.5*v*v*(1.0-mu);
    return 0.5*sigma0_over_m*w*w*w*w/(den*den);
}

/* Exact Rutherford total cross section obtained by integrating mu in [-1,1]. */
static inline double d3_rutherford_sigma_total(double sigma0_over_m, double v, double w)
{
    double x = v/w;
    return sigma0_over_m/(1.0 + x*x);
}

/* Exact inverse CDF for Rutherford scattering. */
static inline double d3_rutherford_mu_from_u(double v, double w, double u)
{
    double x = v/w;
    double x2 = x*x;
    if(u <= 0.0) return -1.0;
    if(u >= 1.0) return 1.0;
    return 1.0 - 2.0*(1.0-u)/(1.0 + u*x2);
}

/* Moller differential law, d(sigma/m)/dmu. */
static inline double d3_moller_dsigma_dmu(double sigma0_over_m, double v, double w, double mu)
{
    double v2=v*v, w2=w*w, v4=v2*v2, w4=w2*w2;
    double num=(3.0*mu*mu+1.0)*v4 + 4.0*v2*w2 + 4.0*w4;
    double den=(1.0-mu*mu)*v4 + 4.0*v2*w2 + 4.0*w4;
    return sigma0_over_m*w4*num/(den*den);
}

/* Safe rejection envelope. The differential law is maximal at |mu|=1. */
static inline double d3_moller_dsigma_max(double sigma0_over_m, double v, double w)
{
    return d3_moller_dsigma_dmu(sigma0_over_m,v,w,1.0);
}

/* Exact analytic integral of the frozen Moller differential law. */
static inline double d3_moller_sigma_total(double sigma0_over_m, double v, double w)
{
    double y=(v/w)*(v/w);
    double f;
    if(y < 1.0e-6)
        f = 0.5 - 0.5*y + (7.0/12.0)*y*y;
    else
        f = (y*y + 2.0*y - (y+1.0)*log1p(y)) / (y*(y+1.0)*(y+2.0));
    return sigma0_over_m*f;
}

/* Convert the frozen channel normalization to sigma/m_eff for a symmetric pair event.
 * For HL, sigma_H*m_H == sigma_L*m_L is the same physical cross section. */
static inline double d3_sigma_over_meff_for_pair(double mi, double mj, int si, int sj, double vrel)
{
    int ch=d3_channel_from_species(si,sj);
    if(ch==D3_CHANNEL_HH) return d3_moller_sigma_total(D3_SIGMA_HH_OVER_MH,vrel,D3_W_HH_KMS);
    if(ch==D3_CHANNEL_LL) return d3_moller_sigma_total(D3_SIGMA_LL_OVER_ML,vrel,D3_W_LL_KMS);
    if(ch==D3_CHANNEL_HL)
    {
        double mH=(si==D3_SPECIES_H)?mi:mj;
        double meff=0.5*(mi+mj);
        double sigma_phys=D3_SIGMA_HL_OVER_MH*mH;
        return (meff>0.0) ? d3_rutherford_sigma_total(sigma_phys/meff,vrel,D3_W_HL_KMS) : 0.0;
    }
    return 0.0;
}

static inline double d3_prob_of_interaction(double mi, double mj, double r, double h_si, double dV[3], double dt, int si, int sj)
{
    double dVmag, rho_eff, sigma_over_meff, cx_eff;
    if(d3_channel_from_species(si,sj)==D3_CHANNEL_NONE || h_si<=0.0 || dt<=0.0) return 0.0;
    dVmag=sqrt(dV[0]*dV[0]+dV[1]*dV[1]+dV[2]*dV[2])/All.cf_atime;
    rho_eff=(0.5*(mi+mj))/(h_si*h_si*h_si)*All.cf_a3inv;
    sigma_over_meff=d3_sigma_over_meff_for_pair(mi,mj,si,sj,dVmag);
    cx_eff=sigma_over_meff*g_geo(r/h_si);
    return rho_eff*cx_eff*dVmag*dt*UNIT_SURFDEN_IN_CGS;
}

/* Build the outgoing relative-velocity unit vector at polar cosine mu relative to dV. */
static inline void d3_scatter_direction(const double dV[3], double mu, double phi, double nhat[3])
{
    double g=sqrt(dV[0]*dV[0]+dV[1]*dV[1]+dV[2]*dV[2]);
    double ez[3], ex[3], ey[3], s;
    if(g<=0.0) {nhat[0]=1.0; nhat[1]=0.0; nhat[2]=0.0; return;}
    ez[0]=dV[0]/g; ez[1]=dV[1]/g; ez[2]=dV[2]/g;
    if(fabs(ez[0])<0.9) {ex[0]=0.0; ex[1]=-ez[2]; ex[2]=ez[1];}
    else {ex[0]=-ez[2]; ex[1]=0.0; ex[2]=ez[0];}
    s=sqrt(ex[0]*ex[0]+ex[1]*ex[1]+ex[2]*ex[2]);
    ex[0]/=s; ex[1]/=s; ex[2]/=s;
    ey[0]=ez[1]*ex[2]-ez[2]*ex[1];
    ey[1]=ez[2]*ex[0]-ez[0]*ex[2];
    ey[2]=ez[0]*ex[1]-ez[1]*ex[0];
    s=sqrt(fmax(0.0,1.0-mu*mu));
    nhat[0]=mu*ez[0]+s*(cos(phi)*ex[0]+sin(phi)*ey[0]);
    nhat[1]=mu*ez[1]+s*(cos(phi)*ex[1]+sin(phi)*ey[1]);
    nhat[2]=mu*ez[2]+s*(cos(phi)*ex[2]+sin(phi)*ey[2]);
}

static inline void d3_calculate_interact_kick_from_unit(double dV[3], double mi, double mj, double nhat[3], double kick_i[3], double kick_j[3])
{
    int k; double mtot=mi+mj, vrel_mag=sqrt(dV[0]*dV[0]+dV[1]*dV[1]+dV[2]*dV[2]);
    if(mtot<=0.0) {for(k=0;k<3;k++){kick_i[k]=0.0;kick_j[k]=0.0;} return;}
    for(k=0;k<3;k++)
    {
        double vi_old=(mj/mtot)*dV[k], vj_old=-(mi/mtot)*dV[k];
        double vi_new=(mj/mtot)*vrel_mag*nhat[k], vj_new=-(mi/mtot)*vrel_mag*nhat[k];
        kick_i[k]=vi_new-vi_old;
        kick_j[k]=vj_new-vj_old;
    }
}

#endif
