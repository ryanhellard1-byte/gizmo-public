#!/usr/bin/env python3
import numpy as np, h5py, sys, math

out=sys.argv[1] if len(sys.argv)>1 else 'phase178_box.hdf5'
N1=int(sys.argv[2]) if len(sys.argv)>2 else 4096
N2=N1
L=100.0
mL=1.0
mH=3.0*mL
vrel=100.0
rng=np.random.default_rng(17820260903)

with h5py.File(out,'w') as f:
    npart=np.array([0,N1,N2,0,0,0],dtype=np.uint32)
    h=f.create_group('Header')
    h.attrs['NumPart_ThisFile']=npart
    h.attrs['NumPart_Total']=npart
    h.attrs['NumPart_Total_HighWord']=np.zeros(6,dtype=np.uint32)
    h.attrs['MassTable']=np.zeros(6,dtype=np.float64)
    h.attrs['Time']=0.0
    h.attrs['Redshift']=0.0
    h.attrs['BoxSize']=L
    h.attrs['NumFilesPerSnapshot']=1
    h.attrs['Omega0']=0.0; h.attrs['OmegaLambda']=0.0; h.attrs['HubbleParam']=1.0
    h.attrs['Flag_Sfr']=0; h.attrs['Flag_Cooling']=0; h.attrs['Flag_StellarAge']=0
    h.attrs['Flag_Metals']=0; h.attrs['Flag_Feedback']=0; h.attrs['Flag_DoublePrecision']=1
    nextid=1
    for typ,N,mass,vx in [(1,N1,mH,+0.5*vrel),(2,N2,mL,-0.5*vrel)]:
        g=f.create_group(f'PartType{typ}')
        g.create_dataset('Coordinates',data=rng.uniform(0,L,(N,3)))
        v=np.zeros((N,3)); v[:,0]=vx
        g.create_dataset('Velocities',data=v)
        g.create_dataset('ParticleIDs',data=np.arange(nextid,nextid+N,dtype=np.uint64)); nextid+=N
        g.create_dataset('Masses',data=np.full(N,mass))

# Analytic first-order HL expectation for the commissioning interval used by CI.
# Code units in the workflow: 1 length = 1 kpc, 1 mass = 1e10 Msun, 1 velocity = 1 km/s.
kpc=3.085678e21; msun=1.989e33
rhoH=(N1*mH/L**3)*(1.0e10*msun)/(kpc**3)
sigmaHL=1.125/(1.0+(vrel/2200.0)**2)
tsec=0.02*kpc/1.0e5
pL=rhoH*sigmaHL*(vrel*1.0e5)*tsec
expected=N2*pL
print(f'wrote {out}: N_H=N_L={N1}, mH/mL={mH/mL}, vrel={vrel} km/s, box={L}')
print(f'first_order_HL_expectation={expected:.6f} collisions; per_L_over_run={pL:.9f}; per_step_approx={pL/100:.9g}')
