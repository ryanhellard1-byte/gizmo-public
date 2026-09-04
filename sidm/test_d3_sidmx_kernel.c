#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define UNIT_SURFDEN_IN_CGS 1.0
struct global_data_all_processes { double cf_atime; double cf_a3inv; } All={1.0,1.0};
double g_geo(double r) {(void)r; return 1.0;}
#include "d3_sidmx_kernel_inline.h"

static double ke(double m,const double v[3]) {return 0.5*m*(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);}
static double n3(const double x[3]) {return sqrt(x[0]*x[0]+x[1]*x[1]+x[2]*x[2]);}
static int close_rel(double a,double b,double tol) {return fabs(a-b)<=tol*fmax(1.0,fmax(fabs(a),fabs(b)));}

static int test_integrated_laws(void)
{
    int fail=0, i, n=20000;
    double v=713.0,w=825.0,s0=2.2966666667,h=2.0/n,sum=0.0;
    double exact=d3_moller_sigma_total(s0,v,w);
    for(i=0;i<=n;i++)
    {
        double mu=-1.0+i*h;
        double f=d3_moller_dsigma_dmu(s0,v,w,mu);
        sum += ((i==0||i==n)?1.0:((i&1)?4.0:2.0))*f;
        if(f>d3_moller_dsigma_max(s0,v,w)*(1.0+1.0e-13)) fail=1;
    }
    sum*=h/3.0;
    if(!close_rel(sum,exact,2.0e-10)) {fprintf(stderr,"Moller integral mismatch %.17e %.17e\n",sum,exact); fail=1;}
    if(!close_rel(d3_rutherford_sigma_total(1.125,2200.0,2200.0),0.5625,1.0e-14)) {fprintf(stderr,"Rutherford total mismatch\n"); fail=1;}
    if(!close_rel(d3_sigma_over_meff_for_pair(3.0,1.0,D3_SPECIES_H,D3_SPECIES_L,0.0),1.6875,1.0e-14)) {fprintf(stderr,"HL meff normalization mismatch\n"); fail=1;}
    for(i=1;i<1000;i++)
    {
        double u=i/1000.0, mu=d3_rutherford_mu_from_u(1700.0,2200.0,u);
        double x=1700.0/2200.0, t=1.0-mu;
        double uback=(2.0-t)/(2.0+t*x*x);
        if(!close_rel(u,uback,2.0e-14)) {fprintf(stderr,"Rutherford inverse CDF mismatch\n"); fail=1; break;}
    }
    printf("integrated-laws moller_numeric=%.17e moller_exact=%.17e\n",sum,exact);
    return fail;
}

static int test_pair(const char *label,int ti,int tj,double mi,double mj,double mu,double phi)
{
    double dv[3]={400.0,-250.0,100.0},nhat[3],ki[3],kj[3],p0[3],p1[3],dp[3];
    double vi0[3],vj0[3],vi1[3],vj1[3],mt=mi+mj;
    int si=d3_species_from_type(ti),sj=d3_species_from_type(tj),ch=d3_channel_from_species(si,sj),k;
    double prob=d3_prob_of_interaction(mi,mj,0.10,1.0,dv,0.00001,si,sj);
    if(si==D3_SPECIES_NONE||sj==D3_SPECIES_NONE||ch==D3_CHANNEL_NONE||!(prob>0.0)||!isfinite(prob)) return 1;
    d3_scatter_direction(dv,mu,phi,nhat);
    if(!close_rel(n3(nhat),1.0,1.0e-13)) {fprintf(stderr,"%s nhat not unit\n",label); return 1;}
    for(k=0;k<3;k++) {vi0[k]=(mj/mt)*dv[k]; vj0[k]=-(mi/mt)*dv[k]; p0[k]=mi*vi0[k]+mj*vj0[k];}
    d3_calculate_interact_kick_from_unit(dv,mi,mj,nhat,ki,kj);
    for(k=0;k<3;k++) {vi1[k]=vi0[k]+ki[k]; vj1[k]=vj0[k]+kj[k]; p1[k]=mi*vi1[k]+mj*vj1[k]; dp[k]=p1[k]-p0[k];}
    {
        double kb=ke(mi,vi0)+ke(mj,vj0),ka=ke(mi,vi1)+ke(mj,vj1);
        double rdp=n3(dp)/fmax(1.0,n3(p0)),rdk=fabs(ka-kb)/fmax(1.0e-30,fabs(kb));
        printf("%s channel=%d prob=%.17e rel_dP=%.17e rel_dK=%.17e\n",label,ch,prob,rdp,rdk);
        if(rdp>1.0e-12||rdk>1.0e-12) return 1;
    }
    return 0;
}

int main(void)
{
    int fail=0;
    fail|=test_integrated_laws();
    fail|=test_pair("HH",D3_TYPE_H,D3_TYPE_H,3.0,3.0,0.71,0.31);
    fail|=test_pair("LL",D3_TYPE_L,D3_TYPE_L,1.0,1.0,-0.42,2.11);
    fail|=test_pair("HL",D3_TYPE_H,D3_TYPE_L,3.0,1.0,0.83,1.27);
    fail|=test_pair("LH",D3_TYPE_L,D3_TYPE_H,1.0,3.0,-0.18,5.03);
    if(fail) {puts("D3_SIDMX_PAIR_LAW: FAIL"); return 1;}
    puts("D3_SIDMX_PAIR_LAW: PASS");
    return 0;
}
