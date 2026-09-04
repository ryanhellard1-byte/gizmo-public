/* here is where we call the core of the SIDM calculation for DM particle-particle interactions */
#ifdef DM_SIDM
#include "sidmx_d3.h"
{
    /* check if target+neighbor are an SIDM candidate, and against self-interaction */
    double Pj_dtime = GET_PARTICLE_TIMESTEP_IN_PHYSICAL(j);
    if( ((1 << local.Type) & (DM_SIDM)) && ((1 << P[j].Type) & (DM_SIDM)) && (local.ID != P[j].ID) && (local.dtime <= Pj_dtime))
    {
        if((local.dtime==Pj_dtime) && (local.ID > P[j].ID)) continue; // ensures interaction will only be calculated once for each pair //
        double h_si = 0.5*(kernel.h_i + kernel.h_j), m_si = 0.5*(local.Mass + P[j].Mass);
        double prob = 0.0;
        int d3_mode = 0, d3_channel = -1;
#ifdef GRAIN_COLLISIONS
        prob = prob_of_grain_interaction(local.Grain_CrossSection_PerUnitMass , local.Mass, kernel.r, h_si, kernel.dv, local.dtime, j);
#else
        d3_mode = sidmx_d3_runtime_mode();
        if(d3_mode > 0)
        {
            d3_channel = sidmx_d3_channel(local.Type,P[j].Type);
            if(d3_channel >= 0)
            {
                prob = sidmx_d3_probability(d3_mode,d3_channel,local.Type,P[j].Type,
                                             local.Mass,P[j].Mass,kernel.r,h_si,kernel.dv,local.dtime);
                sidmx_d3_audit_probability(d3_mode,d3_channel,prob);
            }
        }
        else
        {
            prob = prob_of_interaction(m_si, kernel.r, h_si, kernel.dv, local.dtime);
        }
#endif
        if(prob > 0.2) {out.dtime_sidm = DMIN(out.dtime_sidm , local.dtime*(0.2/prob));} // timestep condition not being met as desired, warn code to lower timestep next turn //
#ifndef GRAIN_COLLISIONS
        if(d3_mode > 0 && prob > 1.0)
        {
            if(ThisTask == 0) fprintf(stderr,"SIDMx-D3: fatal pair probability %g > 1 at integer time %llu\n",prob,(unsigned long long)All.Ti_Current);
            endrun(171204);
        }
#endif
        {
            double sidmx_accept_draw;
#ifndef GRAIN_COLLISIONS
            if(d3_mode > 0)
                sidmx_accept_draw = sidmx_d3_pair_uniform((unsigned long long)local.ID,(unsigned long long)P[j].ID,
                                                           (unsigned long long)All.Ti_Current,d3_mode,0);
            else
#endif
                sidmx_accept_draw = gsl_rng_uniform(random_generator);

            if (sidmx_accept_draw < prob)
            {
#ifdef WAKEUP
                if(!(TimeBinActive[P[j].TimeBin])) {if(WAKEUP*local.dtime < Pj_dtime) {
                    #pragma omp atomic write
                    PPPZ[j].wakeup=1;
                    #pragma omp atomic write
                    NeedToWakeupParticles_local = 1;
                }}
#endif
#ifndef GRAIN_COLLISIONS
                if(d3_mode > 0)
                {
                    double delta_i[3], delta_j[3];
                    double u_mu = sidmx_d3_pair_uniform((unsigned long long)local.ID,(unsigned long long)P[j].ID,
                                                        (unsigned long long)All.Ti_Current,d3_mode,1);
                    double u_phi = sidmx_d3_pair_uniform((unsigned long long)local.ID,(unsigned long long)P[j].ID,
                                                         (unsigned long long)All.Ti_Current,d3_mode,2);
                    sidmx_d3_scatter_deltas(d3_mode,d3_channel,kernel.dv,local.Mass,P[j].Mass,u_mu,u_phi,delta_i,delta_j);
                    sidmx_d3_audit_collision(d3_mode,d3_channel,kernel.dv,local.Mass,P[j].Mass,delta_i,delta_j);
                    int k; for(k=0;k<3;k++) {
                        out.sidm_kick[k] += delta_i[k];
                        /* Keep the local working velocity synchronized so another
                         * accepted collision in this neighbor walk sees the updated
                         * state, not the pre-collision velocity. */
                        local.Vel[k] += delta_i[k];
                        #pragma omp atomic
                        P[j].Vel[k] += delta_j[k];
                    }
                }
                else
#endif
                {
                    double kick[3]; calculate_interact_kick(kernel.dv, kick, m_si);
                    int k; for(k=0;k<3;k++) {
                        const double delta_i = -(P[j].Mass/m_si)*kick[k];
                        out.sidm_kick[k] += delta_i;
                        /* Match the D3 branch: the deferred target kick also has
                         * to update the local working velocity before the next
                         * neighbor is evaluated. */
                        local.Vel[k] += delta_i;
                        #pragma omp atomic
                        P[j].Vel[k] += (local.Mass/m_si)*kick[k]; // this variable is modified here so need to do this carefully here to ensure we don't multiply-write at the same time
                    }
                }
                out.si_count++;
                #pragma omp atomic
                P[j].NInteractions++;
            }
        }
    } // if((1 << ptype) & (DM_SIDM))
}
#endif
