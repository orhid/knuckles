import logging as log
log.basicConfig(format='%(levelname)s:%(message)s', level=log.DEBUG)
import time

import itertools as itt
import random as rnd

from module import wave as wv
from module import encryptor as ecr

def rnorm(n, mu = 0, sg = 1):
  return (rnd.gauss(mu, sg) for i in range(n))

def runif(n, lo = 0, hi = 1):
  return (rnd.uniform(lo, hi) for i in range(n))

def test():
  _path = 'bounce/test/'

#  space = sorted(list(runif(16)))
  value = sorted(list(rnorm(192)))
  ecr.univar_mono_ns(value, filename=f'{_path}test', shape='sine')
#  ecr.univar_stro_sq_plot(function=lambda x: x*x, filename=f'{_path}test', shape='square')
  return

if __name__ == '__main__':
  log.debug(f'[test] running')
  start = time.time()
  test()
  log.debug(f'[test] completed in time : {time.time()-start:.4f}')
