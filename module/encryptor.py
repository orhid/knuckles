import logging as log

import math
from itertools import tee
from module import wave as wv

# utility
_lofrq = 144
_time_range = (0, 11)
_balance_range = (-math.tau/8, math.tau/8)
_frequency_range = (_lofrq, math.pow(2,6)*_lofrq)
_amplitude_range = (0.54, 0)

def linear_map(x, demesne, codemesne):
  return (x - demesne[0]) * (codemesne[1] - codemesne[0]) / (demesne[1] - demesne[0]) + codemesne[0]

def exp(x, bs = 2):
  return math.exp(math.log(bs)*x)

def exponential_map(x, demesne, codemesne, bs = 2):
  a = (codemesne[1] - codemesne[0]) / (exp(demesne[1], bs) - exp(demesne[0], bs))
  b = codemesne[0] - a * exp(demesne[0], bs)
  return a * exp(x, bs) + b

def logarithmic_map(x, demesne, codemesne, bs = 10):
  a = (codemesne[1] - codemesne[0]) / (exp(demesne[1], bs) - exp(demesne[0], bs))
  b = codemesne[1] + a * exp(demesne[0], bs)
  return -a * exp(x, bs) + b

def arctan_map(x, gentle = 0.125):
  # map from [-1,1] onto [-1,1], gentle in [0,0.25]
  return math.atan(x * math.tan(math.tau*gentle)) / (math.tau*gentle)

def arctan_midmap(x, demesne, midpoint, codemesne):
  a = (codemesne[1] - codemesne[0]) / 2
  if x > midpoint:
    return a*arctan_map((x - midpoint) / (demesne[1] - midpoint))
  else:
    return a*arctan_map((x - midpoint) / (midpoint - demesne[0]))

def partition(resolution, demesne):
  return (linear_map(j/resolution, (0,1), demesne)  for j in range(resolution+1))

def find_bounds(iterable):
  return (min(iterable), max(iterable))

def assign_bounds(arg, bounds):
  if bounds is None:
    bounds = find_bounds(arg)
  return bounds

def crt_plr(xs, ys):
  xs = list(xs)
  ys = list(ys)

  if len(xs) != len(ys):
    pass # should throw exception

  rs, ts = tee((math.sqrt(x*x + y*y), math.atan2(y,x)) for x,y in zip(xs, ys))
  return (r[0] for r in rs), (t[1] for t in ts)
  
# processing

def process_amplitude(value, bounds = None):
  value = list(value) # for safety
  demesne = assign_bounds(value, bounds)
  codemesne = _amplitude_range
  return {'value':(logarithmic_map(v, demesne, codemesne) for v in value), 'size':len(value)}

def process_frequency(value, bounds = None):
  value = list(value) # for safety
  demesne = assign_bounds(value, bounds)
  codemesne = _frequency_range
  return {'value':(exponential_map(v, demesne, codemesne) for v in value), 'size':len(value)}

def process_balance(value, bounds = None):
  value = list(value) # for safety
  demesne = assign_bounds(value, bounds = None)
  codemesne = _balance_range
  return {'value':(-linear_map(v, demesne, codemesne) for v in value), 'size':len(value)}

def process_time(value, bounds = None):
  value = list(value) # for safety
  demesne = assign_bounds(value, bounds)
  codemesne = _time_range
  return {'value':(linear_map(v, demesne, codemesne) for v in value), 'size':len(value), 'endpoint':codemesne[1]+1}

def manufacture_time(size, step = 0.5):
  return {'value':partition(size, (0, size*step)), 'size':size, 'endpoint':(size+1)*step}

# additive synthesis
## nulvar

def nulvar_sq_time(value, value_bounds = None, shape = 'sine', filename = 'nulvar_sq_time', write = True):
  # maps the values onto time panning everything in the middle, with constant frequency
  time = process_time(value, value_bounds)
  
  waves = (wv.Plop(offset=t, shape=shape) for t in time['value'])
  if write:
    wv.write(fpath=f'{filename}.wav', waves=waves, duration=time['endpoint'])
  return waves

def nulvar_sq_freq(value, value_bounds = None, shape = 'sine', filename = 'nulvar_sq_freq', write = True):
  # maps the values onto frequency panning everything in the middle, spaces evenly in time
  frequency = process_frequency(value, value_bounds)
  time = manufacture_time(frequency['size'])
  
  waves = (wv.Plop(frequency=f, offset=t, shape=shape) for f,t in zip(frequency['value'], time['value']))
  if write:
    wv.write(fpath=f'{filename}.wav', waves=waves, duration=time['endpoint'])
  return waves

def nulvar_sq_blnc(value, value_bounds = None, shape = 'sine', filename = 'nulvar_sq_blnc', write = True):
  # maps the values onto balance with constant frequency, spaces evenly in time
  balance = process_balance(value, value_bounds)
  time = manufacture_time(balance['size'])
  
  waves = (wv.Plop(balance=b, offset=t, shape=shape) for b,t in zip(balance['value'], time['value']))
  if write:
    wv.write(fpath=f'{filename}.wav', waves=waves, duration=time['endpoint'])
  return waves

def nulvar_ns(value, value_bounds = None, duration = 3, amplitude = 0.02, shape = 'sine', filename = 'nulvar_ns', write = True):
  # maps the arguments onto frequency panning everything in the middle, playing them at the same time

  frequency = process_frequency(value, value_bounds)

  waves = (wv.Wave(frequency=f, shape=shape, amplitude=amplitude) for f in frequency['value'])
  if write:
    wv.write(fpath=f'{filename}.wav', waves=waves, duration=duration)
  return waves

## univar

def univar_sq_time_freq(time, value, time_bounds = None, value_bounds = None, shape = 'sine', filename = 'univar_sq_freq', write = True):
  # maps the arguments onto time and values onto frequency panning everything in the middle

  time = process_time(time, time_bounds)
  frequency = process_frequency(value, value_bounds)

  if time['size'] != frequency['size']:
    pass # should throw exception
  
  waves = (wv.Plop(frequency=f, offset=t, shape=shape) for f,t in zip(frequency['value'], time['value']))
  if write:
    wv.write(fpath=f'{filename}.wav', waves=waves, duration=time['endpoint'])
  return waves

def univar_sq_blnc_freq(space, value, space_bounds = None, value_bounds = None, shape = 'sine', filename = 'univar_sq_blnc', write = True):
  # maps the arguments onto balance and values onto frequency, spacing values equally in time

  balance = process_balance(space, space_bounds)
  frequency = process_frequency(value, value_bounds)
  
  if balance['size'] != frequency['size']:
    pass # should throw exception
  
  time = manufacture_time(balance['size'])

  waves = (wv.Plop(frequency=f, balance=b, offset=t, shape=shape) for f,b,t in zip(frequency['value'], balance['value'], time['value']))
  if write:
    wv.write(fpath=f'{filename}.wav', waves=waves, duration=time['endpoint'])
  return waves

def univar_sq_time_blnc():
  pass

def univar_ns(space, value, space_bounds = None, value_bounds = None, duration = 3, amplitude = 0.02, shape = 'sine', filename = 'univar_ns', write = True):
  # maps the arguments onto frequency and balance, playing them at the same time

  balance = process_balance(space, space_bounds)
  frequency = process_frequency(value, value_bounds)

  if balance['size'] != frequency['size']:
    pass # should throw exception

  waves = (wv.Wave(frequency=f, balance=b, shape=shape, amplitude=amplitude) for f,b in zip(frequency['value'],balance['value']))
  if write:
    wv.write(fpath=f'{filename}.wav', waves=waves, duration=duration)
  return waves

## bivar

def bivar_sq(time, space, value, time_bounds = None, space_bounds = None, value_bounds = None, shape = 'sine', filename = 'bivar_sq', write = True):
  # maps the arguments onto time and balance, map values onto frequency

  time = process_time(time, time_bounds)
  balance = process_balance(space, space_bounds)
  frequency = process_frequency(value, value_bounds)

  if time['size'] != balance['size'] != frequency['size']:
    pass # should throw exception
  
  waves = (wv.Plop(frequency=f, balance=b, offset=t, shape=shape) for f,b,t in zip(frequency['value'], balance['value'], time['value']))
  if write:
    wv.write(fpath=f'{filename}.wav', waves=waves, duration=time['endpoint'])
  return waves
  pass

def bivar_space_sq_freq():
  # project R^2 onto a circle, unwind with balance, preserve distance with loudness, space evenly in time
  pass

def bivar_space_sq_time():
  pass

def bivar_space_ns():
  # project R^2 onto a circle, unwind with frequency, preserve distance with loudness
  pass

def bivar_space_ns_blnc():
  # project R^2 onto a circle, unwind with frequency, preserve distance with balance

## trivar

def trivar_space_sq():
  # project R^2 onto a circle, unwind with balance, preserve distance with loudness, map third argument onto time
  pass

def trivar_space_ns():
  # project R^2 onto a circle, unwind with frequency, preserve distance with loudnes, map third argument onto balances
  pass

# continuous functions

def univar_sq_freq_plot(function, demesne = (-1,1), resolution = 12, value_bounds = None, shape = 'sine', filename = 'univar_sq_freq_plot'):
  argument = list(partition(resolution, demesne))
  value = (function(x) for x in argument)
  univar_sq_freq(time=argument, value=value, time_bounds=demesne, value_bounds=value_bounds, shape=shape, filename=filename)
  return

def univar_sq_blnc_plot(function, demesne = (-1,1), resolution = 12, value_bounds = None, shape = 'sine', filename = 'univar_sq_blnc_plot'):
  argument = list(partition(resolution, demesne))
  value = (function(x) for x in argument)
  univar_sq_blnc(space=argument, value=value, space_bounds=demesne, value_bounds=value_bounds, shape=shape, filename=filename)
  return

def univar_plot():
  pass

def bivar_plot():
  pass

def trivar_plot():
  pass

# compare datasets
## nulvar

def cmp_freq_nulvar_sq_time(datasets, bounds = None, shape = 'sine', frequency_range = _frequency_range, filename = 'cmp_freq_nulvar_sq_time', write = True):
  data = [process_time(t, b) for t,b in zip(datasets, bounds)]

  # throw exception if datasets have differing sizes
  frequency = list(partition(data[0]['size']), frequency_range)
  waves = (wv.Wave(frequency=f, offset=t, shape=shape) for f,d in zip(frequency, data) for t in d['value'])
  if write:
    wv.write(fpath=f'{filename}.wav', waves=waves, duration=data[0]['endpoint'])
  return waves

def cmp_blnc_nulvar_sq_time():
  pass

def cmp_freqblnc_nulvar_sq_time():
  pass

def cmp_nulvar_sq_freq():
  # compare by balance
  pass

def cmp_nulvar_sq_blnc():
  # compare by frequency
  pass

def cmp_nulvar_ns():
  # compare by balance
  pass

## univar

def cmp_univar_sq_freq():
  # compare by balance
  pass

def cmp_univar_sq_blnc():
  # compare by frequency
  pass

# difference

## take two datasets, sonify them using the same method !and the same bounds! then flip the phase of one and add them together
