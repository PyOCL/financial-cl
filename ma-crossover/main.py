import argparse
import pyopencl as cl
import pyopencl.tools
import csv
import numpy
import time
from oclConfigurar import OCLConfigurar, PREFERRED_GPU
from array import array

oclConfigurar = OCLConfigurar()

TEST_GRANVILLE = 0
TEST_EMA = 0

class Main:
    def __init__(self, options):
        self.options = options
        self.result = []
        self.dicRawData = {} # { idx : row }
        self.dicDatetime2Idx = {} # { Date+Time : idx }, Date+Time is unique string

        self.dicTempResultMA_CPU = {}
        self.dicTempResultMA_GPU = {}

        self.PriceData = numpy.dtype([('dataIndex', numpy.int), \
                                      ('open', numpy.float32), \
                                      ('high', numpy.float32), \
                                      ('low', numpy.float32), \
                                      ('close', numpy.float32)])

        # TODO : parse args and save them to specific variables
        self.srcFile = "../data/gold-sample-data.txt"   # options.input
        self.startDataTime = "07/16/20080140"           # options.start
        self.endDataTime = "09/17/20120405"             # options.end
        self.timespan = 5                               # options.timespan

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
        self.dicTempResultMA_CPU = {}
        # The startIdx is the inlcuded value. But the second parameter of range is
        # excluded value. So, we use -2 to calculate the stop index of range.
        # The perfect stop index is startIdx + self.timespan - 2. But we use startIdx - 1
        # to have the same result of Open CL
        lst30MA = []
        count = 0
        for index in xrange(endIdx, startIdx - 1, -1):
            self.dicTempResultMA_CPU[index] = {}
            self.dicTempResultMA_CPU[index]['O'] = 0
            self.dicTempResultMA_CPU[index]['H'] = 0
            self.dicTempResultMA_CPU[index]['L'] = 0
            self.dicTempResultMA_CPU[index]['C'] = 0
            if index >= self.timespan:
                for idx in xrange(self.timespan):
                    self.dicTempResultMA_CPU[index]['O'] += float(self.dicRawData[index - idx].get('Open', 0.0))
                    self.dicTempResultMA_CPU[index]['H'] += float(self.dicRawData[index - idx].get('High', 0.0))
                    self.dicTempResultMA_CPU[index]['L'] += float(self.dicRawData[index - idx].get('Low', 0.0))
                    self.dicTempResultMA_CPU[index]['C'] += float(self.dicRawData[index - idx].get('Close', 0.0))

                self.dicTempResultMA_CPU[index]['O'] /= float(self.timespan)
                self.dicTempResultMA_CPU[index]['H'] /= float(self.timespan)
                self.dicTempResultMA_CPU[index]['L'] /= float(self.timespan)
                self.dicTempResultMA_CPU[index]['C'] /= float(self.timespan)

            if (endIdx - index < 5 or index - startIdx < 5):
                print "%d: AVG Open(%6f)/High(%6f)/Low(%6f)/Close(%6f) "\
                %(index, self.dicTempResultMA_CPU[index]['O'], self.dicTempResultMA_CPU[index]['H'], \
                  self.dicTempResultMA_CPU[index]['L'], self.dicTempResultMA_CPU[index]['C'])
            elif (10 <= endIdx - index <= 12):
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
        realSize = endIdx - startIdx + self.timespan
        globalSize = ((realSize + 15) << 4) >> 4

        evt = program.test_donothing(self.queue, (globalSize,), None, \
            numpy.uint32(self.timespan), numpy.uint32(realSize), \
            oclArrayIn.data, oclArrayOut.data)

        # TODO : Using cl.array, we don't need to use cl.enqueu_read_buffer
        out = oclArrayOut.get()
        print "==========Result by OpenCL=========="
        print out
        return self.result

    def testStuff(self):
        if TEST_GRANVILLE:
            self.__testGranville(self.endDataTime)
        if TEST_EMA:
            self.__testEMA(self.endDataTime)

    def __convertTypeToRawType(self, strType):
        if strType == 'O':
            return 'Open'
        elif strType == 'L':
            return 'Low'
        elif strType == 'H':
            return 'High'
        else:
            return 'Close'

    def __testGranville(self, strDateTime, strType='O'):
        # Normally, I think the strDateTime shoul be the self.endDataTime
        # Since we're trying to calculate the latest trend. Isn't it ?
        # type : 'O', 'C', 'H', 'L'
        targetIdx = self.dicDatetime2Idx.get(strDateTime, -1)
        assert not (self.timespan < 30), "Need a timespan >= 30 for Granville test."
        assert not (targetIdx == -1), "Incorrect input datetime."
        assert not (targetIdx not in self.dicTempResultMA_CPU), "Target datetime not in current temp result."

        strTypeForRaw = self.__convertTypeToRawType(strType)

        lstMA = []
        lstPrice = []
        for idx in xrange(targetIdx-self.timespan+1, targetIdx+1):
            lstMA.append(self.dicTempResultMA_CPU[idx][strType])
            lstPrice.append(float(self.dicRawData[idx][strTypeForRaw]))
        from granville import GranvilleRules
        gr = GranvilleRules(lstMA, lstPrice)
        gr.show()

    def __testEMA(self, strDateTime, strType='O'):
        targetIdx = self.dicDatetime2Idx.get(strDateTime, -1)
        assert not (targetIdx == -1), "Incorrect input datetime."
        assert not (targetIdx not in self.dicTempResultMA_CPU), "Target datetime not in current temp result."

        strTypeForRaw = self.__convertTypeToRawType(strType)

        lstMA = []
        lstPrice = []
        for idx in xrange(targetIdx-self.timespan+1, targetIdx+1):
            lstMA.append(self.dicTempResultMA_CPU[idx][strType])
            lstPrice.append(float(self.dicRawData[idx][strTypeForRaw]))

        from ema import EMA
        ema = EMA(lstMA, lstPrice, self.timespan)
        ema.calculate()
        ema.show()

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
    m.testStuff()
