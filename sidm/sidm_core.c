#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>
#include <time.h>
#include <mpi.h>
#include <gsl/gsl_math.h>
#include <gsl/gsl_integration.h>

#include "../allvars.h"
#include "../proto.h"
#include "../kernel.h"

#define GSLWORKSIZE 100000

/*! \file sidm_routines.c
 *  \brief Fuctions and routines needed for the calculations of dark matter self interactions
 *
 *  This file contains the functions and routines necesary for the computation of
 *  dark matter self interactions.
 *  Originally written by Miguel Rocha, rocham@uci.edu. Oct 2010. Updated on 2014 & re-written by PFH March 2018
 */

/*! This function calculates the interaction probability between two particles.
 *  It checks if comoving integration is on and does the necesary change of
 *  variables and units.
 */

#ifdef DM_SIDM

#include "sidmx_d3.h"

#ifdef SIDMX_D3_LIVE_AUDIT
static unsigned long long sidmx_d3_audit_pairs[3] = {0,0,0};
static unsigned long long sidmx_d3_audit_events[3] = {0,0,0};
static unsigned long long sidmx_d3_audit_pgt02[3] = {0,0,0};
static unsigned long long sidmx_d3_audit_pge1[3] = {0,0,0};
static double sidmx_d3_audit_expected[3] = {0,0,0};
static double sidmx_d3_audit_expected2[3] = {0,0,0};
static double sidmx_d3_audit_maxprob[3] = {0,0,0};
static double sidmx_d3_audit_max_momentum_residual = 0.0;
static double sidmx_d3_audit_max_energy_residual = 0.0;
static unsigned long long sidmx_d3_audit_ti = 0;
static int sidmx_d3_audit_mode = 0;
static int sidmx_d3_audit_active = 0;
static int sidmx_d3_audit_registered = 0;

static void sidmx_d3_audit_clear_block(void)
{
    int ch;
    for(ch=0;ch<3;ch++)
    {
        sidmx_d3_audit_pairs[ch]=0;
        sidmx_d3_audit_events[ch]=0;
        sidmx_d3_audit_pgt02[ch]=0;
        sidmx_d3_audit_pge1[ch]=0;
        sidmx_d3_audit_expected[ch]=0.0;
        sidmx_d3_audit_expected2[ch]=0.0;
        sidmx_d3_audit_maxprob[ch]=0.0;
    }
    sidmx_d3_audit_max_momentum_residual=0.0;
    sidmx_d3_audit_max_energy_residual=0.0;
}

static void sidmx_d3_audit_emit_block(void)
{
    if(!sidmx_d3_audit_active) return;
    printf("SIDMx-D3 AUDIT task=%d ti=%llu mode=%d "
           "pairs_HH=%llu pairs_LL=%llu pairs_HL=%llu "
           "expected_HH=%.17g expected_LL=%.17g expected_HL=%.17g "
           "expected2_HH=%.17g expected2_LL=%.17g expected2_HL=%.17g "
           "events_HH=%llu events_LL=%llu events_HL=%llu "
           "pgt02_HH=%llu pgt02_LL=%llu pgt02_HL=%llu "
           "pge1_HH=%llu pge1_LL=%llu pge1_HL=%llu "
           "maxprob_HH=%.17g maxprob_LL=%.17g maxprob_HL=%.17g "
           "max_momentum_residual=%.17g max_energy_residual=%.17g\n",
           ThisTask, sidmx_d3_audit_ti, sidmx_d3_audit_mode,
           sidmx_d3_audit_pairs[0],sidmx_d3_audit_pairs[1],sidmx_d3_audit_pairs[2],
           sidmx_d3_audit_expected[0],sidmx_d3_audit_expected[1],sidmx_d3_audit_expected[2],
           sidmx_d3_audit_expected2[0],sidmx_d3_audit_expected2[1],sidmx_d3_audit_expected2[2],
           sidmx_d3_audit_events[0],sidmx_d3_audit_events[1],sidmx_d3_audit_events[2],
           sidmx_d3_audit_pgt02[0],sidmx_d3_audit_pgt02[1],sidmx_d3_audit_pgt02[2],
           sidmx_d3_audit_pge1[0],sidmx_d3_audit_pge1[1],sidmx_d3_audit_pge1[2],
           sidmx_d3_audit_maxprob[0],sidmx_d3_audit_maxprob[1],sidmx_d3_audit_maxprob[2],
           sidmx_d3_audit_max_momentum_residual,sidmx_d3_audit_max_energy_residual);
    fflush(stdout);
}

void sidmx_d3_audit_reset(void)
{
    sidmx_d3_audit_clear_block();
    sidmx_d3_audit_active=0;
    sidmx_d3_audit_mode=0;
    sidmx_d3_audit_ti=0;
}

void sidmx_d3_audit_flush(void)
{
    sidmx_d3_audit_emit_block();
    sidmx_d3_audit_active=0;
}

void sidmx_d3_audit_probability(int mode, int ch, double prob)
{
    if(mode <= 0 || ch < 0 || ch > 2) return;
    if(!sidmx_d3_audit_active)
    {
        sidmx_d3_audit_ti=(unsigned long long)All.Ti_Current;
        sidmx_d3_audit_mode=mode;
        sidmx_d3_audit_active=1;
    }
    else if(sidmx_d3_audit_ti != (unsigned long long)All.Ti_Current || sidmx_d3_audit_mode != mode)
    {
        sidmx_d3_audit_emit_block();
        sidmx_d3_audit_clear_block();
        sidmx_d3_audit_ti=(unsigned long long)All.Ti_Current;
        sidmx_d3_audit_mode=mode;
    }
    sidmx_d3_audit_pairs[ch]++;
    sidmx_d3_audit_expected[ch]+=prob;
    sidmx_d3_audit_expected2[ch]+=prob*prob;
    if(prob > 0.2) sidmx_d3_audit_pgt02[ch]++;
    if(prob >= 1.0) sidmx_d3_audit_pge1[ch]++;
    if(prob > sidmx_d3_audit_maxprob[ch]) sidmx_d3_audit_maxprob[ch]=prob;
}

void sidmx_d3_audit_collision(int mode, int ch, const double dV[3],
                              double mass_i, double mass_j,
                              const double delta_i[3], const double delta_j[3])
{
    double pvec[3], dpost[3];
    double pnorm=0.0, pscale=0.0, pre2=0.0, post2=0.0;
    double pres, eres;
    int k;
    (void)mode;
    if(ch < 0 || ch > 2) return;
    sidmx_d3_audit_events[ch]++;
    for(k=0;k<3;k++)
    {
        pvec[k]=mass_i*delta_i[k]+mass_j*delta_j[k];
        dpost[k]=dV[k]+delta_i[k]-delta_j[k];
        pnorm+=pvec[k]*pvec[k];
        pre2+=dV[k]*dV[k];
        post2+=dpost[k]*dpost[k];
    }
    pscale=(mass_i+mass_j)*sqrt(pre2);
    pres=sqrt(pnorm)/DMAX(pscale,DBL_MIN);
    eres=fabs(post2-pre2)/DMAX(pre2,DBL_MIN);
    if(pres > sidmx_d3_audit_max_momentum_residual) sidmx_d3_audit_max_momentum_residual=pres;
    if(eres > sidmx_d3_audit_max_energy_residual) sidmx_d3_audit_max_energy_residual=eres;
}
#else
void sidmx_d3_audit_reset(void) {(void)0;}
void sidmx_d3_audit_probability(int mode, int ch, double prob) {(void)mode;(void)ch;(void)prob;}
void sidmx_d3_audit_collision(int mode, int ch, const double dV[3],
                              double mass_i, double mass_j,
                              const double delta_i[3], const double delta_j[3])
{(void)mode;(void)ch;(void)dV;(void)mass_i;(void)mass_j;(void)delta_i;(void)delta_j;}
void sidmx_d3_audit_flush(void) {(void)0;}
#endif

double prob_of_interaction(double mass, double r, double h_si, double dV[3], double dt)
{
    double dVmag = sqrt(dV[0]*dV[0]+dV[1]*dV[1]+dV[2]*dV[2]) / All.cf_atime; // velocity in physical
    double rho_eff = mass / (h_si*h_si*h_si) * All.cf_a3inv; // density in physical
    double cx_eff = All.DM_InteractionCrossSection * g_geo(r/h_si); // effective cross section (physical) scaled to cgs
    double units = UNIT_SURFDEN_IN_CGS; // needed to convert everything to cgs
    if(All.DM_InteractionVelocityScale>0) {double x=dVmag/All.DM_InteractionVelocityScale; cx_eff/=1+x*x*x*x;} // take velocity dependence
    return rho_eff * cx_eff * dVmag * dt * units; // dimensionless probability
}

/*! This routine sets the kicks for each particle after it has been decided that they will
 *  interact. It uses an algorithm tha conserves energy and momentum but picks a random direction so it does not conserves angular momentum. */
#if !defined(GRAIN_COLLISIONS) /* if using the 'grain collisions' module, these functions will be defined elsewhere [in the grains subroutines] */
void calculate_interact_kick(double dV[3], double kick[3], double m)
{
    double dVmag = (1-All.DM_DissipationFactor)*sqrt(dV[0]*dV[0]+dV[1]*dV[1]+dV[2]*dV[2]);
    if(dVmag<0) {dVmag=0;}
    if(All.DM_KickPerCollision>0) {double v0=All.DM_KickPerCollision; dVmag=sqrt(dVmag*dVmag+v0*v0);}
    double cos_theta = 2.0*gsl_rng_uniform(random_generator)-1.0, sin_theta = sqrt(1.-cos_theta*cos_theta), phi = gsl_rng_uniform(random_generator)*2.0*M_PI;
    kick[0] = 0.5*(dV[0] + dVmag*sin_theta*cos(phi));
    kick[1] = 0.5*(dV[1] + dVmag*sin_theta*sin(phi));
    kick[2] = 0.5*(dV[2] + dVmag*cos_theta);
}
#endif


/*! This function returns the value of the geometrical factor needed for the calculation of the interaction probability. */
double g_geo(double r)
{
    double f, u; int i; u = r / 2.0 * GEOFACTOR_TABLE_LENGTH; i = (int) u;
    if(i >= GEOFACTOR_TABLE_LENGTH) {i = GEOFACTOR_TABLE_LENGTH - 1;}
    if(i <= 1) {f = 0.992318  + (GeoFactorTable[0] - 0.992318)*u;} else {f = GeoFactorTable[i - 1] + (GeoFactorTable[i] - GeoFactorTable[i - 1]) * (u - i);}
    return f;
}

/*! This routine initializes the table that will be used to get the geometrical factor
 *  as a function of the two particle separations. It populates the table with the results of the numerical integration */
void init_geofactor_table(void)
{
    int i; double result, abserr,r;
    gsl_function F; gsl_integration_workspace *workspace = gsl_integration_workspace_alloc(GSLWORKSIZE);
    for(i = 0; i < GEOFACTOR_TABLE_LENGTH; i++)
    {
        r =  2.0/GEOFACTOR_TABLE_LENGTH * (i + 1);
        F.function = &geofactor_integ;
        F.params = &r;
        gsl_integration_qag(&F, 0.0, 1.0, 0, 1.0e-8, GSLWORKSIZE, GSL_INTEG_GAUSS41,workspace, &result, &abserr);
        GeoFactorTable[i] = 2*M_PI*result;
    }
    gsl_integration_workspace_free(workspace);
}

/*! This function returns the integrand of the numerical integration done on init_geofactor_table(). */
double geofactor_integ(double x, void * params)
{
    double result, abserr, r, newparams[2];
    r = *(double *) params; newparams[0] = r; newparams[1] = x;
    gsl_function F; gsl_integration_workspace *workspace = gsl_integration_workspace_alloc(GSLWORKSIZE);
    F.function = &geofactor_angle_integ; F.params = newparams;
    
    gsl_integration_qag(&F, -1.0, 1.0, 0, 1.0e-8, GSLWORKSIZE, GSL_INTEG_GAUSS41,workspace, &result, &abserr);
    gsl_integration_workspace_free(workspace);
    
    /*! This function returns the value W(x). The values of the density kernel as a funtion of x=r/h */
    double wk=0; if(x<1) kernel_main(x, 1, 1, &wk, &wk, -1);
    return x*x*wk*result;
}

/*! This function returns the integrand of the angular part of the integral done on init_geofactor_table(). */
double geofactor_angle_integ(double u, void * params)
{
    double x,r,f;
    r = *(double *) params;
    x = *(double *) (params + sizeof(double));
    f = sqrt(x*x + r*r + 2*x*r*u);
    double wk=0; if(f<1) kernel_main(f, 1, 1, &wk, &wk, -1); /*! This function returns the value W(x). The values of the density kernel as a funtion of x=r/h */
    return wk;
}

/*! Initialize SIDM bookkeeping and fail closed on the frozen D3 species contract. */
void init_self_interactions()
{
    int i;
    for(i = 0; i < NumPart; i++) {P[i].dtime_sidm = 0; P[i].NInteractions = 0;}

#ifndef GRAIN_COLLISIONS
    {
        const int mode = sidmx_d3_runtime_mode();
        if(mode > 0)
        {
            double local_min[2] = {DBL_MAX, DBL_MAX};
            double local_max[2] = {0.0, 0.0};
            double global_min[2], global_max[2];
            long long local_count[2] = {0, 0};
            long long global_count[2] = {0, 0};
            double ratio;

            /* Ntype[] is not yet populated at this point in init(), so audit
             * the loaded particle array directly and reduce across MPI tasks. */
            for(i = 0; i < NumPart; i++)
            {
                int s = -1;
                if(P[i].Type == 1) s = 0;
                if(P[i].Type == 2) s = 1;
                if(s >= 0)
                {
                    local_count[s]++;
                    if(P[i].Mass < local_min[s]) local_min[s] = P[i].Mass;
                    if(P[i].Mass > local_max[s]) local_max[s] = P[i].Mass;
                }
            }

            MPI_Allreduce(local_count, global_count, 2, MPI_LONG_LONG, MPI_SUM, MPI_COMM_WORLD);
            MPI_Allreduce(local_min, global_min, 2, MPI_DOUBLE, MPI_MIN, MPI_COMM_WORLD);
            MPI_Allreduce(local_max, global_max, 2, MPI_DOUBLE, MPI_MAX, MPI_COMM_WORLD);

            if(global_count[0] <= 0 || global_count[1] <= 0 || global_count[0] != global_count[1])
            {
                if(ThisTask == 0)
                    fprintf(stderr, "SIDMx-D3: fatal species counts N_H=%lld N_L=%lld; required N_H=N_L>0\n",
                            global_count[0], global_count[1]);
                endrun(171205);
            }
            if(global_min[0] <= 0.0 || global_min[1] <= 0.0 ||
               fabs(global_max[0]-global_min[0]) > 1.0e-10*fabs(global_max[0]) ||
               fabs(global_max[1]-global_min[1]) > 1.0e-10*fabs(global_max[1]))
            {
                if(ThisTask == 0)
                    fprintf(stderr, "SIDMx-D3: fatal non-uniform species masses H=[%.17g,%.17g] L=[%.17g,%.17g]\n",
                            global_min[0], global_max[0], global_min[1], global_max[1]);
                endrun(171206);
            }

            ratio = global_min[0] / global_min[1];
            if(mode == 10)
            {
                if(fabs(ratio - 1.0) > 1.0e-8)
                {
                    if(ThisTask == 0)
                        fprintf(stderr, "SIDMx-D3: fatal equal-label control H/L macro-mass ratio %.17g; required 1\n", ratio);
                    endrun(171209);
                }
            }
            else if(fabs(ratio - 3.0) > 3.0e-8)
            {
                if(ThisTask == 0)
                    fprintf(stderr, "SIDMx-D3: fatal H/L macro-mass ratio %.17g; required 3\n", ratio);
                endrun(171207);
            }

            /* GIZMO's domain allocator normally starts TopNodeAllocFactor at
             * 0.008 and grows it only when domain_decompose() explicitly
             * requests a retry.  force_create_empty_nodes() also compares its
             * complete-octree node count against that temporary domain capacity.
             * Sparse two-species commissioning ICs can therefore hit the stale
             * MaxTopNodes ceiling on a later rebuild even with ample MaxNodes.
             * 0.1 is already used upstream for extreme dynamic-range startup;
             * this is memory headroom only and changes no force/SIDM physics. */
            if(All.TopNodeAllocFactor < 0.1) All.TopNodeAllocFactor = 0.1;

#ifdef SIDMX_D3_LIVE_AUDIT
            sidmx_d3_audit_reset();
            if(!sidmx_d3_audit_registered)
            {
                atexit(sidmx_d3_audit_flush);
                sidmx_d3_audit_registered=1;
            }
#endif

            if(ThisTask == 0)
            {
                printf("SIDMx-D3 init PASS: mode=%d N_H=%lld N_L=%lld mH/mL=%.17g\n",
                       mode, global_count[0], global_count[1], ratio);
                printf("SIDMx-D3 allocator guard: TopNodeAllocFactor=%.17g\n", All.TopNodeAllocFactor);
            }
        }
    }
#endif
}

/* D3 / SIDMx two-component extension.  Kept in the existing SIDM object so
 * the upstream Makefile and MPI/AGS call graph remain untouched. */
#include "sidmx_d3_impl.h"

#endif
