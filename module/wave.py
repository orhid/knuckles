import logging as log

import math
from itertools import chain, count, islice, repeat

from wavebender import write_wavefile

## useful maths

def sign(x):
  if x > 0:
    return 1
  elif x < 0:
    return -1
  else:
    return 0

def bump(x, length):
  x = x / length
  return 21.02*x - 149.55*x**2 + 433.75*x**3 - 622.64*x**4 + 437.84*x**5 - 120.42*x**6

## fool proofing
  ## functions that check if all attributes are inside their given range

def fool_amplitude(amplitude):
  return max(0, min(amplitude, 1))

def safe_sum(iterable):
  return min(1, max(-1,  sum(iterable)))

## pan law

def lAmp(balance):
  return math.sqrt(2) * (math.cos(balance) + math.sin(balance)) / 2

def rAmp(balance):
  return math.sqrt(2) * (math.cos(balance) - math.sin(balance)) / 2

## wave shapes

def sine(x, period):
  return math.sin(math.tau * period * x / 2)

def square(x, period):
  return sign(sine(x, period))

def saw(x, period):
  return (4 / math.tau) * math.atan(math.tan(x * math.tau *  period / 4))

## base waves

_framerate = 48000
_wvshapes = {'sine':sine, 'square':square, 'saw':saw}

class Wave():
  def __init__(self, shape = 'sine', frequency = 432.0, amplitude = 0.12, offset = 0, balance = 0, framerate = _framerate):
    self.shape = shape # if shape in _wvshapes.keys()
    self.period = float(frequency) / float(framerate)
    self.amplitude = fool_amplitude(amplitude)
    self.offset = int(offset * framerate)
    self.lAmp = lAmp(balance)
    self.rAmp = rAmp(balance)

    self.framerate = framerate

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

class Blip(Wave):
  ## short chunks of sound of a given shape
  ## duration is counted in seconds for all shapes
  
  def __init__(self, duration = 1, **kwargs):
    super().__init__(**kwargs)
    self.duration = duration * self.framerate

  def mono_generator(self):
    return islice(super().mono_generator(), self.duration)

class Plop(Blip):
  ## short decaying chunks of sound of a given shape
  ## duration is counted in seconds for all shapes

  def mono_generator(self):
    for i, s in zip(count(), super().mono_generator()):
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

def _samples(waves, duration = None, framerate = _framerate):
  left_signal = [w.left_signal() for w in waves]
  right_signal = [w.right_signal() for w in waves]
  if duration is not None:
    duration = duration * framerate
  return compute_samples((left_signal, right_signal), duration)

def write(fpath, waves, duration):
  # fpath : path to write file to
  # waves : waves
  write_wavefile(fpath, samples=_samples(waves, duration), nchannels=2, sampwidth=2, framerate=_framerate, bufsize=2048)
  return
