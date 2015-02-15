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
    GRANULARITY = 20
    def __init__(self, lstMA200, lstK):
        # Pass in at least 5 most recent values to calculate the trend
        # Start from the least recent, e.g. lstMA200 = [100, 101, 102, 104, 105]
        # 105 : today, 104 : yesterday, 102 : the day before yesterday ... etc.
        #assert(len(lstMA200) == GranvilleRules.GRANULARITY)
        #assert(len(lstK) == GranvilleRules.GRANULARITY)
        self.strConclusion = 'Nothing'

        self.nTrendForMA200 = None
        self.nTrendForPrice = None

        self.nTrendForMA200 = self.calcTrend(lstMA200)
        self.nTrendForPrice = self.calcTrend(lstK)
        pass

    def calcTrend(self, lstInput):
        # TODO : is it suitable to calculate trend by slope ?
        #        or use least square method to find a line ?
        x = numpy.array([i for i in xrange(GranvilleRules.GRANULARITY)])
        y = numpy.array(lstInput)
        z = numpy.polyfit(x, y, 2)
        p = numpy.poly1d(z)
        t = p(GranvilleRules.GRANULARITY)
        print "t = p(5) = %f"%(t)
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

        # TODO : parse args and save them to specific variables
        self.srcFile = "../data/gold-sample-data.txt"  # options.input
        self.startDataTime = "07/16/20080140"          # options.start
        self.endDataTime = "09/17/20120405"            # options.end
        self.timespan = 5                              # options.timespan

        print "Loading data ..."
        time1 = time.time()
        self.__loadData()
        print "Data preparation takes : %f sec."%(time.time()-time1)
        print "=" * 20

    def __loadData(self):
        ## ?? convert to a better style?
        f = open(self.srcFile, 'r')
        csvData = csv.DictReader(f)
        self.dicRawData = {}
        self.dicDatetime2Idx = {}
        for idx, row in enumerate(csvData):
            self.dicRawData[idx] = row
            self.dicDatetime2Idx[row['Date']+row['Time']] = idx
        print "Number of Row : %d " %(len(self.dicRawData))
        f.close()

    def prepare(self, program):
        self.context = oclConfigurar.getContext(DEVICE=PREFERRED_GPU)
        self.queue = cl.CommandQueue(self.context)

        PriceData, PriceData_c_decl = cl.tools.match_dtype_to_c_struct(
                                                            self.context.devices[0],
                                                            "PriceData",
                                                            self.PriceData)
        self.PriceData = cl.tools.get_or_register_dtype("PriceData", PriceData)
        return self.loadProgram(program)

    def loadProgram(self, program):
        f = open(program, 'r')
        fstr = ''.join(f.readlines())
        f.close()
        return cl.Program(self.context, fstr).build(['-I kernel/'])

    def calcualteAVG(self):
        # startIdx, endIdx, self.timespan
        #     | ..... |
        #     s       e   <== index
        #  |..|   <== base

        startIdx = self.dicDatetime2Idx.get(self.startDataTime, -1)
        endIdx = self.dicDatetime2Idx.get(self.endDataTime, -1)
        print "Calculate MA(%d) from %s(%d) to %s(%d) - CPU version "\
            %(self.timespan, self.startDataTime, startIdx, self.endDataTime, endIdx)

        if startIdx > endIdx or startIdx < 0 or endIdx < 0: return

        print "=" * 10 + "Result in Descending Order" + "=" * 10
        dicTempResult = {}
        # The startIdx is the inlcuded value. But the second parameter of range is
        # excluded value. So, we use -2 to calculate the stop index of range.
        # The perfect stop index is startIdx + self.timespan - 2. But we use startIdx - 1
        # to have the same result of Open CL
        for index in xrange(endIdx, startIdx - 1, -1):
            dicTempResult[index] = {}
            dicTempResult[index]['O'] = 0
            dicTempResult[index]['H'] = 0
            dicTempResult[index]['L'] = 0
            dicTempResult[index]['C'] = 0
            if index >= self.timespan:
                for idx in xrange(self.timespan):
                    dicTempResult[index]['O'] += float(self.dicRawData[index - idx].get('Open', 0.0))
                    dicTempResult[index]['H'] += float(self.dicRawData[index - idx].get('High', 0.0))
                    dicTempResult[index]['L'] += float(self.dicRawData[index - idx].get('Low', 0.0))
                    dicTempResult[index]['C'] += float(self.dicRawData[index - idx].get('Close', 0.0))

                dicTempResult[index]['O'] /= float(self.timespan)
                dicTempResult[index]['H'] /= float(self.timespan)
                dicTempResult[index]['L'] /= float(self.timespan)
                dicTempResult[index]['C'] /= float(self.timespan)

            if (endIdx - index < 4 or index - startIdx < 4):
                print "%d: AVG Open(%6f)/High(%6f)/Low(%6f)/Close(%6f) "\
                %(index, dicTempResult[index]['O'], dicTempResult[index]['H'], \
                  dicTempResult[index]['L'], dicTempResult[index]['C'])
            elif (4 <= endIdx - index <= 6):
                print "..."

        print "=" * 10 + "Done" + "=" * 10

    def __prepareInBufferForOCL(self, sIdx, eIdx):
        if not self.dicRawData or not self.dicDatetime2Idx: return
        print "-" * 10

        lstRawData = []
        addData = lstRawData.append
        for k, v in self.dicRawData.iteritems():
            if (sIdx - self.timespan + 1) <= k <= eIdx:
              addData((k, float(v['Open']), float(v['High']), float(v['Low']), float(v['Close'])))
        clArrayIn = oclConfigurar.createOCLArrayForInput(self.queue, self.PriceData, lstRawData)

        print "Lenght of Input : %d"%(len(lstRawData))
        print "Input : ",clArrayIn
        return clArrayIn

    def __prepareOutBufferForOCL(self, sIdx, eIdx):
        if not self.dicRawData or not self.dicDatetime2Idx: return
        print "-" * 10

        sizeOut = eIdx - sIdx + self.timespan
        clArrayOut = oclConfigurar.createOCLArrayEmpty(self.queue, self.PriceData, sizeOut)
        print "Lenght of Output : %d"%(sizeOut)
        print "Output : ",clArrayOut
        return clArrayOut

    def run(self):
        startIdx = self.dicDatetime2Idx.get(self.startDataTime, -1)
        endIdx = self.dicDatetime2Idx.get(self.endDataTime, -1)
        assert not (startIdx > endIdx or startIdx < 0 or endIdx < 0), "StartTime or EndTime incorrect !!"

        program = self.prepare('kernel/granville_rule.c')

        oclArrayIn = self.__prepareInBufferForOCL(startIdx, endIdx)
        oclArrayOut = self.__prepareOutBufferForOCL(startIdx, endIdx)
        globalSize = (((endIdx - startIdx + self.timespan) + 15) << 4) >> 4

        evt = program.test_donothing(self.queue, (len(self.dicRawData),), None, \
            numpy.int32(self.timespan), oclArrayIn.data, oclArrayOut.data)

        # TODO : Using cl.array, we don't need to use cl.enqueu_read_buffer
        out = oclArrayOut.get()
        print "==========Result by OpenCL=========="
        print out

        #lstTemp = [out[x][1] for x in xrange(-1, -21, -1)]
        #print lstTemp
        #gr = GranvilleRules(lstTemp, lstTemp)
        return self.result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Calculate the MA cross over date and direction')
    parser.add_argument('--input', help='the input file')
    parser.add_argument('--start', help='the target start date time for MA')
    parser.add_argument('--end', help='the target end date time for MA')
    parser.add_argument('--timespan', help='the time span to calculate MA 1', default=5)

    args = parser.parse_args()

    m = Main(args)

    time2 = time.time()
    m.calcualteAVG()
    time3 = time.time()
    print " CPU takes : %f sec."%(time3-time2)
    print "=" * 20
    result = m.run()
    print " GPU takes : %f sec."%(time.time()-time3)
    print "=" * 20
