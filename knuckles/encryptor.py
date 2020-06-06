import logging as log
import math
from itertools import tee

from . import wave as wv

# utility
_lofrq = 144
_time_range = (0, 12)
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
    raise IndexError(f'Provided datasets are of differing lengths, which may result in unexpected bahaviour.')

  rs, ts = tee((math.sqrt(x*x + y*y), math.atan2(y,x)) for x,y in zip(xs, ys))
  return (r[0] for r in rs), (t[1] for t in ts)
 
def test_len(*args):
  if len({arg['size'] for arg in args}) > 1:
    raise IndexError(f'Provided datasets are of differing lengths, which may result in unexpected bahaviour.')

# processing
def process_data(value):
  value = list(value)
  return {'value':(v for v in value), 'size':len(value)}

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

def process_balance_space(value, bounds = None, midpoint = None):
  value = list(value) # for safety
  demesne = assign_bounds(value, bounds = None)
  if midpoint is None:
    midpoint = (demesne[0] + demesne[1])/2
  codemesne = _balance_range
  return {'value':(-arctan_midmap(v, demesne, midpoint, codemesne) for v in value), 'size':len(value)}

def process_time(value, bounds = None):
  value = list(value) # for safety
  demesne = assign_bounds(value, bounds)
  codemesne = _time_range
  return {'value':(linear_map(v, demesne, codemesne) for v in value), 'size':len(value), 'endpoint':codemesne[1]+1}

def manufacture_time(size, step = 0.5):
  return {'value':partition(size, (0, size*step)), 'size':size, 'endpoint':(size+1)*step}

# additive synthesis
## nulvar

def nulvar_sq_time(value, value_bounds = None, frequency = 432, balance = 0, shape = 'sine', filename = 'nulvar_sq_time', write = True):
  # maps the values onto time panning everything in the middle, with constant frequency
  time = process_time(value, value_bounds)
  
  waves = (wv.Plop(offset=t, frequency=frequency, balance=balance, shape=shape) for t in time['value'])
  sonif = wv.Sonification(waves, time['endpoint'], filename)
  if write:
    sonif.render()
  return sonif

def nulvar_sq_freq(value, value_bounds = None, balance = 0, shape = 'sine', filename = 'nulvar_sq_freq', write = True):
  # maps the values onto frequency panning everything in the middle, spaces evenly in time
  frequency = process_frequency(value, value_bounds)
  time = manufacture_time(frequency['size'])
  
  waves = (wv.Plop(frequency=f, offset=t, balance=balance, shape=shape) for f,t in zip(frequency['value'], time['value']))
  sonif = wv.Sonification(waves, time['endpoint'], filename)
  if write:
    sonif.render()
  return sonif

def nulvar_sq_blnc(value, value_bounds = None, frequency = 432, shape = 'sine', filename = 'nulvar_sq_blnc', write = True):
  # maps the values onto balance with constant frequency, spaces evenly in time
  balance = process_balance(value, value_bounds)
  time = manufacture_time(balance['size'])
  
  waves = (wv.Plop(balance=b, offset=t, frequency=frequency, shape=shape) for b,t in zip(balance['value'], time['value']))
  sonif = wv.Sonification(waves, time['endpoint'], filename)
  if write:
    sonif.render()
  return sonif

def nulvar_ns(value, value_bounds = None, duration = 3, amplitude = 0.02, balance=0, shape = 'sine', filename = 'nulvar_ns', write = True):
  # maps the arguments onto frequency panning everything in the middle, playing them at the same time
  frequency = process_frequency(value, value_bounds)

  waves = (wv.Wave(frequency=f, balance=balance, shape=shape, amplitude=amplitude) for f in frequency['value'])
  sonif = wv.Sonification(waves, duration, filename)
  if write:
    sonif.render()
  return sonif

## univar

def univar_sq_time_freq(time, value, time_bounds = None, value_bounds = None, balance = 0, shape = 'sine', filename = 'univar_sq_freq', write = True):
  # maps the arguments onto time and values onto frequency panning everything in the middle
  time = process_time(time, time_bounds)
  frequency = process_frequency(value, value_bounds)
  
  test_len(time, frequency)
  
  waves = (wv.Plop(frequency=f, offset=t, balance=balance, shape=shape) for f,t in zip(frequency['value'], time['value']))
  sonif = wv.Sonification(waves, time['endpoint'], filename)
  if write:
    sonif.render()
  return sonif

def univar_sq_blnc_freq(space, value, space_bounds = None, value_bounds = None, shape = 'sine', filename = 'univar_sq_blnc', write = True):
  # maps the arguments onto balance and values onto frequency, spacing values equally in time

  balance = process_balance(space, space_bounds)
  frequency = process_frequency(value, value_bounds)
 
  test_len(balance, frequency)
  
  time = manufacture_time(balance['size'])

  waves = (wv.Plop(frequency=f, balance=b, offset=t, shape=shape) for f,b,t in zip(frequency['value'], balance['value'], time['value']))
  sonif = wv.Sonification(waves, time['endpoint'], filename)
  if write:
    sonif.render()
  return sonif

def univar_sq_time_blnc(time, space, time_bounds = None, space_bounds = None, frequency = 432, shape = 'sine', filename = 'univar_sq_blnc', write = True):
  # maps the arguments onto time and values onto balance
  
  time = process_time(time, time_bounds)
  balance = process_balance(space, space_bounds)

  test_len(time, balance)
  
  waves = (wv.Plop(balance=b, offset=t, frequency=frequency, shape=shape) for b,t in zip(balance['value'], time['value']))
  sonif = wv.Sonification(waves, time['endpoint'], filename)
  if write:
    sonif.render()
  return sonif

def univar_ns(space, value, space_bounds = None, value_bounds = None, duration = 3, amplitude = 0.02, shape = 'sine', filename = 'univar_ns', write = True):
  # maps the arguments onto frequency and balance, playing them at the same time

  balance = process_balance(space, space_bounds)
  frequency = process_frequency(value, value_bounds)

  test_len(balance, frequency)

  waves = (wv.Wave(frequency=f, balance=b, shape=shape, amplitude=amplitude) for f,b in zip(frequency['value'],balance['value']))
  sonif = wv.Sonification(waves, duration, filename)
  if write:
    sonif.render()
  return sonif

def univar_space_ns(xarg, yarg, duration = 3, amplitude = 0.02, shape = 'sine', filename = 'univar_space_ns', write = True):
  # project R^2 onto a circle, unwind with frequency, preserve distance with loudness
  ampli, frequency = crt_plr(xarg, yarg)
  ampli = process_loudness(ampli)
  frequency = process_frequency(frequency, (-math.tau/2, math.tau/2))

  test_len(ampli, frequency)

  waves = (wv.Wave(frequency=f, shape=shape, amplitude=amplitude*a) for f,a in zip(frequency['value'], ampli['value']))
  sonif = wv.Sonification(waves, duration, filename)
  if write:
    sonif.render()
  return sonif

def univar_space_ns_blnc(xarg, yarg, duration = 3, amplitude = 0.02, shape = 'sine', filename = 'univar_space_ns_blnc', write = True):
  # project R^2 onto a circle, unwind with frequency, preserve distance with balance
  balance, frequency = crt_plr(xarg, yarg)
  balance = process_balance_space(balance)
  frequency = process_frequency(frequency, (-math.tau/2, math.tau/2))

  test_len(balance, frequency)

  waves = (wv.Wave(frequency=f, balance=b, shape=shape, amplitude=amplitude) for f,b in zip(frequency['value'], balance['value']))
  sonif = wv.Sonification(waves, duration, filename)
  if write:
    sonif.render()
  return sonif

## bivar

def bivar_sq(time, space, value, time_bounds = None, space_bounds = None, value_bounds = None, shape = 'sine', filename = 'bivar_sq', write = True):
  # maps the arguments onto time and balance, map values onto frequency

  time = process_time(time, time_bounds)
  balance = process_balance(space, space_bounds)
  frequency = process_frequency(value, value_bounds)

  test_len(time, balance, frequency)
  
  waves = (wv.Plop(frequency=f, balance=b, offset=t, shape=shape) for f,b,t in zip(frequency['value'], balance['value'], time['value']))
  sonif = wv.Sonification(waves, time['endpoint'], filename)
  if write:
    sonif.render()
  return sonif

def bivar_space_sq_freq(xarg, yarg, value, value_bounds = None, shape = 'sine', filename = 'bivar_space_sq_freq', write = True):
  # project R^2 onto a circle, unwind with balance, preserve distance with loudness, space evenly in time
  ampli, balance = crt_plr(xarg, yarg)
  ampli = process_amplitude(ampli)
  balace = process_balance(balance, (-math.tau/2, math.tau/2))
  frequency = process_frequency(value, value_bounds)

  test_len(ampli, balance, frequency)

  time = manufacture_time(ampli['size'])
  waves = (wv.Plop(frequency=f, balance=b, offset=t, apmlitude=a, shape=shape) for f,b,t,a in zip(frequency['value'], balance['value'], time['value'], ampli['value']))
  sonif = wv.Sonification(waves, time['endpoint'], filename)
  if write:
    sonif.render()
  return sonif

def bivar_space_sq_time(xarg, yarg, time, time_bounds = None, shape = 'sine', filename = 'bivar_space_sq_time', write = True):
  # project R^2 onto a circle, unwind with balance, preserve distance with loudness
  ampli, balance = crt_plr(xarg, yarg)
  ampli = process_amplitude(ampli)
  balace = process_balance(balance, (-math.tau/2, math.tau/2))
  time = process_time(time, time_bounds)

  test_len(ampli, balance, time)

  waves = (wv.Plop(balance=b, offset=t, apmlitude=a, shape=shape) for b,t,a in zip(balance['value'], time['value'], ampli['value']))
  sonif = wv.Sonification(waves, time['endpoint'], filename)
  if write:
    sonif.render()
  return sonif

def bivar_space_ns(xarg, yarg, space, space_bounds = None, duration = 3, amplitude = 0.02, shape = 'sine', filename = 'bivar_space_ns', write = True):
  # project R^2 onto a circle, unwind with frequency, preserve distance with loudnes, map third argument onto balance
  ampli, frequency = crt_plr(xarg, yarg)
  ampli = process_loudness(ampli)
  frequency = process_frequency(frequency, (-math.tau/2, math.tau/2))
  balance = process_balance(space, space_bounds)
  
  test_len(ampli, balance, frequency)

  waves = (wv.Wave(frequency=f, balance=b, shape=shape, amplitude=amplitude*a) for f,b,a in zip(frequency['value'], balance['value'], ampli['value']))
  sonif = wv.Sonification(waves, duration, filename)
  if write:
    sonif.render()
  return sonif

## trivar

def trivar_space_sq(xarg, yarg, time, value, time_bounds = None, value_bounds = None, shape = 'sine', filename = 'trivar_space_sq', write = True):
  # project R^2 onto a circle, unwind with balance, preserve distance with loudness, map third argument onto time
  ampli, balance = crt_plr(xarg, yarg)
  ampli = process_amplitude(ampli)
  balace = process_balance(balance, (-math.tau/2, math.tau/2))
  time = process_time(time, time_bounds)
  frequency = process_frequency(value, value_bounds)

  test_len(ampli, balance, time, frequency)

  waves = (wv.Plop(frequency=f, balance=b, offset=t, apmlitude=a, shape=shape) for f,b,t,a in zip(frequency['value'], balance['value'], time['value'], ampli['value']))
  sonif = wv.Sonification(waves, time['endpoint'], filename)
  if write:
    sonif.render()
  return sonif

# compare datasets
## nulvar

def cmp_freq_nulvar_sq_time(datasets, bounds = None, shape = 'sine', frequency_range = _frequency_range, filename = 'cmp_freq_nulvar_sq_time', write = True):
  # compare by frequency
  datasets = [process_data(data) for data in datasets]
  test_len(*datasets)
  frequency = list(partition(len(datasets)-1, frequency_range))
  
  sonif = wv.soni_sum(nulvar_sq_time(data['value'], bounds, frequency=f, shape=shape, write=False) for data,f in zip(datasets,frequency))
  sonif.filename = filename
  if write:
    sonif.render()
  return sonif

def cmp_blnc_nulvar_sq_time(datasets, bounds = None, shape = 'sine', balance_range = _balance_range, filename = 'cmp_blnc_nulvar_sq_time', write = True):
  # compare by balance
  datasets = [process_data(data) for data in datasets]
  test_len(*datasets)
  balance = list(partition(len(datasets)-1, balance_range))
  log.debug(balance)

  sonif = wv.soni_sum(nulvar_sq_time(data['value'], bounds, balance=b, shape=shape, write=False) for data,b in zip(datasets,balance))
  sonif.filename = filename
  if write:
    sonif.render()
  return sonif

def cmp_freqblnc_nulvar_sq_time(datasets, bounds = None, shape = 'sine', balance_range = _balance_range, frequency_range = _frequency_range, filename = 'cmp_freqblnc_nulvar_sq_time', write = True):
  # compare by balance and frequency
  datasets = [process_data(data) for data in datasets]
  test_len(*datasets)
  balance = list(partition(len(datasets)-1, balance_range))
  frequency = list(partition(len(datasets)-1, frequency_range))
  
  sonif = wv.soni_sum(nulvar_sq_time(data['value'], bounds, frequency=f, balance=b, shape=shape, write=False) for data,f,b in zip(datasets,frequency,balance))
  sonif.filename = filename
  if write:
    sonif.render()
  return sonif

def cmp_nulvar_sq_freq(datasets, bounds = None, shape = 'sine', balance_range = _balance_range, filename = 'cmp_nulvar_sq_freq', write = True):
  # compare by balance
  datasets = [process_data(data) for data in datasets]
  test_len(*datasets)
  balance = list(partition(len(datasets)-1, balance_range))
  
  sonif = wv.soni_sum(nulvar_sq_freq(data['value'], bounds, balance=b, shape=shape, write=False) for data,b in zip(datasets,balance))
  sonif.filename = filename
  if write:
    sonif.render()
  return sonif

def cmp_nulvar_sq_blnc(datasets, bounds = None, shape = 'sine', frequency_range = _frequency_range, filename = 'cmp_nulvar_sq_blnc', write = True):
  # compare by frequency
  datasets = [process_data(data) for data in datasets]
  test_len(*datasets)
  frequency = list(partition(len(datasets)-1, frequency_range))
  
  sonif = wv.soni_sum(nulvar_sq_blnc(data['value'], bounds, frequency=f, shape=shape, write=False) for data,f in zip(datasets,frequency))
  sonif.filename = filename
  if write:
    sonif.render()
  return sonif

def cmp_nulvar_ns(datasets, bounds = None, duration = 3, amplitude = 0.02, balance_range = _balance_range, filename = 'cmp_nulvar_ns', write = True):
  # compare by balance
  datasets = [process_data(data) for data in datasets]
  test_len(*datasets)
  balance = list(partition(len(datasets)-1, balance_range))
  
  sonif = wv.soni_sum(nulvar_ns(data['value'], bounds, balance=b, duration=duration, amplitude=amplitude, write=False) for data,b in zip(datasets,balance))
  sonif.filename = filename
  if write:
    sonif.render()
  return sonif

## univar

def cmp_univar_sq_freq(time_datasets, value_datasets, time_bounds = None, value_bounds = None, shape = 'sine', balance_range = _balance_range, filename = 'cmp_univar_sq_freq', write = True):
  # compare by balance
  time = [process_data(data) for data in time_datasets]
  frequency = [process_data(data) for data in value_datasets]
  test_len(*time)
  test_len(*frequency)
  balance = list(partition(len(time)-1, balance_range))
  
  sonif = wv.soni_sum(univar_sq_time_freq(t['value'], f['value'], time_bounds, value_bounds, balance=b, shape=shape, write=False) for t,f,b in zip(time, frequency, balance))
  sonif.filename = filename
  if write:
    sonif.render()
  return sonif

def cmp_univar_sq_blnc(time_datasets, space_datasets, time_bounds = None, space_bounds = None, shape = 'sine', frequency_range = _frequency_range, filename = 'cmp_univar_sq_blnc', write = True):
  # compare by frequency
  time = [process_data(data) for data in time_datasets]
  balance = [process_data(data) for data in space_datasets]
  test_len(*time)
  test_len(*balance)
  frequency = list(partition(len(time)-1, frequency_range))
  
  sonif = wv.soni_sum(univar_sq_time_blnc(t['value'], b['value'], time_bounds, value_bounds, frequency=f, shape=shape, write=False) for t,b,f in zip(time, balance, frequency))
  sonif.filename = filename
  if write:
    sonif.render()
  return sonif

# difference

def diff(sonif1, sonif2, filename = 'diff', write = True):
  # take two wave sequences, flip the phase of one and add them together
  sonif2.flip_phase()
  sonif = sonif1 + sonif2
  if write:
    sonif.render()
  return sonif
