import numpy


class Pid:
    def __init__(self, Kp_, Ki_, Kd_, dt_ = 1.):
        self._Kp_ = Kp_
        self._Ki_ = Ki_
        self._Kd_ = Kd_
        self._dt_ = dt_
        self._enable = True
        self._integral = 0.
        self._T0_ = None
        self._T1_ = None
        self._e0_ = None
        self._e1_ = None

    def __call__(self, setPoint, T_):
        output = 0.
        
        self._T0_ = T_
        self._e0_ = setPoint - self._T0_

        if self._T1_ is not None:
            #if self._enable:

            if (numpy.abs(self._e0_) > 10.):
                self._integral = 0
            else:
                self._integral += self._e0_ * self._dt_
            
            dedt_ = (self._e0_ - self._e1_) / self._dt_

            P_ = self._e0_ * self._Kp_
            I_ = self._integral * self._Ki_
            D_ = dedt_ * self._Kd_

            output = P_ + I_ + D_

            if output < 0.:
                output = 0.
                self._enable = False
            elif output > 1.:
                output = 1.
                self._enable = False
            else:
                self._enable = True

        self._T1_ = self._T0_
        self._e1_ = self._e0_

        return output
