# Gaussian linear-bath nonlinearity no-go theorem

## Statement

A Gaussian continuum bath of harmonic auxiliary degrees of freedom, coupled linearly to a system variable, cannot by itself generate the amplitude-nonlinear isolated Hellard modified-inertia law

    a mu(a/a_H) = g_N

with nonconstant mu.

## Proof sketch

Let the parent action be quadratic in bath variables X_lambda and linear in the system history q:

    S = S_sys[q]
        + 1/2 \int d lambda X_lambda D_lambda X_lambda
        + \int d lambda q C_lambda X_lambda.

The bath Euler-Lagrange equations are linear:

    D_lambda X_lambda = - C_lambda q.

With retarded boundary conditions,

    X_lambda = - D_lambda,ret^{-1} C_lambda q.

Substitution back into the effective equation for q produces a term of the form

    \int dt' K_ret(t,t') q(t'),

where K_ret is determined by the bath spectral density and propagators. This contribution is linear in q because both the bath equations and the system-bath coupling are linear.

Equivalently, Gaussian functional integration generates an effective influence functional quadratic in q. Its first functional derivative is therefore linear in q.

The isolated Hellard law requires an amplitude-dependent inertial response through

    mu(a/a_H) = (a/a_H)/sqrt(1+(a/a_H)^2),

which is nonlinear in acceleration amplitude. Therefore it cannot arise solely from integrating out a Gaussian harmonic bath with linear system-bath coupling.

## Consequence

A conservative microscopic parent for the Hellard candidate must contain at least one of:

1. nonlinear system-bath coupling;
2. interacting/non-Gaussian bath degrees of freedom;
3. a nonlinear constraint or collective order parameter before bath elimination;
4. an in-in/doubled-history effective action whose nonlinear response comes from a non-Gaussian parent sector.

The theorem does not rule out scale-invariant continuum baths. It rules out the simplest Gaussian + linear-coupling realization as the source of the MOND-like amplitude nonlinearity.
