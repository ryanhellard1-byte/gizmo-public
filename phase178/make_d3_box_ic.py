#!/usr/bin/env python3
import numpy as np, h5py, sys

out=sys.argv[1] if len(sys.argv)>1 else 'phase178_box.hdf5'
N1=int(sys.argv[2]) if len(sys.argv)>2 else 4096
N2=N1
L=100.0
mL=1.0e-6
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
print(f'wrote {out}: N_H=N_L={N1}, mH/mL={mH/mL}, vrel={vrel} km/s, box={L}')
