import numpy


class Step:
    def __init__(self, values, segmentDuration):
        self._values = numpy.array(values)
        
        if isinstance(segmentDuration, (list, numpy.ndarray)):
            self._segmentTime = numpy.cumsum(segmentDuration)
        else:
            self._segmentTime = (numpy.arange(self._values.size) + 1) * segmentDuration

    def __call__(self, elapsed):
        return self._values[numpy.searchsorted(self._segmentTime, elapsed % self._segmentTime[-1])]

    def iteration(self, elapsed):
        return int(numpy.floor(elapsed / self._segmentTime[-1]))


class Linear:
    def __init__(self, values, segmentDuration):
        self._values = numpy.array(values)
        
        if isinstance(segmentDuration, (list, numpy.ndarray)):
            self._segmentTime = numpy.insert(numpy.cumsum(segmentDuration), 0, 0)
        else:
            self._segmentTime = numpy.arange(self._values.size) * segmentDuration

    def __call__(self, elapsed):
        return numpy.interp(elapsed % self._segmentTime[-1], self._segmentTime, self._values)

    def iteration(self, elapsed):
        return int(numpy.floor(elapsed / self._segmentTime[-1]))
