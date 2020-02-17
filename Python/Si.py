import numpy


def si(value, suffix = '', digits = 4):
    if suffix == '\u00B0' or suffix == '':
        separator = ''
        symbol = ''
    else:
        separator = ' '

        if value != 0:
            symbols = ['y', 'z', 'a', 'f', 'p', 'n', 'u', 'm', '', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
            
            pow1000 = int(numpy.floor(numpy.log10(value) / 3.))
            value /= (1000. ** pow1000)
            
            symbol = symbols[pow1000 + 8]
        else:
            symbol = ''
    
    if value == 0:
        number = '0'
    else:
        pow10 = int(numpy.floor(numpy.log10(value)))
        number = '{{:.{:d}f}}'.format(max(0, digits - pow10 - 1)).format(value)
    
    return '{:s}{:s}{:s}{:s}'.format(number, separator, symbol, suffix)
