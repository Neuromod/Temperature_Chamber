import copy
import numpy
import scipy.optimize as optimize
import matplotlib.pyplot as pyplot


# Steinhart-Hart: Ohm -> Kelvin
def temperature(coeff, r):
    a = coeff[0]
    b = coeff[1]
    c = coeff[2]
    logR = numpy.log(r)
    
    return 1. / (a + b * logR + c * (logR ** 3.))


# Steinhart-Hart: Kelvin -> Ohm
def resistance(coeff, t, x0 = 50 + 273.15):
    if isinstance(t, (list, numpy.ndarray)):
        r = numpy.zeros(len(t))
        for i in range(len(t)):
            f = lambda r : temperature(coeff, r) - t[i]
            r[i] = optimize.fsolve(f, x0 = x0)[0]
    else:
        f = lambda r : temperature(coeff, r) - t
        r = optimize.fsolve(f, x0 = x0)[0]
            
    return r


# Steinhart-Hart coefficient solver (Ohm, Kelvin)
def coefficients(r, t):
    logR = numpy.log(r)
    a = numpy.column_stack((numpy.ones(len(r)), logR, logR ** 3.))
    b = 1 / t
    
    return numpy.matmul(numpy.linalg.inv(numpy.matmul(a.T, a)), numpy.matmul(a.T, b))
