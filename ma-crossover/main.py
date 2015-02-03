import argparse
import pyopencl as cl
import csv
from time import time
from array import array

class Main:
  def __init__(self, options):
    self.options = options
    self.result = []
    self.dicRawData = {} # { idx : row}

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
    csvData = csv.DictReader(f)
    for idx, row in enumerate(csvData):
      print '{} {} {} {} {} {}'.format(row['Date'], row['Time'], row['Open'], row['High'], row['Low'], row['Close'])
      self.dicRawData.setdefault(idx, row)
    print "Number of Row : %d " %(len(self.dicRawData))
    f.close()

  def calcualteAVG(self, startIdx, endIdx, calcBase):
    #     | ..... |
    #     s       e   <== index
    #  |..|   <== base
    if startIdx > endIdx: return
    if endIdx >= len(self.dicRawData):
      endIdx = len(self.dicRawData) - 1

    dicTempResult = {}
    for index in xrange(startIdx, endIdx+1):
      print "index : %d" %(index)

      lstIndice = [index-i for i in xrange(calcBase) if index-i >= 0]
      for idx in lstIndice:
        vOpen = float(self.dicRawData[idx].get('Open', 0.0))
        vHigh = float(self.dicRawData[idx].get('High', 0.0))
        vLow = float(self.dicRawData[idx].get('Low', 0.0))
        vClose = float(self.dicRawData[idx].get('Close', 0.0))
        print " idx : %d - open(%f)/high(%f)/low(%f)/close(%f)" %(idx, vOpen, vHigh, vLow, vClose)
        dicTempResult[index]['O'] = dicTempResult.setdefault(index, {}).setdefault('O', 0.0) + vOpen
        dicTempResult[index]['H'] = dicTempResult.setdefault(index, {}).setdefault('H', 0.0) + vHigh
        dicTempResult[index]['L'] = dicTempResult.setdefault(index, {}).setdefault('L', 0.0) + vLow
        dicTempResult[index]['C'] = dicTempResult.setdefault(index, {}).setdefault('C', 0.0) + vClose

      dicTempResult[index]['O'] /= float(len(lstIndice))
      dicTempResult[index]['H'] /= float(len(lstIndice))
      dicTempResult[index]['L'] /= float(len(lstIndice))
      dicTempResult[index]['C'] /= float(len(lstIndice))
      print " AVG Open : %f " %(dicTempResult[index]['O'])
      print " AVG High : %f " %(dicTempResult[index]['H'])
      print " AVG Low : %f " %(dicTempResult[index]['L'])
      print " AVG Close : %f " %(dicTempResult[index]['C'])
      print "=" * 20

    print dicTempResult

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
  parser.add_argument('--sidx', help='start Index')
  parser.add_argument('--eidx', help='end Index')
  parser.add_argument('--base', help='calc base')
  parser.add_argument('--timespan', help='the time span to calculate MA 1', default=5)
  args = parser.parse_args()
  m = Main(args)

  rawData = m.loadData(args.input)
  m.calcualteAVG(int(args.sidx), int(args.eidx), int(args.base))
  # result = m.run()

  # print '=' * 40
  # print 'MA Result:'
  # for data in result:
  #   print '{} - {}: {:0.4f}'.format(data['date'], data['time'], data['ma'])
  # print '=' * 40