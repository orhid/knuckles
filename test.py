import logging as log
log.basicConfig(format='%(levelname)s:%(message)s', level=log.DEBUG)
import time

import random as rnd
import operator

from knuckles import wave as wv
import knuckles as nkl

_path = 'bounce/sonifications/'

def rnorm(n, mu = 0, sg = 1):
  return (rnd.gauss(mu, sg) for i in range(n))

def soni1():
  sn = wv.Plop(shape='sine')
  sw = wv.Plop(shape='saw', offset=0.8)
  sq = wv.Plop(shape='square', offset=1.6)

  sonif = wv.Sonification((sn, sw, sq), duration=2.4, filename=f'{_path}sonification1')
  sonif.render()
  return

def soni2():
  v1 = list(rnorm(12))
  v2 = list(rnorm(12))
  nkl.cmp_nulvar_sq_freq((v1,v2), bounds=(-2,2), filename=f'{_path}sonification2')

def soni3():
  v1 = sorted(list(rnorm(12)))
  v2 = sorted(list(rnorm(12)))
  nkl.cmp_nulvar_sq_freq((v1,v2), bounds=(-2,2), filename=f'{_path}sonification3')

def soni4():
  value = (j/2 for j in range(12))
  nkl.nulvar_sq_freq(value, filename=f'{_path}sonification4')

def soni5():
  time = (j for j in range(12))
  space = (j*2 for j in range(12))
  value = (j/2 for j in range(12))
  nkl.bivar_sq(time, space, value, filename=f'{_path}sonification5')

def soni6():
  data = [{'height': rnd.gauss(144, 12), 'gender': rnd.choice('mw')} for j in range(12)]
  data.sort(key=operator.itemgetter('height'))
  mheight = [d['height'] for d in data if d['gender'] == 'm']
  wheight = [d['height'] for d in data if d['gender'] == 'w']
  msonif = nkl.nulvar_sq_time(mheight, shape='saw', write=False)
  wsonif = nkl.nulvar_sq_time(wheight, shape='heart', write=False)
  sonif = msonif + wsonif
  sonif.render(f'{_path}sonification6')

def test():
  soni6()
  return

if __name__ == '__main__':
  log.debug(f'[test] running')
  start = time.time()
  test()
  log.debug(f'[test] completed in time : {time.time()-start:.4f}')
