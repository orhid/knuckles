import math
import struct
from itertools import count, islice, zip_longest

import module._wav as wv

## base waves

def sine_wave(frequency=440.0, amplitude=1/6, framerate=96000, skip_frame=0):
  if amplitude > 1.0: amplitude = 1.0
  if amplitude < 0.0: amplitude = 0.0
  for i in count(skip_frame):
    sine = math.sin(2.0 * math.pi * float(frequency) * (float(i) / float(framerate)))
    yield float(amplitude) * sine
    
def damp_wave(wave, rate=1, framerate=96000):
  for frame, sample in enumerate(wave):
    yield sample*math.exp(-frame*rate/framerate)
    
## wav creation

def grouper(n, iterable, fillvalue=None):
  # grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx
  
  args = [iter(iterable)] * n
  return zip_longest(fillvalue=fillvalue, *args)

def compute_samples(waves, nsamples=None):
  # create a generator which creates a sequence of the sum of each wave at each sample
#  if len(waves)
  return islice(map(sum, zip(*waves)), nsamples)

def write_wavefile(f, samples, nframes=None, nchannels=1, sampwidth=4, framerate=96000, bufsize=2048):
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
