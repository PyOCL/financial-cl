import argparse
import pyopencl as cl
import csv
from time import time
from array import array

class Main:
  def __init__(self, options):
    self.options = options
    self.result = []

  def prepare(self, program):
    self.context = cl.create_some_context()
    self.queue = cl.CommandQueue(self.context)

  def loadProgram(self, program):
    f = open(program, 'r')
    fstr = ''.join(f.readlines())
    f.close()
    return cl.Program(self.context, fstr).build()

  def loadData(self, rawFile):
    ## ?? convert to a better style?
    f = open(rawFile, 'r')
    for row in csv.DictReader(f):
      print '{} {} {} {} {} {}'.format(row['Date'], row['Time'], row['Open'], row['High'], row['Low'], row['Close'])
    f.close()

  def run(self):
    program = self.prepare('ma.c')
    ##?? load csv

    ## create buffer for input

    ## create buffer for output

    ## run program

    ## read data back
    return self.result

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Calculate the MA cross over date and direction')
  parser.add_argument('--input', help='the input file')
  parser.add_argument('--timespan', help='the time span to calculate MA 1', default=5)
  args = parser.parse_args()
  m = Main(args)

  rawData = m.loadData(args.input)

  # result = m.run()

  # print '=' * 40
  # print 'MA Result:'
  # for data in result:
  #   print '{} - {}: {:0.4f}'.format(data['date'], data['time'], data['ma'])
  # print '=' * 40