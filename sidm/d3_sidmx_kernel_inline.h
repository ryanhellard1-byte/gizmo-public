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
    double _s0=(s0_),_v=(v_),_w=(w_),_mu=(mu_); \
    double _den=_w*_w+0.5*_v*_v*(1.0-_mu); \
    0.5*_s0*_w*_w*_w*_w/(_den*_den); })

#define d3_rutherford_sigma_total(s0_,v_,w_) ({ \
    double _x=(v_)/(w_); (s0_)/(1.0+_x*_x); })

#define d3_rutherford_mu_from_u(v_,w_,u_) ({ \
    double _v=(v_),_w=(w_),_u=(u_),_mu; double _x=_v/_w,_x2=_x*_x; \
    if(_u<=0.0) _mu=-1.0; else if(_u>=1.0) _mu=1.0; \
    else _mu=1.0-2.0*(1.0-_u)/(1.0+_u*_x2); _mu; })

#define d3_moller_dsigma_dmu(s0_,v_,w_,mu_) ({ \
    double _s0=(s0_),_v=(v_),_w=(w_),_mu=(mu_); \
    double _v2=_v*_v,_w2=_w*_w,_v4=_v2*_v2,_w4=_w2*_w2; \
    double _num=(3.0*_mu*_mu+1.0)*_v4+4.0*_v2*_w2+4.0*_w4; \
    double _den=(1.0-_mu*_mu)*_v4+4.0*_v2*_w2+4.0*_w4; \
    _s0*_w4*_num/(_den*_den); })

#define d3_moller_dsigma_max(s0_,v_,w_) d3_moller_dsigma_dmu((s0_),(v_),(w_),1.0)

#define d3_moller_sigma_total(s0_,v_,w_) ({ \
    double _s0=(s0_),_y=((v_)/(w_))*((v_)/(w_)),_f; \
    if(_y<1.0e-6) _f=0.5-0.5*_y+(7.0/12.0)*_y*_y; \
    else _f=(_y*_y+2.0*_y-(_y+1.0)*log1p(_y))/(_y*(_y+1.0)*(_y+2.0)); \
    _s0*_f; })

#define d3_sigma_over_meff_for_pair(mi_,mj_,si_,sj_,vrel_) ({ \
    double _mi=(mi_),_mj=(mj_),_vrel=(vrel_),_ans=0.0; int _si=(si_),_sj=(sj_); \
    int _ch=d3_channel_from_species(_si,_sj); \
    if(_ch==D3_CHANNEL_HH) _ans=d3_moller_sigma_total(D3_SIGMA_HH_OVER_MH,_vrel,D3_W_HH_KMS); \
    else if(_ch==D3_CHANNEL_LL) _ans=d3_moller_sigma_total(D3_SIGMA_LL_OVER_ML,_vrel,D3_W_LL_KMS); \
    else if(_ch==D3_CHANNEL_HL) { double _mH=(_si==D3_SPECIES_H)?_mi:_mj; double _meff=0.5*(_mi+_mj); \
        double _sigma_phys=D3_SIGMA_HL_OVER_MH*_mH; \
        if(_meff>0.0) _ans=d3_rutherford_sigma_total(_sigma_phys/_meff,_vrel,D3_W_HL_KMS); } \
    _ans; })

#define d3_prob_of_interaction(mi_,mj_,r_,h_,dV_,dt_,si_,sj_) ({ \
    double _mi=(mi_),_mj=(mj_),_r=(r_),_h=(h_),_dt=(dt_),_p=0.0; int _si=(si_),_sj=(sj_); \
    if(d3_channel_from_species(_si,_sj)!=D3_CHANNEL_NONE && _h>0.0 && _dt>0.0) { \
        double _vmag=sqrt((dV_)[0]*(dV_)[0]+(dV_)[1]*(dV_)[1]+(dV_)[2]*(dV_)[2])/All.cf_atime; \
        double _rho=(0.5*(_mi+_mj))/(_h*_h*_h)*All.cf_a3inv; \
        double _som=d3_sigma_over_meff_for_pair(_mi,_mj,_si,_sj,_vmag); \
        _p=_rho*_som*g_geo(_r/_h)*_vmag*_dt*UNIT_SURFDEN_IN_CGS; } \
    _p; })

#define d3_scatter_direction(dV_,mu_,phi_,nhat_) do { \
    double _g=sqrt((dV_)[0]*(dV_)[0]+(dV_)[1]*(dV_)[1]+(dV_)[2]*(dV_)[2]); \
    double _ez[3],_ex[3],_ey[3],_s,_mu=(mu_),_phi=(phi_); \
    if(_g<=0.0) { (nhat_)[0]=1.0;(nhat_)[1]=0.0;(nhat_)[2]=0.0; } else { \
        _ez[0]=(dV_)[0]/_g;_ez[1]=(dV_)[1]/_g;_ez[2]=(dV_)[2]/_g; \
        if(fabs(_ez[0])<0.9){_ex[0]=0.0;_ex[1]=-_ez[2];_ex[2]=_ez[1];}else{_ex[0]=-_ez[2];_ex[1]=0.0;_ex[2]=_ez[0];} \
        _s=sqrt(_ex[0]*_ex[0]+_ex[1]*_ex[1]+_ex[2]*_ex[2]);_ex[0]/=_s;_ex[1]/=_s;_ex[2]/=_s; \
        _ey[0]=_ez[1]*_ex[2]-_ez[2]*_ex[1];_ey[1]=_ez[2]*_ex[0]-_ez[0]*_ex[2];_ey[2]=_ez[0]*_ex[1]-_ez[1]*_ex[0]; \
        _s=sqrt(fmax(0.0,1.0-_mu*_mu)); \
        (nhat_)[0]=_mu*_ez[0]+_s*(cos(_phi)*_ex[0]+sin(_phi)*_ey[0]); \
        (nhat_)[1]=_mu*_ez[1]+_s*(cos(_phi)*_ex[1]+sin(_phi)*_ey[1]); \
        (nhat_)[2]=_mu*_ez[2]+_s*(cos(_phi)*_ex[2]+sin(_phi)*_ey[2]); } \
    } while(0)

#define d3_calculate_interact_kick_from_unit(dV_,mi_,mj_,nhat_,ki_,kj_) do { \
    int _k; double _mi=(mi_),_mj=(mj_),_mt=_mi+_mj; \
    double _vr=sqrt((dV_)[0]*(dV_)[0]+(dV_)[1]*(dV_)[1]+(dV_)[2]*(dV_)[2]); \
    if(_mt<=0.0){for(_k=0;_k<3;_k++){(ki_)[_k]=0.0;(kj_)[_k]=0.0;}} else { \
        for(_k=0;_k<3;_k++){double _vio=(_mj/_mt)*(dV_)[_k],_vjo=-(_mi/_mt)*(dV_)[_k]; \
            double _vin=(_mj/_mt)*_vr*(nhat_)[_k],_vjn=-(_mi/_mt)*_vr*(nhat_)[_k]; \
            (ki_)[_k]=_vin-_vio;(kj_)[_k]=_vjn-_vjo;}} \
    } while(0)

#endif
