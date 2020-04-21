import logging as log

import math
from module import wave as wv

# utility
_lofrq = 144
_time_range = (0,11)
_frequency_range = (_lofrq, math.pow(2,6)*_lofrq)

def linear_map(x, demesne, codemesne):
  return (x - demesne[0]) * (codemesne[1] - codemesne[0]) / (demesne[1] - demesne[0]) + codemesne[0]

def exp2(x):
  return math.exp(math.log(2)*x)

def logaritmic_map(x, demesne, codemesne):
  a = (codemesne[1] - codemesne[0]) / (exp2(demesne[1] - exp2(demesne[0])))
  b = codemesne[0] - a * exp2(demesne[0])
  return a * exp2(x) + b

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

# continuous functions

def sglvar_mono_plot(function, demesne = (-1,1), resolution = 12, value_bounds = None, shape = 'sine', filename = 'sglvar_mono_plot'):
  argument = list(linear_map(j/resolution, (0,1), demesne)  for j in range(resolution+1))
  value = list(function(x) for x in argument)
  sglvar_mono(time=argument, value=value, time_bounds=demesne, value_bounds=value_bounds, shape=shape, filename=filename)
  return
