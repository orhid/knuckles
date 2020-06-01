import logging as log

import math
from itertools import chain, count, islice, repeat

from wavebender import write_wavefile

_framerate = 48000

## useful maths

def sign(x):
  if x > 0:
    return 1
  elif x < 0:
    return -1
  else:
    return 0

def bump(x, length = 1):
  x = x / length
  return 21.02*x - 149.55*x**2 + 433.75*x**3 - 622.64*x**4 + 437.84*x**5 - 120.42*x**6

## fool proofing
  ## functions that check if all atheartbutes are inside their given range

def fool_amplitude(amplitude):
  return min(1, max(-1, amplitude))

def safe_sum(iterable):
  return min(1, max(-1, sum(iterable)))

## pan law

def lAmp(balance):
  return math.sqrt(2) * (math.cos(balance) + math.sin(balance)) / 2

def rAmp(balance):
  return math.sqrt(2) * (math.cos(balance) - math.sin(balance)) / 2

## wave shapes

def sine(x, period):
  return math.sin(math.tau * period * x / 2)

def saw(x, period):
  if period * _framerate < 3456:
    return (8 / math.tau) * math.atan(math.tan(x * math.tau *  period / 4))
  else:
    return sumsine(x, period, 1)

def square(x, period):
  if period * _framerate < 3456:
    return sign(sine(x, period))
  else:
    return sumsine(x, period, 2)

def heart(x, period):
  return sumsine(x, period, 3)

def funnel(x, period):
  return sumsine(x, period, 4)

def sumsine(x, period, mod):
  n = math.floor(((20000 / (period * _framerate)) + 1) / mod) + 1
  return 4 * mod * sum(math.pow(-1, k*mod) * math.sin(math.tau * period * x * (mod*k+1)) / (mod*k+1) for k in range(n)) / math.tau

## base waves

_wvshapes = {'sine':sine, 'square':square, 'saw':saw, 'heart':heart, 'funnel':funnel}

class Wave():
  def __init__(self, shape = 'sine', frequency = 432.0, amplitude = 0.12, offset = 0, balance = 0):
    self.shape = shape # if shape in _wvshapes.keys()
    self.period = float(frequency) / float(_framerate)
    self.amplitude = fool_amplitude(amplitude)
    self.offset = int(offset * framerate)

    # balance should be in [-math.tau/8 , math.tau/8]
    self.lAmp = lAmp(balance)
    self.rAmp = rAmp(balance)

  def mono_generator(self, amp = 1):
    for i in count():
      yield amp * float(self.amplitude) * _wvshapes[self.shape](float(i), self.period)

  def left_generator(self):
    return self.mono_generator(amp=self.lAmp)

  def right_generator(self):
    return self.mono_generator(amp=self.rAmp)

  def push(self, iterator):
    return chain(repeat(0, self.offset), iterator, repeat(0))
    
  def left_signal(self):
    return self.push(self.left_generator())

  def right_signal(self):
    return self.push(self.right_generator())

  def signal(self):
    return (self.left_signal(), self.right_signal())

  ### modifiers

  def flip_phase(self):
    self.amplitude = -self.amplitude

  def pan_left(self):
    self.lAmp = 1
    self.rAmp = 0

  def pan_center(self):
    self.lAmp = lAmp(0)
    self.rAmp = rAmp(0)

  def pan_right(self):
    self.lAmp = 0
    self.rAmp = 1

class Blip(Wave):
  ## short chunks of sound of a given shape
  ## duration is counted in seconds for all shapes
  
  def __init__(self, duration = 1, **kwargs):
    super().__init__(**kwargs)
    self.duration = duration * _framerate

  def mono_generator(self, amp = 1):
    return islice(super().mono_generator(amp), self.duration)

class Plop(Blip):
  ## short decaying chunks of sound of a given shape
  ## duration is counted in seconds for all shapes

  def mono_generator(self, amp = 1):
    for i, s in zip(count(), super().mono_generator(amp)):
      yield s * bump(i, self.duration)

## wav creation

### the following two functions should be combined into one, implementing the Wave class
def compute_samples(channels, nsamples=None):
  '''
  create a generator which computes the samples.
  essentially it creates a sequence of the sum of each function in the channel
  at each sample in the file for each channel.
  '''
  return islice(zip(*(map(safe_sum, zip(*channel)) for channel in channels)), nsamples)

def _samples(waves, duration = None):
  signal = (s for s in zip(*(w.signal() for w in waves)))
  
  if duration is not None:
    duration = int(duration * _framerate)
  return compute_samples(signal, duration)

def write(fpath, waves, duration):
  # fpath : path to write file to
  # waves : waves
  write_wavefile(fpath, samples=_samples(waves, duration), nchannels=2, sampwidth=2, framerate=_framerate, bufsize=2048)
  return
