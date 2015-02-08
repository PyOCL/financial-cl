import argparse
import pyopencl as cl
import pyopencl.tools
import csv
import numpy
import time
from array import array

class Main:
  def __init__(self, options):
    self.options = options
    self.result = []
    self.dicRawData = {} # { idx : row }
    self.dicDatetime2Idx = {} # { Date+Time : idx }, Date+Time is unique string

    self.stRawData = numpy.dtype([('f1', numpy.int), \
                                  ('f2', numpy.float), \
                                  ('f3', numpy.float), \
                                  ('f4', numpy.float), \
                                  ('f5', numpy.float)])

  def prepare(self, program):
    self.context = cl.create_some_context()
    self.queue = cl.CommandQueue(self.context)

    # TODO : Should use the device you choose.
    self.stRawData, stRawData_c_decl = cl.tools.match_dtype_to_c_struct(self.context.devices[0], \
      "stRawData", self.stRawData)
    self.stRawData = cl.tools.get_or_register_dtype("stRawData", self.stRawData)
    #print "self.stRawData : ", self.stRawData
    #print "stRawData_c_decl : ", stRawData_c_decl

    return self.loadProgram(program)

  def loadProgram(self, program):
    f = open(program, 'r')
    fstr = ''.join(f.readlines())
    f.close()
    return cl.Program(self.context, fstr).build()

  def loadData(self, rawFile):
    ## ?? convert to a better style?
    f = open(rawFile, 'r')
    csvData = csv.DictReader(f)
    self.dicRawData = {}
    self.dicDatetime2Idx = {}
    for idx, row in enumerate(csvData):
      #print '{} {} {} {} {} {}'.format(row['Date'], row['Time'], row['Open'], row['High'], row['Low'], row['Close'])
      self.dicRawData[idx] = row
      self.dicDatetime2Idx[row['Date']+row['Time']] = idx
    print "Number of Row : %d " %(len(self.dicRawData))
    f.close()

  def calcualteAVG(self, startIdx, endIdx, calcBase):
    #     | ..... |
    #     s       e   <== index
    #  |..|   <== base
    if startIdx > endIdx: return
    if endIdx >= len(self.dicRawData):
      endIdx = len(self.dicRawData) - 1

    nCount = endIdx+1 - startIdx
    dicTempResult = {}
    for index in xrange(startIdx, endIdx+1):
      #print "index : %d" %(index)

      lstIndice = [index-i for i in xrange(calcBase) if index-i >= 0]
      for idx in lstIndice:
        vOpen = float(self.dicRawData[idx].get('Open', 0.0))
        vHigh = float(self.dicRawData[idx].get('High', 0.0))
        vLow = float(self.dicRawData[idx].get('Low', 0.0))
        vClose = float(self.dicRawData[idx].get('Close', 0.0))
        #print " idx : %d - open(%f)/high(%f)/low(%f)/close(%f)" %(idx, vOpen, vHigh, vLow, vClose)
        dicTempResult[index]['O'] = dicTempResult.setdefault(index, {}).setdefault('O', 0.0) + vOpen
        dicTempResult[index]['H'] = dicTempResult.setdefault(index, {}).setdefault('H', 0.0) + vHigh
        dicTempResult[index]['L'] = dicTempResult.setdefault(index, {}).setdefault('L', 0.0) + vLow
        dicTempResult[index]['C'] = dicTempResult.setdefault(index, {}).setdefault('C', 0.0) + vClose

      dicTempResult[index]['O'] /= float(len(lstIndice))
      dicTempResult[index]['H'] /= float(len(lstIndice))
      dicTempResult[index]['L'] /= float(len(lstIndice))
      dicTempResult[index]['C'] /= float(len(lstIndice))

      if (index < 4 or index + 4 > nCount):
        print " AVG Open(%6f)/High(%6f)/Low(%6f)/Close(%6f) " %(dicTempResult[index]['O'], dicTempResult[index]['H'], \
          dicTempResult[index]['L'], dicTempResult[index]['C'])
      elif (4 <= index < 6):
        print "..."

    print "=" * 10 + "Done" + "=" * 10

  def prepareInBufferForOCL(self, sIdx, eIdx):
    # TODO : create input buffer only start from sIdx-Base ~ eIdx for calculation input
    if not self.dicRawData or not self.dicDatetime2Idx: return

    lstRawData = [(k, float(v['Open']), float(v['High']), float(v['Low']), float(v['Close'])) for k, v in self.dicRawData.iteritems() ]
    arrInRawData = numpy.array(lstRawData, dtype=self.stRawData)
    print "arrInRawData : ", arrInRawData
    print "arrInRawData.shape : ", arrInRawData .shape

    # Use cl.Buffer
    #bufInRaw = cl.Buffer(self.context, cl.mem_flags.READ_ONLY | \
    #  cl.mem_flags.USE_HOST_PTR, hostbuf=arrInRawData)

    # Use cl.array
    arrayIn = cl.array.to_device(self.queue, arrInRawData)
    return arrayIn

  def prepareOutBufferForOCL(self, sIdx, eIdx):
    # TODO : create output buffer with a size (eIdx-sIdx+1) for storeing result
    if not self.dicRawData or not self.dicDatetime2Idx: return

    arrOutRawData = numpy.zeros(len(self.dicRawData), dtype=self.stRawData)
    print "arrOutRawData : ", arrOutRawData
    print "arrOutRawData.shape : ", arrOutRawData .shape

    # Use cl.Buffer 
    #bufOutRaw = cl.Buffer(self.context, cl.mem_flags.WRITE_ONLY | \
    #  cl.mem_flags.USE_HOST_PTR, hostbuf=arrOutRawData)
    #return bufOutRaw

    # Use cl.array
    arrayOut = cl.array.to_device(self.queue, arrOutRawData)
    return arrayOut

  def run(self):
    program = self.prepare('ma.c')

    inBuff = self.prepareInBufferForOCL(2, 5)
    outBuff = self.prepareOutBufferForOCL(2, 5)

    globalSize = ((len(self.dicRawData) + 15) << 4) >> 4
    nCalculateRange = 5 # Take 5 as exampel

    evt = program.test_donothing(self.queue, (len(self.dicRawData),), None, \
        numpy.int32(nCalculateRange), inBuff.data, outBuff.data)

    # TODO : Using cl.array, we don't need to use cl.enqueu_read_buffer
    print outBuff

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

  time1 = time.time()
  rawData = m.loadData(args.input)
  print " Data preparation takes : %f sec."%(time.time()-time1)
  print "=" * 20

  time2 = time.time()
  m.calcualteAVG(0, len(m.dicRawData), 5)  # int(args.sidx), int(args.eidx), int(args.base)
  time3 = time.time()
  print " CPU takes : %f sec."%(time3-time2)
  print "=" * 20
  result = m.run()
  print " GPU takes : %f sec."%(time.time()-time3)
  print "=" * 20

  # print '=' * 40
  # print 'MA Result:'
  # for data in result:
  #   print '{} - {}: {:0.4f}'.format(data['date'], data['time'], data['ma'])
  # print '=' * 40