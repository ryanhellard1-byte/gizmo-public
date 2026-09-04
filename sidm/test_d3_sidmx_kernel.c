/*
 * Standalone smoke test for the first-pass D3/SIDMx kernel scaffold.
 *
 * This intentionally stubs the tiny subset of GIZMO globals/functions needed by
 * d3_sidmx_kernel_inline.h so GitHub Actions can verify that the guarded D3
 * routing/probability/kick helper compiles and conserves pair momentum/energy.
 *
 * It is not a full GIZMO integration test and does not claim production physics.
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define UNIT_SURFDEN_IN_CGS 1.0

struct global_data_all_processes
{
    double cf_atime;
    double cf_a3inv;
} All = {1.0, 1.0};

double g_geo(double r)
{
    (void)r;
    return 1.0;
}

#include "d3_sidmx_kernel_inline.h"

static double kinetic_energy(double m, const double v[3])
{
    return 0.5 * m * (v[0]*v[0] + v[1]*v[1] + v[2]*v[2]);
}

static double norm3(const double x[3])
{
    return sqrt(x[0]*x[0] + x[1]*x[1] + x[2]*x[2]);
}

static int test_pair(const char *label, int type_i, int type_j, double mi, double mj)
{
    const double nhat[3] = {0.0, 1.0, 0.0};
    double dv[3] = {0.40, -0.25, 0.10};
    double kick_i[3], kick_j[3];
    double pi_before[3], pi_after[3], dp[3];
    double vi_before[3], vj_before[3], vi_after[3], vj_after[3];
    double mtot = mi + mj;
    int si = d3_species_from_type(type_i);
    int sj = d3_species_from_type(type_j);
    int ch = d3_channel_from_species(si, sj);
    double prob = d3_prob_of_interaction(mi, mj, 0.10, 1.0, dv, 0.01, si, sj);

    if(si == D3_SPECIES_NONE || sj == D3_SPECIES_NONE || ch == D3_CHANNEL_NONE)
    {
        fprintf(stderr, "%s bad route si=%d sj=%d ch=%d\n", label, si, sj, ch);
        return 1;
    }
    if(!(prob > 0.0) || !isfinite(prob))
    {
        fprintf(stderr, "%s bad probability %.17e\n", label, prob);
        return 1;
    }

    for(int k=0;k<3;k++)
    {
        vi_before[k] = (mj/mtot) * dv[k];
        vj_before[k] = -(mi/mtot) * dv[k];
        pi_before[k] = mi*vi_before[k] + mj*vj_before[k];
    }

    d3_calculate_interact_kick_from_unit(dv, mi, mj, (double *)nhat, kick_i, kick_j);

    for(int k=0;k<3;k++)
    {
        vi_after[k] = vi_before[k] + kick_i[k];
        vj_after[k] = vj_before[k] + kick_j[k];
        pi_after[k] = mi*vi_after[k] + mj*vj_after[k];
        dp[k] = pi_after[k] - pi_before[k];
    }

    double k_before = kinetic_energy(mi, vi_before) + kinetic_energy(mj, vj_before);
    double k_after = kinetic_energy(mi, vi_after) + kinetic_energy(mj, vj_after);
    double rel_dp = norm3(dp) / fmax(1.0, norm3(pi_before));
    double rel_dk = fabs(k_after - k_before) / fmax(1.0e-30, fabs(k_before));

    printf("%s channel=%d prob=%.17e rel_dP=%.17e rel_dK=%.17e\n", label, ch, prob, rel_dp, rel_dk);

    if(rel_dp > 1.0e-12 || rel_dk > 1.0e-12)
    {
        fprintf(stderr, "%s conservation fail rel_dP=%.17e rel_dK=%.17e\n", label, rel_dp, rel_dk);
        return 1;
    }
    return 0;
}

int main(void)
{
    int fail = 0;
    fail |= test_pair("HH", D3_TYPE_H, D3_TYPE_H, 3.0, 3.0);
    fail |= test_pair("LL", D3_TYPE_L, D3_TYPE_L, 1.0, 1.0);
    fail |= test_pair("HL", D3_TYPE_H, D3_TYPE_L, 3.0, 1.0);
    fail |= test_pair("LH", D3_TYPE_L, D3_TYPE_H, 1.0, 3.0);

    if(fail)
    {
        puts("D3_SIDMX_SMOKE: FAIL");
        return 1;
    }
    puts("D3_SIDMX_SMOKE: PASS");
    return 0;
}
