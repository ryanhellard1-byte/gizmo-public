#ifndef D3_SIDMX_KERNEL_H
#define D3_SIDMX_KERNEL_H

#ifdef __cplusplus
extern "C" {
#endif

#ifndef D3_SIDMX_H_TYPE
#define D3_SIDMX_H_TYPE 1
#endif

#ifndef D3_SIDMX_L_TYPE
#define D3_SIDMX_L_TYPE 2
#endif

#ifndef D3_SIDMX_CHANNEL_MASK
#define D3_SIDMX_CHANNEL_MASK 7
#endif

enum d3_sidmx_channel {
    D3_CH_NONE = 0,
    D3_CH_HH = 1,
    D3_CH_LL = 2,
    D3_CH_HL = 4
};

int d3_sidmx_channel_from_types(int type_i, int type_j);
int d3_sidmx_channel_enabled(int channel);
const char *d3_sidmx_channel_name(int channel);

double d3_sidmx_differential_xsec_per_mass(int channel, double mu, double v_km_s, int basis_type);
double d3_sidmx_total_xsec_per_mass(int channel, double v_km_s, int basis_type);
double d3_sidmx_sample_mu(int channel, double v_km_s, double u);
void d3_sidmx_make_kick(const double dV[3], int channel, double v_km_s,
                        double u_mu, double u_phi, double kick[3]);

#ifdef __cplusplus
}
#endif

#endif
