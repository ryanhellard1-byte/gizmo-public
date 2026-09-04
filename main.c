#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <time.h>
#include <math.h>
#include <gsl/gsl_math.h>

#include "allvars.h"
#include "proto.h"
#ifdef D3_SIDMX
#include "sidm/d3_sidmx_kernel_inline.h"
#endif


/*! \file main.c
 *  \brief start of the program
 */
/*
 * This file was originally part of the GADGET3 code developed by
 * Volker Springel. The code has been modified
 * in part by Phil Hopkins (phopkins@caltech.edu) for GIZMO.
 */

#ifdef D3_SIDMX
static int d3_binary_pair_selftest_one(const char *label, int ti, int tj, double mi, double mj, double mu, double phi)
{
  double dv[3] = {400.0, -250.0, 100.0};
  double nhat[3], ki[3], kj[3], vi0[3], vj0[3], vi1[3], vj1[3];
  double mt = mi + mj, pscale = 0.0, dp2 = 0.0, kb = 0.0, ka = 0.0;
  int si = d3_species_from_type(ti), sj = d3_species_from_type(tj);
  int ch = d3_channel_from_species(si, sj), k;

  if(ch == D3_CHANNEL_NONE) return 1;
  d3_scatter_direction(dv, mu, phi, nhat);
  d3_calculate_interact_kick_from_unit(dv, mi, mj, nhat, ki, kj);

  for(k = 0; k < 3; k++)
    {
      double p0, p1;
      vi0[k] = (mj / mt) * dv[k];
      vj0[k] = -(mi / mt) * dv[k];
      vi1[k] = vi0[k] + ki[k];
      vj1[k] = vj0[k] + kj[k];
      p0 = mi * vi0[k] + mj * vj0[k];
      p1 = mi * vi1[k] + mj * vj1[k];
      dp2 += (p1 - p0) * (p1 - p0);
      pscale += p0 * p0;
      kb += 0.5 * mi * vi0[k] * vi0[k] + 0.5 * mj * vj0[k] * vj0[k];
      ka += 0.5 * mi * vi1[k] * vi1[k] + 0.5 * mj * vj1[k] * vj1[k];
    }

  {
    double rel_dp = sqrt(dp2) / fmax(1.0, sqrt(pscale));
    double rel_dk = fabs(ka - kb) / fmax(1.0e-30, fabs(kb));
    if(ThisTask == 0)
      printf("D3_BINARY_PAIR %s channel=%d rel_dP=%.17e rel_dK=%.17e\n", label, ch, rel_dp, rel_dk);
    return (rel_dp > 1.0e-12 || rel_dk > 1.0e-12);
  }
}

static int d3_binary_pair_selftest(void)
{
  int fail = 0;
  double hl0 = d3_sigma_over_meff_for_pair(3.0, 1.0, D3_SPECIES_H, D3_SPECIES_L, 0.0);
  double rhalf = d3_rutherford_sigma_total(D3_SIGMA_HL_OVER_MH, D3_W_HL_KMS, D3_W_HL_KMS);

  if(fabs(hl0 - 1.6875) > 1.0e-13) fail = 1;
  if(fabs(rhalf - 0.5625) > 1.0e-13) fail = 1;
  fail |= d3_binary_pair_selftest_one("HH", D3_TYPE_H, D3_TYPE_H, 3.0, 3.0, 0.71, 0.31);
  fail |= d3_binary_pair_selftest_one("LL", D3_TYPE_L, D3_TYPE_L, 1.0, 1.0, -0.42, 2.11);
  fail |= d3_binary_pair_selftest_one("HL", D3_TYPE_H, D3_TYPE_L, 3.0, 1.0, 0.83, 1.27);
  fail |= d3_binary_pair_selftest_one("LH", D3_TYPE_L, D3_TYPE_H, 1.0, 3.0, -0.18, 5.03);

  if(ThisTask == 0)
    printf("D3_GIZMO_BINARY_PAIR_SELFTEST: %s\n", fail ? "FAIL" : "PASS");
  return fail;
}
#endif

/*!
 *  This function initializes the MPI communication packages, and sets
 *  cpu-time counters to 0. Then begrun() is called, which sets up
 *  the simulation either from IC's or from restart files.  Finally,
 *  run() is started, the main simulation loop, which iterates over
 *  the timesteps.
 */
int main(int argc, char **argv)
{
  int i;

#ifdef IMPOSE_PINNING
  get_core_set();
#endif

  MPI_Init(&argc, &argv);
  MPI_Comm_rank(MPI_COMM_WORLD, &ThisTask);
  MPI_Comm_size(MPI_COMM_WORLD, &NTask);

#ifdef D3_SIDMX
  if(argc >= 2 && strcmp(argv[1], "--d3-pair-selftest") == 0)
    {
      int fail = d3_binary_pair_selftest();
      MPI_Finalize();
      return fail ? 1 : 0;
    }
#endif

#ifdef IMPOSE_PINNING
  pin_to_core_set();
#endif

  double safe_memorypertask = mpi_report_comittable_memory(0,1);
  MPI_Barrier(MPI_COMM_WORLD);

  /* initialize OpenMP thread pool and bind (implicitly though OpenMP runtime) */
  if(ThisTask == 0)
    {
      char *username = getenv("USER");
      char hostname[201]; hostname[200] = '\0';
      int have_hn = gethostname(hostname,200);
      time_t rawtime;
      struct tm * timeinfo;
      time ( &rawtime );
      timeinfo = localtime ( &rawtime );

      printf("\nSystem time: %s", asctime(timeinfo) );
      printf("This is GIZMO, version %d, running on %s as %s.\n",
              GIZMO_VERSION,
              have_hn == 0 ? hostname : "?",
              username ? username : "?"
      );
#ifdef BUILDINFO
      printf(BUILDINFO", " __DATE__ " " __TIME__ "\n");
#endif
      printf("\nCode was compiled with settings:\n\n");
      output_compile_time_options();
   }

#ifdef _OPENMP
#pragma omp parallel
  {
#pragma omp master
    {
      maxThreads = omp_get_num_threads();
    }
  }
#elif defined(PTHREADS_NUM_THREADS)
  if(ThisTask == 0) {printf("Using %d POSIX threads\n", maxThreads);}
#endif

  for(PTask = 0; NTask > (1 << PTask); PTask++);

  if(argc < 2)
    {
      if(ThisTask == 0)
	{
	  printf("Parameters are missing.\n");
	  printf("Call with <ParameterFile> [<RestartFlag>] [<RestartSnapNum>]\n");
	  printf("\n");
	  printf("   RestartFlag    Action\n");
	  printf("       0          Read initial conditions and start simulation\n");
	  printf("       1          Read restart files and resume simulation\n");
	  printf("       2          Restart from specified snapshot dump and continue simulation\n");
	  printf("       3          Run FOF and optionally SUBFIND if enabled\n");
	  printf("       4          Convert snapshot file to different format\n");
	  printf("       5          Calculate power spectrum and two-point function\n");
	  printf("       6          Calculate velocity power spectrum for the gas particles\n");
	  printf("\n");
	}
      endrun(0);
    }

  strcpy(ParameterFile, argv[1]);

  if(argc >= 3)
    RestartFlag = atoi(argv[2]);
  else
    RestartFlag = 0;

  if(argc >= 4)
    RestartSnapNum = atoi(argv[3]);
  else
    RestartSnapNum = -1;

  /* initialize CPU-time/Wallclock-time measurement */
  for(i = 0; i < CPU_PARTS; i++) {All.CPU_Sum[i] = CPU_Step[i] = 0;}

  CPUThisRun = 0;
  WallclockTime = my_second();

  begrun();			/* set-up run  */

  run();			/* main simulation loop */

  MPI_Finalize();		/* clean up & finalize MPI */

  return 0;
}
