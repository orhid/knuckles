import logging as log

import math
from module import wave as wv

# utility
_lofrq = 144
_time_range = (0, 11)
_balance_rabge = (-math.tau/8, math.tau/8)
_frequency_range = (_lofrq, math.pow(2,6)*_lofrq)

def linear_map(x, demesne, codemesne):
  return (x - demesne[0]) * (codemesne[1] - codemesne[0]) / (demesne[1] - demesne[0]) + codemesne[0]

def exp2(x):
  return math.exp(math.log(2)*x)

def logaritmic_map(x, demesne, codemesne):
  a = (codemesne[1] - codemesne[0]) / (exp2(demesne[1] - exp2(demesne[0])))
  b = codemesne[0] - a * exp2(demesne[0])
  return a * exp2(x) + b

def partition(resolution, demesne):
  return (linear_map(j/resolution, (0,1), demesne)  for j in range(resolution+1))

def find_bounds(iterable):
  return (min(iterable), max(iterable))

def assign_bounds(arg, bounds):
  if bounds is None:
    bounds = find_bounds(arg)
  return bounds

# additive synthesis

def sglvar_mono(time, value, time_bounds = None, value_bounds = None, shape = 'sine', filename = 'sglvar_mono'):
  # maps the arguments onto time and values onto frequency panning everything in the middle

  time_bounds = assign_bounds(time, time_bounds)
  value_bounds = assign_bounds(value, value_bounds)
  
  time_range = _time_range
  frequency_range = _frequency_range

  waves = (wv.Plop(frequency=logaritmic_map(v, demesne=value_bounds, codemesne=frequency_range), offset=linear_map(t, demesne=time_bounds, codemesne=time_range), shape=shape) for v,t in zip(value, time))
  wv.write(fpath=f'{filename}.wav', waves=waves, duration=time_range[1]+1)
  return

def sglvar_stro(space, value, space_bounds = None, value_bounds = None, shape = 'sine', filename = 'sglvar_stro'):
  # maps the arguments onto balance and values onto frequency, spacing values equally in time

  space_bounds = assign_bounds(space, space_bounds)
  value_bounds = assign_bounds(value, value_bounds)

  balance_range = _balance_range
  frequency_range = _frequency_range

  waves = (wv.Plop(frequency=logaritmic_map(v, demesne=value_bounds, codemesne=frequency_range), balance=linear_map(s, demesne=space_bounds, codemesne=balance_range), offset=t, shape=shape) for v,s,t/2 in zip(value, space, itt.count()))
  # time is fucked up
  wv.write(fpath=f'{filename}.wav', waves=waves, duration=time_range[1]+1)
# continuous functions

def sglvar_mono_plot(function, demesne = (-1,1), resolution = 12, value_bounds = None, shape = 'sine', filename = 'sglvar_mono_plot'):
  argument = partition(resolution, demesne)
  value = (function(x) for x in argument)
  sglvar_mono(time=argument, value=value, time_bounds=demesne, value_bounds=value_bounds, shape=shape, filename=filename)
  return
