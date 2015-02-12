import argparse
import pyopencl as cl
import pyopencl.tools
import csv
import numpy
import time
from oclConfigurar import OCLConfigurar, PREFERRED_GPU
from array import array

SIGNAL_BUY          = "Signal to buy"
SIGNAL_SELL         = "Signal to sell"
SIGNAL_BUY_OPP      = "A buying opportunity"
SIGNAL_SELL_OPP     = "A selling opportunity"
SIGNAL_TIME_TO_BUY  = "Buy for short-term technical rise"
SIGNAL_TIME_TO_SELL = "Sell for short-term technical reaction"

TREND_TYPE_DECLINE_FLATTERN  = 0
TREND_TYPE_DECLINE_FALL      = 1
TREND_TYPE_RISING_FLATTERN   = 2
TREND_TYPE_RISING_ADVANCE    = 3

oclConfigurar = OCLConfigurar()

class GranvilleRules:
  # http://www.angelfire.com/sk/mtsp500/granville.html
  # http://www.cnyes.com/twstock/class/Chap4_02.htm
  GRANULARITY = 5
  def __init__(self, lstMA200, lstK):
    # Pass in at least 5 most recent values to calculate the trend
    # Start from the least recent, e.g. lstMA200 = [100, 101, 102, 104, 105]
    # 105 : today, 104 : yesterday, 102 : the day before yesterday ... etc.
    assert(len(lstMA200) == GranvilleRules.GRANULARITY)
    assert(len(lstK) == GranvilleRules.GRANULARITY)
    self.strConclusion = 'Nothing'

    self.nTrendForMA200 = None
    self.nTrendForPrice = None

    self.nTrendForMA200 = self.calcTrend(lstMA200)
    self.nTrendForPrice = self.calcTrend(lstK)
    pass

  def calcTrend(self, lstInput):
    # TODO : is it suitable to calculate trend by slope ?
    #        or use least square method to find a line ?
    for i in xrange(len(lstInput)-1):
      slope = float(lstInput[i+1]-lstInput[i]) / float((i+1)-i)
      print slope
    return None

  def analyze(self):
    pass

  def output(self):
    pass

class Main:
  def __init__(self, options):
    self.options = options
    self.result = []
    self.dicRawData = {} # { idx : row }
    self.dicDatetime2Idx = {} # { Date+Time : idx }, Date+Time is unique string

    self.PriceData = numpy.dtype([('dataIndex', numpy.int), \
                                  ('open', numpy.float32), \
                                  ('high', numpy.float32), \
                                  ('low', numpy.float32), \
                                  ('close', numpy.float32)])


  def prepare(self, program):
    self.context = oclConfigurar.getContext(DEVICE=PREFERRED_GPU)
    self.queue = cl.CommandQueue(self.context)

    # TODO : Should use the device you choose.
    self.PriceData, PriceData_c_decl = cl.tools.match_dtype_to_c_struct(
                                                        self.context.devices[0],
                                                        "PriceData",
                                                        self.PriceData)
    self.PriceData = cl.tools.get_or_register_dtype("PriceData", self.PriceData)

    return self.loadProgram(program)

  def loadProgram(self, program):
    f = open(program, 'r')
    fstr = ''.join(f.readlines())
    f.close()
    return cl.Program(self.context, fstr).build(['-I kernel/'])

  def loadData(self, rawFile):
    ## ?? convert to a better style?
    f = open(rawFile, 'r')
    csvData = csv.DictReader(f)
    self.dicRawData = {}
    self.dicDatetime2Idx = {}
    for idx, row in enumerate(csvData):
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
    print "=" * 10 + "Result in Descending Order" + "=" * 10
    dicTempResult = {}
    # The startIdx is the inlcuded value. But the second parameter of range is
    # excluded value. So, we use -2 to calculate the stop index of range.
    # The perfect stop index is startIdx + calcBase - 2. But we use startIdx - 1
    # to have the same result of Open CL
    for index in range(endIdx, startIdx - 1, -1):
      dicTempResult[index] = {}
      dicTempResult[index]['O'] = 0
      dicTempResult[index]['H'] = 0
      dicTempResult[index]['L'] = 0
      dicTempResult[index]['C'] = 0
      if index >= calcBase:
        for idx in range(calcBase):
          dicTempResult[index]['O'] += float(self.dicRawData[index - idx].get('Open', 0.0))
          dicTempResult[index]['H'] += float(self.dicRawData[index - idx].get('High', 0.0))
          dicTempResult[index]['L'] += float(self.dicRawData[index - idx].get('Low', 0.0))
          dicTempResult[index]['C'] += float(self.dicRawData[index - idx].get('Close', 0.0))

        dicTempResult[index]['O'] /= float(calcBase)
        dicTempResult[index]['H'] /= float(calcBase)
        dicTempResult[index]['L'] /= float(calcBase)
        dicTempResult[index]['C'] /= float(calcBase)

      if (index < 4 or index + 4 > nCount):
        print "%d: AVG Open(%6f)/High(%6f)/Low(%6f)/Close(%6f) " % (index, dicTempResult[index]['O'], dicTempResult[index]['H'], \
          dicTempResult[index]['L'], dicTempResult[index]['C'])
      elif (4 <= index <= 6):
        print "..."

    print "=" * 10 + "Done" + "=" * 10

  def prepareInBufferForOCL(self, sIdx, eIdx):
    # TODO : create input buffer only start from sIdx-Base ~ eIdx for calculation input
    if not self.dicRawData or not self.dicDatetime2Idx: return

    lstRawData = [(k, float(v['Open']), float(v['High']), float(v['Low']), float(v['Close'])) for k, v in self.dicRawData.iteritems() ]
    arrInRawData = numpy.array(lstRawData, dtype=self.PriceData)
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

    arrOutRawData = numpy.zeros(len(self.dicRawData), dtype=self.PriceData)
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
    program = self.prepare('kernel/granville_rule.c')

    inBuff = self.prepareInBufferForOCL(2, 5)
    outBuff = self.prepareOutBufferForOCL(2, 5)

    globalSize = ((len(self.dicRawData) + 15) << 4) >> 4
    nCalculateRange = 5 # Take 5 as exampel

    evt = program.test_donothing(self.queue, (len(self.dicRawData),), None, \
        numpy.int32(nCalculateRange), inBuff.data, outBuff.data)

    # TODO : Using cl.array, we don't need to use cl.enqueu_read_buffer
    print outBuff

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
