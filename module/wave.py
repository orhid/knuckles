import math
import struct
from itertools import count, islice, zip_longest
from numpy import sign

import module._wav as wv

## useful maths

def shelf(x, length, rate=1/3):
  # note to self: change this to a proper bump function
  return math.exp(x/(length*rate))

## fool proofing
  ## functions that check if all attributes are inside their given range

def fool_amplitude(amplitude):
  return max(0, min(amplitude, 1))

## base waves

def sine_wave(frequency=440.0, amplitude=1/6, framerate=48000, skip_frame=0):
  amplitude = fool_amplitude(amplitude)
  for i in count(skip_frame):
    yield float(amplitude) * math.sin(math.tau * float(frequency) * float(i) / float(framerate))
   
def square_wave(frequency=440.0, amplitude=1/6, framerate=48000, skip_frame=0):
  amplitude = fool_amplitude(amplitude)
  for i in count(skip_frame):
    yield float(amplitude) * sign(math.sin(math.tau * float(frequency) * float(i) / float(framerate)))

def saw_wave(frequency=440.0, amplitude=1/6, framerate=48000, skip_frame=0):
  amplitude = fool_amplitude(amplitude)
  for i in count(skip_frame):
    yield float(amplitude) * (-2 / math.pi) * math.atan(1/math.tan(math.pi * float(frequency) * float(i) / float(framerate)))

## blips
  ## short chunks of sound of a given shape
  ## duration is counted in seconds for all shapes

def blip(wave='sine', frequency=440.0, amplitude=1/6, framerate=48000, duration=1):
  return islice(globals()[f'{wave}_wave'](frequency, amplitude, framerate), duration*framerate)

## plops
  ## short decaying chunks of sound of a given shape

def plop(wave='sine', frequency=440.0, amplitude=1/6, framerate=48000, duration=1):
  for i, s in zip(count, blip(wave, frequency, amplitue, framerate, duration)):
    yield s * shelf(i, duration*framerate)

## wav creation

def grouper(n, iterable, fillvalue=None):
  # grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx
  
  args = [iter(iterable)] * n
  return zip_longest(fillvalue=fillvalue, *args)

def sum_samples(waves, nsamples=None):
  # create a generator which creates a sequence of the sum of each wave at each sample
#  if len(waves)
  return islice(map(sum, zip(*waves)), nsamples)

def write_wavefile(f, samples, nframes=None, nchannels=1, sampwidth=4, framerate=48000, bufsize=2048):
  # f is the filepath
  # samples is an array of values for every sample
  if nframes is None:
    nframes = 0
    
  w = wv.open(f, 'wb')
  w.setparams((nchannels, sampwidth, framerate, nframes, 'NONE', 'not compressed'))
  
  max_amplitude = float(int((2 ** (sampwidth * 8)) / 2) - 1)
  
  # split the samples into chunks (to reduce memory consumption and improve performance)
  for chunk in grouper(bufsize, samples):
    frames = b''.join(struct.pack('i', int(max_amplitude * sample)) for sample in chunk if sample is not None)
    w.writeframesraw(frames)
    
  w.close()
  return
