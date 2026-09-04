#include <math.h>
#include <stddef.h>
#include "d3_sidmx_kernel.h"

#ifndef M_PI
#define M_PI 3.141592653589793238462643383279502884
#endif

#define D3_MASS_RATIO_H_OVER_L 3.0
#define D3_SIGMA0_HH_OVER_MH 6.89
#define D3_W_HH_KMS 275.0
#define D3_SIGMA0_LL_OVER_ML (6.89/3.0)
#define D3_W_LL_KMS 825.0
#define D3_SIGMA0_HL_OVER_MH 1.125
#define D3_W_HL_KMS 2200.0

static double d3_clamp(double x, double lo, double hi)
{
    return x < lo ? lo : (x > hi ? hi : x);
}

int d3_sidmx_channel_from_types(int type_i, int type_j)
{
    const int iH = (type_i == D3_SIDMX_H_TYPE), iL = (type_i == D3_SIDMX_L_TYPE);
    const int jH = (type_j == D3_SIDMX_H_TYPE), jL = (type_j == D3_SIDMX_L_TYPE);
    if(iH && jH) return D3_CH_HH;
    if(iL && jL) return D3_CH_LL;
    if((iH && jL) || (iL && jH)) return D3_CH_HL;
    return D3_CH_NONE;
}

int d3_sidmx_channel_enabled(int channel)
{
    return channel != D3_CH_NONE && ((D3_SIDMX_CHANNEL_MASK & channel) != 0);
}

const char *d3_sidmx_channel_name(int channel)
{
    if(channel == D3_CH_HH) return "HH";
    if(channel == D3_CH_LL) return "LL";
    if(channel == D3_CH_HL) return "HL";
    return "NONE";
}

static double d3_channel_sigma0(int channel, int basis_type)
{
    if(channel == D3_CH_HH) {
        return (basis_type == D3_SIDMX_H_TYPE) ? D3_SIGMA0_HH_OVER_MH : 0.0;
    }
    if(channel == D3_CH_LL) {
        return (basis_type == D3_SIDMX_L_TYPE) ? D3_SIGMA0_LL_OVER_ML : 0.0;
    }
    if(channel == D3_CH_HL) {
        if(basis_type == D3_SIDMX_H_TYPE) return D3_SIGMA0_HL_OVER_MH;
        if(basis_type == D3_SIDMX_L_TYPE) return D3_MASS_RATIO_H_OVER_L * D3_SIGMA0_HL_OVER_MH;
    }
    return 0.0;
}

static double d3_channel_w(int channel)
{
    if(channel == D3_CH_HH) return D3_W_HH_KMS;
    if(channel == D3_CH_LL) return D3_W_LL_KMS;
    if(channel == D3_CH_HL) return D3_W_HL_KMS;
    return 0.0;
}

double d3_sidmx_differential_xsec_per_mass(int channel, double mu, double v_km_s, int basis_type)
{
    const double s0 = d3_channel_sigma0(channel, basis_type);
    const double w = d3_channel_w(channel);
    double v, v2, w2, v4, w4;
    if(s0 <= 0.0 || w <= 0.0) return 0.0;
    mu = d3_clamp(mu, -1.0, 1.0);
    v = fabs(v_km_s);
    v2 = v*v; w2 = w*w; v4 = v2*v2; w4 = w2*w2;

    if(channel == D3_CH_HL) {
        const double q = w2 + 0.5*v2*(1.0-mu);
        return s0*w4/(2.0*q*q);
    }

    if(channel == D3_CH_HH || channel == D3_CH_LL) {
        const double num = s0*w4*((3.0*mu*mu+1.0)*v4 + 4.0*v2*w2 + 4.0*w4);
        const double den0 = (1.0-mu*mu)*v4 + 4.0*v2*w2 + 4.0*w4;
        return num/(den0*den0);
    }
    return 0.0;
}

static double d3_moller_F1(double k)
{
    if(k < 1.0e-8) {
        const double k2=k*k, k3=k2*k;
        return 1.0 + (5.0/3.0)*k + (9.0/5.0)*k2 + (13.0/7.0)*k3;
    }
    {
        const double sk = sqrt(k);
        return 2.0/(1.0-k) - atanh(sk)/sk;
    }
}

static double d3_moller_F(double z, double k)
{
    z = d3_clamp(z, 0.0, 1.0);
    if(k < 1.0e-8) {
        const double z2=z*z, z3=z*z2, z5=z3*z2, z7=z5*z2;
        return z + (5.0/3.0)*k*z3 + (9.0/5.0)*k*k*z5 + (13.0/7.0)*k*k*k*z7;
    }
    {
        const double sk = sqrt(k);
        return 2.0*z/(1.0-k*z*z) - atanh(sk*z)/sk;
    }
}

double d3_sidmx_total_xsec_per_mass(int channel, double v_km_s, int basis_type)
{
    const double s0 = d3_channel_sigma0(channel, basis_type);
    const double w = d3_channel_w(channel);
    const double v = fabs(v_km_s);
    if(s0 <= 0.0 || w <= 0.0) return 0.0;

    if(channel == D3_CH_HL) {
        const double x = (v/w)*(v/w);
        return s0/(1.0+x);
    }

    if(channel == D3_CH_HH || channel == D3_CH_LL) {
        const double v2=v*v, w2=w*w;
        const double c=(v2+2.0*w2)*(v2+2.0*w2);
        const double k=(v2*v2)/c;
        const double pref=s0*(w2*w2)/c;
        return 2.0*pref*d3_moller_F1(k);
    }
    return 0.0;
}

double d3_sidmx_sample_mu(int channel, double v_km_s, double u)
{
    const double v=fabs(v_km_s), w=d3_channel_w(channel);
    u=d3_clamp(u, 0.0, 1.0-0x1p-53);
    if(w <= 0.0) return 1.0;

    if(channel == D3_CH_HL) {
        const double a=(v/w)*(v/w);
        if(a < 1.0e-10) return 2.0*u-1.0;
        {
            const double inv_t=(1.0 + u*a)/(1.0+a);
            const double t=1.0/inv_t;
            return d3_clamp(1.0 - 2.0*(t-1.0)/a, -1.0, 1.0);
        }
    }

    if(channel == D3_CH_HH || channel == D3_CH_LL) {
        const double v2=v*v, w2=w*w;
        const double c=(v2+2.0*w2)*(v2+2.0*w2);
        const double k=(v2*v2)/c;
        if(k < 1.0e-10) return 2.0*u-1.0;
        {
            const int sign = (u < 0.5) ? -1 : 1;
            const double q = ((u < 0.5) ? (2.0*u) : (2.0*u-1.0))*d3_moller_F1(k);
            double lo=0.0, hi=1.0, mid=0.5;
            int it;
            for(it=0; it<56; it++) {
                mid=0.5*(lo+hi);
                if(d3_moller_F(mid,k) < q) lo=mid; else hi=mid;
            }
            return sign*0.5*(lo+hi);
        }
    }
    return 1.0;
}

static void d3_basis_from_direction(const double n[3], double e1[3], double e2[3])
{
    double a[3], norm;
    if(fabs(n[0]) < 0.8) {a[0]=1.0; a[1]=0.0; a[2]=0.0;}
    else {a[0]=0.0; a[1]=1.0; a[2]=0.0;}

    e1[0]=n[1]*a[2]-n[2]*a[1];
    e1[1]=n[2]*a[0]-n[0]*a[2];
    e1[2]=n[0]*a[1]-n[1]*a[0];
    norm=sqrt(e1[0]*e1[0]+e1[1]*e1[1]+e1[2]*e1[2]);
    e1[0]/=norm; e1[1]/=norm; e1[2]/=norm;
    e2[0]=n[1]*e1[2]-n[2]*e1[1];
    e2[1]=n[2]*e1[0]-n[0]*e1[2];
    e2[2]=n[0]*e1[1]-n[1]*e1[0];
}

void d3_sidmx_make_kick(const double dV[3], int channel, double v_km_s,
                        double u_mu, double u_phi, double kick[3])
{
    const double speed=sqrt(dV[0]*dV[0]+dV[1]*dV[1]+dV[2]*dV[2]);
    double n[3],e1[3],e2[3],nout[3],mu,sint,phi;
    int k;
    if(speed <= 0.0 || channel == D3_CH_NONE) {kick[0]=kick[1]=kick[2]=0.0; return;}
    for(k=0;k<3;k++) n[k]=dV[k]/speed;
    d3_basis_from_direction(n,e1,e2);
    mu=d3_sidmx_sample_mu(channel,v_km_s,u_mu);
    sint=sqrt(fmax(0.0,1.0-mu*mu));
    phi=2.0*M_PI*d3_clamp(u_phi,0.0,1.0-0x1p-53);
    for(k=0;k<3;k++) {
        nout[k]=mu*n[k]+sint*(cos(phi)*e1[k]+sin(phi)*e2[k]);
        kick[k]=0.5*(dV[k]-speed*nout[k]);
    }
}
