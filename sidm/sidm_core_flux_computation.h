/* here is where we call the core of the SIDM calculation for DM particle-particle interactions */
#ifdef DM_SIDM
{
    double Pj_dtime = GET_PARTICLE_TIMESTEP_IN_PHYSICAL(j);
    if( ((1 << local.Type) & (DM_SIDM)) && ((1 << P[j].Type) & (DM_SIDM)) && (local.ID != P[j].ID) && (local.dtime <= Pj_dtime))
    {
        if((local.dtime==Pj_dtime) && (local.ID > P[j].ID)) continue;
        double h_si = 0.5*(kernel.h_i + kernel.h_j), m_si = 0.5*(local.Mass + P[j].Mass);
#ifdef GRAIN_COLLISIONS
        double prob = prob_of_grain_interaction(local.Grain_CrossSection_PerUnitMass , local.Mass, kernel.r, h_si, kernel.dv, local.dtime, j);
#else
#ifdef D3_SIDMX
#include "d3_sidmx_kernel_inline.h"
        int species_i=d3_species_from_type(local.Type), species_j=d3_species_from_type(P[j].Type);
        int d3_channel=d3_channel_from_species(species_i,species_j);
        double prob=d3_prob_of_interaction(local.Mass,P[j].Mass,kernel.r,h_si,kernel.dv,local.dtime,species_i,species_j);
#else
        double prob = prob_of_interaction(m_si, kernel.r, h_si, kernel.dv, local.dtime);
#endif
#endif
        if(prob > 0.2) {out.dtime_sidm = DMIN(out.dtime_sidm , local.dtime*(0.2/prob));}
        if (gsl_rng_uniform(random_generator) < prob)
        {
#ifdef WAKEUP
            if(!(TimeBinActive[P[j].TimeBin])) {if(WAKEUP*local.dtime < Pj_dtime) {
                #pragma omp atomic write
                PPPZ[j].wakeup=1;
                #pragma omp atomic write
                NeedToWakeupParticles_local = 1;
            }}
#endif
#ifdef D3_SIDMX
            double vphys=sqrt(kernel.dv[0]*kernel.dv[0]+kernel.dv[1]*kernel.dv[1]+kernel.dv[2]*kernel.dv[2])/All.cf_atime;
            double mu=1.0, phi=2.0*M_PI*gsl_rng_uniform(random_generator), nhat[3];
            if(d3_channel==D3_CHANNEL_HL)
            {
                mu=d3_rutherford_mu_from_u(vphys,D3_W_HL_KMS,gsl_rng_uniform(random_generator));
            }
            else if(d3_channel==D3_CHANNEL_HH || d3_channel==D3_CHANNEL_LL)
            {
                double sigma0=(d3_channel==D3_CHANNEL_HH)?D3_SIGMA_HH_OVER_MH:D3_SIGMA_LL_OVER_ML;
                double w=(d3_channel==D3_CHANNEL_HH)?D3_W_HH_KMS:D3_W_LL_KMS;
                double fmax_d3=d3_moller_dsigma_max(sigma0,vphys,w), ftry;
                do {
                    mu=2.0*gsl_rng_uniform(random_generator)-1.0;
                    ftry=d3_moller_dsigma_dmu(sigma0,vphys,w,mu);
                } while(gsl_rng_uniform(random_generator)*fmax_d3 > ftry);
            }
            d3_scatter_direction(kernel.dv,mu,phi,nhat);
            {
                double kick_i[3],kick_j[3]; int k;
                d3_calculate_interact_kick_from_unit(kernel.dv,local.Mass,P[j].Mass,nhat,kick_i,kick_j);
                for(k=0;k<3;k++) {
                    out.sidm_kick[k] += kick_i[k];
                    #pragma omp atomic
                    P[j].Vel[k] += kick_j[k];
                }
            }
#else
            double kick[3]; calculate_interact_kick(kernel.dv, kick, m_si);
            int k; for(k=0;k<3;k++) {
                out.sidm_kick[k] -= (P[j].Mass/m_si)*kick[k];
                #pragma omp atomic
                P[j].Vel[k] += (local.Mass/m_si)*kick[k];
            }
#endif
            out.si_count++;
            #pragma omp atomic
            P[j].NInteractions++;
        }
    }
}
#endif
