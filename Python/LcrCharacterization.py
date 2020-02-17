import atexit
import time
import numpy
import matplotlib.pyplot as pyplot

from Chamber import *
from Lcr import *
from Pid import *
from Si import *
from SetPoint import *


# Configuration variables

chamberPort = 'COM3'
lcrPort     = 'COM7'

oversample = 256
dt_ = 0.7368

Kp_ = 0.06
Ki_ = 0.0008
Kd_ = 0

setPointValues     = numpy.array([25, 25, 75, 75])
setPointDuration   = numpy.array([15, 50, 15]) * 60
setPointIterations = 1

setPoint = Linear(setPointValues, setPointDuration)

V_ = 3.261    # Thermistor circuit applied voltage
R_ = 2178.6   # Thermistor series resistor


# Functions / classes

def atExit():
    if 'initialPacket' in globals() and initialPacket is not None:
        print('Saving data...')
        
        metadata = {}
        metadata['Duration']  = elapsed
        metadata['Timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tStart))
        metadata['Frequency'] = initialPacket['Frequency']
        metadata['Quantity 1'] = initialPacket['Quantity 1']
        metadata['Quantity 2'] = initialPacket['Quantity 2']

        sp = numpy.array(SP_)
        t  = numpy.array(T_)
        p  = numpy.array(P_)
        m1 = numpy.array(M1_)
        m2 = numpy.array(M2_)

        numpy.savez('../Data/Characterization_%s.npz' % time.strftime('%Y-%m-%d_%H%M', time.localtime(tStart)), metadata = metadata, T = t, P = p, SP = sp, M1 = m1, M2 = m2)


def log(elapsed, SP_, T_, P_, M1_, M2_, quantity1, quantity2):
    timeString    = '[{:.1f} s]'.format(elapsed)
    chamberString = 'Chamber: [SP: {:.2f} \u00B0C, T: {:.2f} \u00B0C, P: {:.3f} AU]'.format(SP_[-1], T_[-1], P_[-1])
        
    measurement1 = si(M1_[-1], unit(quantity1))
        
    if quantity2 is None:
        lcrString = 'LCR: [{:s}: {:s}]'.format(quantity1, measurement1)
    else:
        measurement2 = si(M2_[-1], unit(quantity2))
        lcrString = 'LCR: [{:s}: {:s}, {:s}: {:s}]'.format(quantity1, measurement1, quantity2, measurement2)

    return '{:s} {:s}, {:s}'.format(timeString, chamberString, lcrString)


class Plot:
    def __init__(self):
        self._init = False
         
    def __call__(self, elapsed, SP_, T_, P_, M1_, M2_, quantity1, quantity2):
        if (len(T_) > 2) and (len(M1_) > 2):
            if self._init == False:
                self._init = True

                pyplot.ion()
                self._fig = pyplot.figure(figsize = (16, 8))

                self._ax1 = self._fig.add_subplot(211)

                self._l1a, = self._ax1.plot([], [], color = 'C2')
                self._l1b, = self._ax1.plot([], [], color = 'C0')
                self._ax1.set_ylabel('Temperature (\u00B0C)', color = 'C0')

                self._ax2 = self._ax1.twinx()

                self._l2, = self._ax2.plot([], [], color = 'C1')
                self._ax2.set_ylabel('Power (au)', color = 'C1')
                self._ax2.set_ylim(-0.02, 1.02)

                self._ax3 = self._fig.add_subplot(212, sharex = self._ax1)
                self._l3, = self._ax3.plot([], [], color = 'C0')
                self._ax3.set_xlabel('Time (m)')
                self._ax3.set_ylabel('{:s} ({:s})'.format(quantity1, unit(quantity1)), color = 'C0')

                if quantity2 is not None:
                    self._ax4 = self._ax3.twinx()
                    self._l4, = self._ax4.plot([], [], color = 'C1')
                    u = unit(quantity2)
                    if u is None:
                        unitString = ''
                    else:
                        unitString = '({:s})'.format(u)
                    self._ax4.set_ylabel('{:s} {:s}'.format(quantity2, unitString), color = 'C1')

            tChamber = numpy.linspace(0, elapsed, len(T_))

            self._l1a.set_xdata(tChamber / 60.)
            self._l1a.set_ydata(SP_)

            self._l1b.set_xdata(tChamber / 60.)
            self._l1b.set_ydata(T_)

            self._l2.set_xdata(tChamber / 60.)
            self._l2.set_ydata(P_)

            self._ax1.set_xlim(tChamber[0] / 60., tChamber[-1] / 60.)

            Tmin_ = min(min(T_), min(SP_))
            Tmax_ = max(max(T_), max(SP_))
            
            if (Tmin_ != Tmax_):
                delta = (Tmax_ - Tmin_) / 50.
                self._ax1.set_ylim(Tmin_ - delta, Tmax_ + delta)

            tLcr = numpy.linspace(0, elapsed, len(M1_))

            self._l3.set_xdata(tLcr / 60.)
            self._l3.set_ydata(M1_)

            m1min = min(M1_)
            m1max = max(M1_)
            
            if (m1min != m1max):
                delta = (m1max - m1min) / 50.
                self._ax3.set_ylim(m1min - delta, m1max + delta)
            
            if quantity2 is not None:
                self._l4.set_xdata(tLcr / 60.)
                self._l4.set_ydata(M2_)
            
                m2min = min(M2_)
                m2max = max(M2_)
            
                if (m2min != m2max):
                    delta = (m2max - m2min) / 50.
                    self._ax4.set_ylim(m2min - delta, m2max + delta)
                
            self._fig.canvas.draw()
            self._fig.canvas.flush_events()


# Code
atexit.register(atExit)

polynomial   = numpy.load('../Data/Polynomial.npy')
coefficients = numpy.load('../Data/Coefficients.npy')

chamber = Chamber(chamberPort)
chamber.setupThermistor(oversample, polynomial, coefficients, V_, R_)

lcr = Lcr(lcrPort)

pid = Pid(Kp_, Ki_, Kd_, dt_)

plot = Plot()

initialPacket = None

SP_ = []
T_  = []
P_  = []
M1_ = []
M2_ = []

tStart = time.time()

while True:
    chamberMeasurements = chamber.read()
    packets = lcr.read()

    if chamber.error:
        print('ERROR: Temperature chamber data link error!')
        quit()

    if lcr.error:
        print('ERROR: LCR data link error!')
        quit()

    if initialPacket is not None:
        for packet in packets:
            error  = packet['Frequency']  != initialPacket['Frequency']
            error |= packet['Quantity 1'] != initialPacket['Quantity 1']
            error |= packet['Quantity 2'] != initialPacket['Quantity 2']
            
            if error:
                print('ERROR: Settings changed!')
                quit()

    elapsed = time.time() - tStart

    if setPoint.iteration(elapsed) > setPointIterations - 1:
        print('Execution Complete.')
        quit()

    if len(chamberMeasurements) > 0:
        newSp = setPoint(elapsed)
        
        newP = pid(newSp, chamberMeasurements[-1])
        chamber.write(newP)

        if (len(P_) > 0.):
            lastSp = SP_[-1]
            lastP  = P_[-1]
        else:
            lastSp = 0.
            lastP  = 0.

        for i in range(len(chamberMeasurements) - 1):
            SP_.append(lastSp)
            P_.append(lastP)

        SP_.append(newSp)
        T_.extend(chamberMeasurements)
        P_.append(newP)
    
    if len(packets) > 0:
        if initialPacket is None:
            initialPacket = packets[0]

        for packet in packets:
            M1_.append(packet['Measurement 1'])

            if packet['Quantity 2'] is not None:
                M2_.append(packet['Measurement 2'])

    if len(chamberMeasurements) > 0 and len(M1_) > 0:
        quantity1 = initialPacket['Quantity 1']
        quantity2 = initialPacket['Quantity 2']

        print(log(elapsed, SP_, T_, P_, M1_, M2_, quantity1, quantity2))
        plot(elapsed, SP_, T_, P_, M1_, M2_, quantity1, quantity2)
