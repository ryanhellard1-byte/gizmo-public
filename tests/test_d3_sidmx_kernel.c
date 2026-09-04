#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "../sidm/d3_sidmx_kernel.h"

static uint64_t state=0x9e3779b97f4a7c15ULL;
static double rng01(void){ state ^= state>>12; state ^= state<<25; state ^= state>>27; return ((state*2685821657736338717ULL)>>11)*(1.0/9007199254740992.0); }
static double relerr(double a,double b){double s=fmax(fmax(fabs(a),fabs(b)),1e-300);return fabs(a-b)/s;}

static double simpson_segment(int ch,double v,int type,double a,double b)
{
    double c=0.5*(a+b);
    double fa=d3_sidmx_differential_xsec_per_mass(ch,a,v,type);
    double fb=d3_sidmx_differential_xsec_per_mass(ch,b,v,type);
    double fc=d3_sidmx_differential_xsec_per_mass(ch,c,v,type);
    return (b-a)*(fa+4.0*fc+fb)/6.0;
}

static double adaptive_simpson_rec(int ch,double v,int type,double a,double b,double whole,double tol,int depth)
{
    double c=0.5*(a+b);
    double left=simpson_segment(ch,v,type,a,c), right=simpson_segment(ch,v,type,c,b);
    double delta=left+right-whole;
    if(depth<=0 || fabs(delta)<=15.0*tol) return left+right+delta/15.0;
    return adaptive_simpson_rec(ch,v,type,a,c,left,0.5*tol,depth-1)+adaptive_simpson_rec(ch,v,type,c,b,right,0.5*tol,depth-1);
}

static double numerical_total(int ch,double v,int type)
{
    double whole=simpson_segment(ch,v,type,-1.0,1.0);
    return adaptive_simpson_rec(ch,v,type,-1.0,1.0,whole,1e-12,24);
}

int main(void){
    const double vs[]={0.0,50.0,81.68153862497117,300.0,1000.0,3000.0};
    double worst_total=0,worst_p=0,worst_e=0,worst_mu=0; int iv,ch,n;
    int channels[]={D3_CH_HH,D3_CH_LL,D3_CH_HL}; int types[]={D3_SIDMX_H_TYPE,D3_SIDMX_L_TYPE,D3_SIDMX_H_TYPE};
    for(ch=0;ch<3;ch++) for(iv=0;iv<6;iv++) {
        double exact=d3_sidmx_total_xsec_per_mass(channels[ch],vs[iv],types[ch]);
        double num=numerical_total(channels[ch],vs[iv],types[ch]);
        double er=relerr(exact,num); if(er>worst_total) worst_total=er;
    }
    for(n=0;n<100000;n++) {
        int channel=channels[n%3];
        double mi=(channel==D3_CH_LL)?1.0:3.0, mj=(channel==D3_CH_HH)?3.0:1.0;
        if(channel==D3_CH_HL && (n&1)){mi=1.0;mj=3.0;}
        double vi[3]={400*rng01()-200,400*rng01()-200,400*rng01()-200};
        double vj[3]={400*rng01()-200,400*rng01()-200,400*rng01()-200};
        double dv[3]={vi[0]-vj[0],vi[1]-vj[1],vi[2]-vj[2]};
        double speed=sqrt(dv[0]*dv[0]+dv[1]*dv[1]+dv[2]*dv[2]);
        double u_mu=rng01(),u_phi=rng01(),kick[3],mu=d3_sidmx_sample_mu(channel,speed,u_mu);
        double msi=0.5*(mi+mj), vi2[3],vj2[3],p0[3],p1[3],uin2[3]; int k;
        d3_sidmx_make_kick(dv,channel,speed,u_mu,u_phi,kick);
        for(k=0;k<3;k++){vi2[k]=vi[k]-(mj/msi)*kick[k]; vj2[k]=vj[k]+(mi/msi)*kick[k]; p0[k]=mi*vi[k]+mj*vj[k]; p1[k]=mi*vi2[k]+mj*vj2[k]; uin2[k]=vi2[k]-vj2[k];}
        {
            double pn=sqrt(p0[0]*p0[0]+p0[1]*p0[1]+p0[2]*p0[2]);
            double pd=sqrt((p1[0]-p0[0])*(p1[0]-p0[0])+(p1[1]-p0[1])*(p1[1]-p0[1])+(p1[2]-p0[2])*(p1[2]-p0[2]));
            double pe=pd/fmax(pn,1.0); if(pe>worst_p)worst_p=pe;
        }
        {
            double e0=0,e1=0; for(k=0;k<3;k++){e0+=0.5*mi*vi[k]*vi[k]+0.5*mj*vj[k]*vj[k];e1+=0.5*mi*vi2[k]*vi2[k]+0.5*mj*vj2[k]*vj2[k];}
            double ee=relerr(e0,e1);if(ee>worst_e)worst_e=ee;
        }
        if(speed>0){double realized=(dv[0]*uin2[0]+dv[1]*uin2[1]+dv[2]*uin2[2])/(speed*sqrt(uin2[0]*uin2[0]+uin2[1]*uin2[1]+uin2[2]*uin2[2]));double me=fabs(realized-mu);if(me>worst_mu)worst_mu=me;}
    }
    printf("worst_total_relerr %.17g\n",worst_total);
    printf("worst_momentum_relerr %.17g\n",worst_p);
    printf("worst_energy_relerr %.17g\n",worst_e);
    printf("worst_mu_abs_err %.17g\n",worst_mu);
    {
        double v=81.68153862497117,w=2200.0,s0=1.125,x=(v/w)*(v/w);
        double sigmaT=2*s0*(log1p(x)-x/(1+x))/(x*x);
        printf("HL_sigmaT_M11 %.15f\n",sigmaT);
        if(fabs(sigmaT-1.122935472452217)>2e-12) return 2;
    }
    if(worst_total>2e-8 || worst_p>2e-12 || worst_e>2e-12 || worst_mu>2e-12) return 1;
    puts("STATUS PASS"); return 0;
}
