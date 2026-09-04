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
        double d3_prob = 0.0;
        int species_i = 0, species_j = 0, d3_channel = 0;
        if(local.Type == 2) {species_i = 1;} else if(local.Type == 3) {species_i = 2;}
        if(P[j].Type == 2) {species_j = 1;} else if(P[j].Type == 3) {species_j = 2;}
        if(species_i == 1 && species_j == 1) {d3_channel = 1;} /* HH */
        if(species_i == 2 && species_j == 2) {d3_channel = 2;} /* LL */
        if(((species_i == 1) && (species_j == 2)) || ((species_i == 2) && (species_j == 1))) {d3_channel = 3;} /* HL/LH */
        if((d3_channel > 0) && (h_si > 0.0) && (local.dtime > 0.0))
        {
            double d3_dVmag = sqrt(kernel.dv[0]*kernel.dv[0] + kernel.dv[1]*kernel.dv[1] + kernel.dv[2]*kernel.dv[2]) / All.cf_atime;
            double d3_sigma_over_mass = 0.0, d3_w = 1.0e30;
            if(d3_channel == 1) {d3_sigma_over_mass = 6.89; d3_w = 275.0;} /* HH */
            if(d3_channel == 2) {d3_sigma_over_mass = 2.2966666667; d3_w = 825.0;} /* LL */
            if(d3_channel == 3) {d3_sigma_over_mass = 0.5*(1.125 + 3.375); d3_w = 2200.0;} /* HL pair-level mean */
            double d3_x = d3_dVmag / d3_w;
            double d3_vsup = 1.0 / (1.0 + d3_x*d3_x*d3_x*d3_x);
            double d3_rho_eff = (0.5 * (local.Mass + P[j].Mass)) / (h_si*h_si*h_si) * All.cf_a3inv;
            double d3_cx_eff = d3_sigma_over_mass * d3_vsup * g_geo(kernel.r/h_si);
            d3_prob = d3_rho_eff * d3_cx_eff * d3_dVmag * local.dtime * UNIT_SURFDEN_IN_CGS;
        }
        double prob = d3_prob;
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
            double mtot = local.Mass + P[j].Mass;
            double vrel_mag = sqrt(kernel.dv[0]*kernel.dv[0] + kernel.dv[1]*kernel.dv[1] + kernel.dv[2]*kernel.dv[2]);
            int k; for(k=0;k<3;k++) {
                double vi_old = (P[j].Mass/mtot) * kernel.dv[k];
                double vj_old = -(local.Mass/mtot) * kernel.dv[k];
                double vi_new = (P[j].Mass/mtot) * vrel_mag * nhat[k];
                double vj_new = -(local.Mass/mtot) * vrel_mag * nhat[k];
                double kick_i = vi_new - vi_old;
                double kick_j = vj_new - vj_old;
                out.sidm_kick[k] += kick_i;
                #pragma omp atomic
                P[j].Vel[k] += kick_j; // this variable is modified here so need to do this carefully here to ensure we don't multiply-write at the same time
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
