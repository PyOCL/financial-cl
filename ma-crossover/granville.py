import math
import numpy
import matplotlib.pyplot as plt

SIGNAL_BUY          = "Signal to buy"
SIGNAL_SELL         = "Signal to sell"
SIGNAL_BUY_OPP      = "A buying opportunity"
SIGNAL_SELL_OPP     = "A selling opportunity"
SIGNAL_TIME_TO_BUY  = "Buy for short-term technical rise"
SIGNAL_TIME_TO_SELL = "Sell for short-term technical reaction"

TREND_TYPE_UNKNOWN           = 0
TREND_TYPE_DECLINE_FLATTERN  = 1
TREND_TYPE_DECLINE_FALL      = 2
TREND_TYPE_RISING_FLATTERN   = 3
TREND_TYPE_RISING_ADVANCE    = 4

class GranvilleRules:
    # http://www.angelfire.com/sk/mtsp500/granville.html
    # http://www.cnyes.com/twstock/class/Chap4_02.htm
    def __init__(self, lstMA, lstPrice):
        # Basically, the larger MA timespan we set, 
        # the more accurate result we'll get.
        # lstMA : the oldest in the beginning, the latest at the end.
        assert (len(lstMA) >= 30)
        assert (len(lstPrice) >= 30)
        self.lstMA = lstMA
        self.lstPrice = lstPrice

        self.strConclusion = 'Nothing'

        self.nTrendForMA = None
        self.nTrendForPrice = None

        self.nTrendForMA = self.calcTrend(self.lstMA)
        self.nTrendForPrice = self.calcTrend(self.lstPrice)
        pass

    def calcTrend(self, lstInput, typeInput=''):
        # Need to test by different input
        # Slope determines the level of gradient, from oldest to latest
        lstSlope = []
        for x in xrange(len(lstInput)):
            if x == 0:
                continue
            s = lstInput[x] - lstInput[x-1]
            lstSlope.append(s)
        
        # Quadratic differential determines concavity, from latest to oldest
        lstConcavity = []
        for x in xrange(len(lstSlope)-1, 0, -1):
            c = lstSlope[x] - lstSlope[x-1]
            lstConcavity.append(c)

        # Default set a span for calculating Concavity MA.
        nFlipIndex = len(lstConcavity) / 3
        nFlipCount = 0
        # To find the first encoutered top or bottom
        for x in xrange(len(lstConcavity)-1):
            if lstConcavity[x] * lstConcavity[x+1] < 0 and nFlipCount < 2:
                nFlipCount += 1
                nFlipIndex = x

        # To calculate the ma-concavity according to these partial samples
        lstMAConcavity = []
        for x in xrange(len(lstConcavity)):
            if x + nFlipIndex > len(lstConcavity):
                continue
            temp = 0
            for y in xrange(nFlipIndex):
                temp += lstConcavity[x+y]
            temp /= float(nFlipIndex)
            lstMAConcavity.append(temp)
        
        # determin the result.
        if math.fabs(lstSlope[-1]) > math.fabs(lstSlope[-2]):
            if lstSlope[-1] > 0 and lstMAConcavity[0] > 0:
                return TREND_TYPE_RISING_ADVANCE
            elif lstSlope[-1] > 0 and lstMAConcavity[0] < 0:
                return TREND_TYPE_RISING_FLATTERN
            elif lstSlope[-1] < 0 and lstMAConcavity[0] > 0:
                return TREND_TYPE_DECLINE_FLATTERN
            else:
                return TREND_TYPE_DECLINE_FALL
        else:
            if lstSlope[-1] > 0 and lstMAConcavity[0] > 0:
                return TREND_TYPE_UNKNOWN
            elif lstSlope[-1] > 0 and lstMAConcavity[0] < 0:
                return TREND_TYPE_RISING_FLATTERN
            elif lstSlope[-1] < 0 and lstMAConcavity[0] > 0:
                return TREND_TYPE_DECLINE_FLATTERN
            else:
                return TREND_TYPE_UNKNOWN
        return TREND_TYPE_UNKNOWN

    def printTrendToMsg(self, nTrend, strTarget=''):
        ret = strTarget + ' : '
        if nTrend == TREND_TYPE_RISING_ADVANCE:
            ret += 'Going up and advancing'
        elif nTrend == TREND_TYPE_RISING_FLATTERN:
            ret += 'Going up and flatterning'
        elif nTrend == TREND_TYPE_DECLINE_FALL:
            ret += 'Going down and falling'
        elif nTrend == TREND_TYPE_DECLINE_FLATTERN:
            ret += 'Going down and flatterning'
        else:
            ret += 'unknown'
        print ret

    def show(self):
        self.printTrendToMsg(self.nTrendForMA, '(Red) MA')
        self.printTrendToMsg(self.nTrendForPrice, '(Blue) Price')
        plt.plot(self.lstMA, 'r', self.lstPrice, 'b')
        plt.ylabel("Values")
        plt.show()
