#ifndef D3_SIDMX_KERNEL_INLINE_H
#define D3_SIDMX_KERNEL_INLINE_H

#include <math.h>

/* Frozen D3/SIDMx microscopic kernel helpers.
 * Embeddable inside GIZMO's flux include blocks: GNU-C statement-expression
 * macros are used so this header remains legal when included from function scope.
 * Particle Type 2 -> heavy H; Particle Type 3 -> light L.
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

#define d3_species_from_type(type_) \
    (((type_)==D3_TYPE_H)?D3_SPECIES_H:(((type_)==D3_TYPE_L)?D3_SPECIES_L:D3_SPECIES_NONE))

#define d3_channel_from_species(si_,sj_) \
    ((((si_)==D3_SPECIES_H)&&((sj_)==D3_SPECIES_H))?D3_CHANNEL_HH: \
     ((((si_)==D3_SPECIES_L)&&((sj_)==D3_SPECIES_L))?D3_CHANNEL_LL: \
     (((((si_)==D3_SPECIES_H)&&((sj_)==D3_SPECIES_L))||(((si_)==D3_SPECIES_L)&&((sj_)==D3_SPECIES_H)))?D3_CHANNEL_HL:D3_CHANNEL_NONE)))

#define d3_rutherford_dsigma_dmu(s0_,v_,w_,mu_) ({ \
    double d3rd_s0=(s0_),d3rd_v=(v_),d3rd_w=(w_),d3rd_mu=(mu_); \
    double d3rd_den=d3rd_w*d3rd_w+0.5*d3rd_v*d3rd_v*(1.0-d3rd_mu); \
    0.5*d3rd_s0*d3rd_w*d3rd_w*d3rd_w*d3rd_w/(d3rd_den*d3rd_den); })

#define d3_rutherford_sigma_total(s0_,v_,w_) ({ \
    double d3rt_x=(v_)/(w_); \
    (s0_)/(1.0+d3rt_x*d3rt_x); })

#define d3_rutherford_mu_from_u(v_,w_,u_) ({ \
    double d3ru_v=(v_),d3ru_w=(w_),d3ru_u=(u_),d3ru_mu; \
    double d3ru_x=d3ru_v/d3ru_w,d3ru_x2=d3ru_x*d3ru_x; \
    if(d3ru_u<=0.0) { d3ru_mu=-1.0; } \
    else if(d3ru_u>=1.0) { d3ru_mu=1.0; } \
    else { d3ru_mu=1.0-2.0*(1.0-d3ru_u)/(1.0+d3ru_u*d3ru_x2); } \
    d3ru_mu; })

#define d3_moller_dsigma_dmu(s0_,v_,w_,mu_) ({ \
    double d3md_s0=(s0_),d3md_v=(v_),d3md_w=(w_),d3md_mu=(mu_); \
    double d3md_v2=d3md_v*d3md_v,d3md_w2=d3md_w*d3md_w; \
    double d3md_v4=d3md_v2*d3md_v2,d3md_w4=d3md_w2*d3md_w2; \
    double d3md_num=(3.0*d3md_mu*d3md_mu+1.0)*d3md_v4+4.0*d3md_v2*d3md_w2+4.0*d3md_w4; \
    double d3md_den=(1.0-d3md_mu*d3md_mu)*d3md_v4+4.0*d3md_v2*d3md_w2+4.0*d3md_w4; \
    d3md_s0*d3md_w4*d3md_num/(d3md_den*d3md_den); })

#define d3_moller_dsigma_max(s0_,v_,w_) d3_moller_dsigma_dmu((s0_),(v_),(w_),1.0)

#define d3_moller_sigma_total(s0_,v_,w_) ({ \
    double d3mt_s0=(s0_),d3mt_y=((v_)/(w_))*((v_)/(w_)),d3mt_f; \
    if(d3mt_y<1.0e-6) { d3mt_f=0.5-0.5*d3mt_y+(7.0/12.0)*d3mt_y*d3mt_y; } \
    else { d3mt_f=(d3mt_y*d3mt_y+2.0*d3mt_y-(d3mt_y+1.0)*log1p(d3mt_y))/(d3mt_y*(d3mt_y+1.0)*(d3mt_y+2.0)); } \
    d3mt_s0*d3mt_f; })

#define d3_sigma_over_meff_for_pair(mi_,mj_,si_,sj_,vrel_) ({ \
    double d3s_mi=(mi_),d3s_mj=(mj_),d3s_vrel=(vrel_),d3s_ans=0.0; \
    int d3s_si=(si_),d3s_sj=(sj_),d3s_ch=d3_channel_from_species(d3s_si,d3s_sj); \
    if(d3s_ch==D3_CHANNEL_HH) { \
        d3s_ans=d3_moller_sigma_total(D3_SIGMA_HH_OVER_MH,d3s_vrel,D3_W_HH_KMS); \
    } else if(d3s_ch==D3_CHANNEL_LL) { \
        d3s_ans=d3_moller_sigma_total(D3_SIGMA_LL_OVER_ML,d3s_vrel,D3_W_LL_KMS); \
    } else if(d3s_ch==D3_CHANNEL_HL) { \
        double d3s_mH=(d3s_si==D3_SPECIES_H)?d3s_mi:d3s_mj; \
        double d3s_meff=0.5*(d3s_mi+d3s_mj); \
        double d3s_sigma_phys=D3_SIGMA_HL_OVER_MH*d3s_mH; \
        if(d3s_meff>0.0) { d3s_ans=d3_rutherford_sigma_total(d3s_sigma_phys/d3s_meff,d3s_vrel,D3_W_HL_KMS); } \
    } \
    d3s_ans; })

#define d3_prob_of_interaction(mi_,mj_,r_,h_,dV_,dt_,si_,sj_) ({ \
    double d3p_mi=(mi_),d3p_mj=(mj_),d3p_r=(r_),d3p_h=(h_),d3p_dt=(dt_),d3p_p=0.0; \
    int d3p_si=(si_),d3p_sj=(sj_); \
    if(d3_channel_from_species(d3p_si,d3p_sj)!=D3_CHANNEL_NONE && d3p_h>0.0 && d3p_dt>0.0) { \
        double d3p_vmag=sqrt((dV_)[0]*(dV_)[0]+(dV_)[1]*(dV_)[1]+(dV_)[2]*(dV_)[2])/All.cf_atime; \
        double d3p_rho=(0.5*(d3p_mi+d3p_mj))/(d3p_h*d3p_h*d3p_h)*All.cf_a3inv; \
        double d3p_som=d3_sigma_over_meff_for_pair(d3p_mi,d3p_mj,d3p_si,d3p_sj,d3p_vmag); \
        d3p_p=d3p_rho*d3p_som*g_geo(d3p_r/d3p_h)*d3p_vmag*d3p_dt*UNIT_SURFDEN_IN_CGS; \
    } \
    d3p_p; })

#define d3_scatter_direction(dV_,mu_,phi_,nhat_) do { \
    double d3sd_g=sqrt((dV_)[0]*(dV_)[0]+(dV_)[1]*(dV_)[1]+(dV_)[2]*(dV_)[2]); \
    double d3sd_ez[3],d3sd_ex[3],d3sd_ey[3],d3sd_s,d3sd_mu=(mu_),d3sd_phi=(phi_); \
    if(d3sd_g<=0.0) { \
        (nhat_)[0]=1.0; (nhat_)[1]=0.0; (nhat_)[2]=0.0; \
    } else { \
        d3sd_ez[0]=(dV_)[0]/d3sd_g; d3sd_ez[1]=(dV_)[1]/d3sd_g; d3sd_ez[2]=(dV_)[2]/d3sd_g; \
        if(fabs(d3sd_ez[0])<0.9) { d3sd_ex[0]=0.0; d3sd_ex[1]=-d3sd_ez[2]; d3sd_ex[2]=d3sd_ez[1]; } \
        else { d3sd_ex[0]=-d3sd_ez[2]; d3sd_ex[1]=0.0; d3sd_ex[2]=d3sd_ez[0]; } \
        d3sd_s=sqrt(d3sd_ex[0]*d3sd_ex[0]+d3sd_ex[1]*d3sd_ex[1]+d3sd_ex[2]*d3sd_ex[2]); \
        d3sd_ex[0]/=d3sd_s; d3sd_ex[1]/=d3sd_s; d3sd_ex[2]/=d3sd_s; \
        d3sd_ey[0]=d3sd_ez[1]*d3sd_ex[2]-d3sd_ez[2]*d3sd_ex[1]; \
        d3sd_ey[1]=d3sd_ez[2]*d3sd_ex[0]-d3sd_ez[0]*d3sd_ex[2]; \
        d3sd_ey[2]=d3sd_ez[0]*d3sd_ex[1]-d3sd_ez[1]*d3sd_ex[0]; \
        d3sd_s=sqrt(fmax(0.0,1.0-d3sd_mu*d3sd_mu)); \
        (nhat_)[0]=d3sd_mu*d3sd_ez[0]+d3sd_s*(cos(d3sd_phi)*d3sd_ex[0]+sin(d3sd_phi)*d3sd_ey[0]); \
        (nhat_)[1]=d3sd_mu*d3sd_ez[1]+d3sd_s*(cos(d3sd_phi)*d3sd_ex[1]+sin(d3sd_phi)*d3sd_ey[1]); \
        (nhat_)[2]=d3sd_mu*d3sd_ez[2]+d3sd_s*(cos(d3sd_phi)*d3sd_ex[2]+sin(d3sd_phi)*d3sd_ey[2]); \
    } \
} while(0)

#define d3_calculate_interact_kick_from_unit(dV_,mi_,mj_,nhat_,ki_,kj_) do { \
    int d3k_k; \
    double d3k_mi=(mi_),d3k_mj=(mj_),d3k_mt=d3k_mi+d3k_mj; \
    double d3k_vr=sqrt((dV_)[0]*(dV_)[0]+(dV_)[1]*(dV_)[1]+(dV_)[2]*(dV_)[2]); \
    if(d3k_mt<=0.0) { \
        for(d3k_k=0;d3k_k<3;d3k_k++) { (ki_)[d3k_k]=0.0; (kj_)[d3k_k]=0.0; } \
    } else { \
        for(d3k_k=0;d3k_k<3;d3k_k++) { \
            double d3k_vio=(d3k_mj/d3k_mt)*(dV_)[d3k_k],d3k_vjo=-(d3k_mi/d3k_mt)*(dV_)[d3k_k]; \
            double d3k_vin=(d3k_mj/d3k_mt)*d3k_vr*(nhat_)[d3k_k],d3k_vjn=-(d3k_mi/d3k_mt)*d3k_vr*(nhat_)[d3k_k]; \
            (ki_)[d3k_k]=d3k_vin-d3k_vio; (kj_)[d3k_k]=d3k_vjn-d3k_vjo; \
        } \
    } \
} while(0)

#endif
