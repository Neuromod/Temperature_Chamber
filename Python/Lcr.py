import time
import serial


class Lcr:
    _PACKET_PERIOD = 0.5024

    def __init__(self, port):
        self._uart = serial.Serial(port, baudrate = 9600, bytesize = 8, parity = 'N', stopbits = 1, timeout = 0)
        self._buffer = []
        self._synced = False
        self._error = False
        self._t0 = None
        self._t1 = None
        self._lastRx = time.time()
        self._packetCount = 0

    def read(self):
        packets = []
        
        t = time.time()

        if self._uart.in_waiting > 0:
            self._lastRx = t
            self._buffer.extend(list(self._uart.read(self._uart.in_waiting)))

            if not self._synced and len(self._buffer) >= 17:
                for i in range(len(self._buffer) - 16):
                    if self._buffer[i] == 0x00 and self._buffer[i + 1] == 0x0D and self._buffer[i + 15] == 0x0D and self._buffer[i + 16] == 0x0A:
                        self._synced = True
                        self._buffer = self._buffer[i:]
                        break
            
            if self._synced:
                if not self._error and (self._packetCount > 0 or self._t1 is None):       # Check for missing packets
                    section = len(self._buffer) % 17

                    if section != 0:
                        self._t0 = t - section * 0.0177
                       
                        if self._t1 is not None:
                            if (self._t0 - self._t1) - (self._packetCount + len(self._buffer) // 17) * self._PACKET_PERIOD < .3:
                                self._packetCount = 0
                            else:
                                self._error = True
                        
                        self._t1 = self._t0

                while len(self._buffer) >= 17:
                    if self._buffer[0] != 0x00 or self._buffer[1] != 0x0D or self._buffer[15] != 0x0D or self._buffer[16] != 0x0A:
                        self._synced = False
                        self._error = True
                        break
                    else:
                        packets.append(self._getPacket())
                        self._buffer = self._buffer[17:]
                        self._packetCount += 1

        if t - self._lastRx > 5.:      # If 5 s have elapsed without receiving any deta
            self._error = True

        return packets

    @property
    def start(self):
        return self._start

    @property
    def error(self):
        return self._error

    def _getPacket(self):
        packet = {}

        value = self._buffer[3] >> 5

        if value == 0:
            frequency = 100
        elif value == 1:
            frequency = 120
        elif value == 2:
            frequency = 1_000
        elif value == 3:
            frequency = 10_000
        elif value == 4:
            frequency = 100_000
        elif value == 5:
            frequency = 0
        else: 
            frequency = None

        packet['Frequency'] = frequency

        if (self._buffer[2] & 0x80):
            suffix = 'p'
        else:
            suffix = 's'

        value = self._buffer[5]
        
        if value == 1:
            quantity = 'L' + suffix
        elif value == 2:
            quantity = 'C' + suffix
        elif value == 3:
            quantity = 'R' + suffix
        elif value == 4:
            quantity = 'R'
        else:
            quantity = None

        packet['Quantity 1'] = quantity
        
        scale = []

        for value in [self._buffer[8] >> 3, self._buffer[14] >> 3]:
            if value == 9:
                scale.append(1E-12)
            elif value == 10:
                scale.append(1E-9)
            elif value == 5 or value == 11:
                scale.append(1E-6)
            elif value == 6 or value == 12:
                scale.append(1E-3)
            elif value == 2 or value == 8:
                scale.append(1E3)
            elif value == 3:
                scale.append(1E6)
            else:
                scale.append(1)
        
        measurement = float((self._buffer[6] << 8) + self._buffer[7]) * 10. ** -float(self._buffer[8] & 0x07) * scale[0]

        packet['Measurement 1'] = measurement
        
        value = self._buffer[10]

        if value == 1:
            quantity = 'DF'
        elif value == 2:
            quantity = 'Q'
        elif value == 3:
            quantity = 'R' + suffix
        elif value == 4:
            quantity = '\u03B8'    # Lowercase theta
        else:
            quantity = None

        packet['Quantity 2'] = quantity

        if quantity == None:
            measurement = None
        else:
            measurement = float((self._buffer[11] << 8) + self._buffer[12]) * 10. ** -float(self._buffer[13] & 0x07) * scale[1]

        packet['Measurement 2'] = measurement

        return packet


def unit(quantity):
    if quantity[0] == 'L':
        return 'H'
    elif quantity[0] == 'C':
        return 'F'
    elif quantity[0] == 'R':
        return '\u03A9'           # Uppercase omega
    elif quantity == '\u03B8':    # Lowercase theta
        return '\u00B0'           # Degree
    else:
        return ''