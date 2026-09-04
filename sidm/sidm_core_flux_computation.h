/* here is where we call the core of the SIDM calculation for DM particle-particle interactions */
#ifdef DM_SIDM
{
    /* check if target+neighbor are an SIDM candidate, and against self-interaction */
    double Pj_dtime = GET_PARTICLE_TIMESTEP_IN_PHYSICAL(j);
    if( ((1 << local.Type) & (DM_SIDM)) && ((1 << P[j].Type) & (DM_SIDM)) && (local.ID != P[j].ID) && (local.dtime <= Pj_dtime))
    {
        if((local.dtime==Pj_dtime) && (local.ID > P[j].ID)) continue; // ensures interaction will only be calculated once for each pair //
        double h_si = 0.5*(kernel.h_i + kernel.h_j), m_si = 0.5*(local.Mass + P[j].Mass);
#ifdef GRAIN_COLLISIONS
        double prob = prob_of_grain_interaction(local.Grain_CrossSection_PerUnitMass , local.Mass, kernel.r, h_si, kernel.dv, local.dtime, j);
#else
#ifdef D3_SIDMX
        int species_i = d3_species_from_type(local.Type);
        int species_j = d3_species_from_type(P[j].Type);
        if(species_i == D3_SPECIES_NONE || species_j == D3_SPECIES_NONE) continue;
        double prob = d3_prob_of_interaction(local.Mass, P[j].Mass, kernel.r, h_si, kernel.dv, local.dtime, species_i, species_j);
#else
        double prob = prob_of_interaction(m_si, kernel.r, h_si, kernel.dv, local.dtime);
#endif
#endif
        if(prob > 0.2) {out.dtime_sidm = DMIN(out.dtime_sidm , local.dtime*(0.2/prob));} // timestep condition not being met as desired, warn code to lower timestep next turn //
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
            double cos_theta = 2.0*gsl_rng_uniform(random_generator)-1.0;
            double sin_theta = sqrt(1.-cos_theta*cos_theta);
            double phi = gsl_rng_uniform(random_generator)*2.0*M_PI;
            double nhat[3];
            nhat[0] = sin_theta*cos(phi);
            nhat[1] = sin_theta*sin(phi);
            nhat[2] = cos_theta;
            double kick_i[3], kick_j[3];
            d3_calculate_interact_kick_from_unit(kernel.dv, local.Mass, P[j].Mass, nhat, kick_i, kick_j);
            int k; for(k=0;k<3;k++) {
                out.sidm_kick[k] += kick_i[k];
                #pragma omp atomic
                P[j].Vel[k] += kick_j[k]; // this variable is modified here so need to do this carefully here to ensure we don't multiply-write at the same time
            }
#else
            double kick[3]; calculate_interact_kick(kernel.dv, kick, m_si);
            int k; for(k=0;k<3;k++) {
                out.sidm_kick[k] -= (P[j].Mass/m_si)*kick[k];
                #pragma omp atomic
                P[j].Vel[k] += (local.Mass/m_si)*kick[k]; // this variable is modified here so need to do this carefully here to ensure we don't multiply-write at the same time
            }
#endif
            out.si_count++;
            #pragma omp atomic
            P[j].NInteractions++;
        }
    } // if((1 << ptype) & (DM_SIDM))
}
#endif
