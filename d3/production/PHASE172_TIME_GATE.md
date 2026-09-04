# Phase 172 time gate

The production campaign is not complete at 10 Gyr.

Every frozen Phase-172 run requires the analysis schedule:

`0, 0.25, 0.5, 1, 2, 5, 10, 20, 40, 55.28, 80 Gyr`.

A production output is structurally acceptable only if:

1. the manifest SHA-256 is exactly `e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d`;
2. every manifest row carries the exact frozen analysis schedule above;
3. every `run_summary.csv` row is `COMPLETE` and `final_time_Gyr >= 80`;
4. `profiles.csv` contains H, L, and total profiles at every frozen analysis time for every run, including 55.28 and 80 Gyr;
5. `collision_log_summary.csv` represents every manifest run.

The 10 Gyr values remain required intermediate diagnostics. They are not a substitute for completion of the 80 Gyr campaign.

This gate is an execution/output contract only. Passing it does not establish the D3/SIDMx physical claim.
