import math
import numpy
import matplotlib.pyplot as plt

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

class GranvilleRules:
    # http://www.angelfire.com/sk/mtsp500/granville.html
    # http://www.cnyes.com/twstock/class/Chap4_02.htm
    def __init__(self, lstMA, lstPrice):
        # Basically, the larger MA timespan we set, 
        # the more accurate result we'll get.
        assert (len(lstMA) >= 30)
        self.lstMA = lstMA
        self.strConclusion = 'Nothing'

        self.nTrendForMA = None
        self.nTrendForPrice = None

        self.nTrendForMA = self.calcTrend(lstMA)
        pass

    def calcTrend(self, lstInput):
        # Need to test by different input
        # Slope determines the level of gradient
        lstSlope = []
        for x in xrange(len(lstInput)):
            if x == 0:
                continue
            s = lstInput[x] - lstInput[x-1]
            lstSlope.append(s)
        
        # Quadratic differential determines concavity
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

        # To calculate the concavity according to this partial samples
        lstMAConcavity = []
        for x in xrange(len(lstConcavity)):
            if x + nFlipIndex > len(lstConcavity):
                continue
            temp = 0
            for y in xrange(nFlipIndex):
                temp += lstConcavity[x]
            temp /= float(nFlipIndex)
            lstMAConcavity.append(temp)
        
        # determin the result.
        if math.fabs(lstSlope[-1]) > math.fabs(lstSlope[-2]):
            if lstSlope[-1] > 0 and lstMAConcavity[0] > 0:
                print "=> Going Up and Advancing "
            elif lstSlope[-1] > 0 and lstMAConcavity[0] < 0:
                print "=> Going Up and Flatterning "
            elif lstSlope[-1] < 0 and lstMAConcavity[0] > 0:
                print "=> Going Down and Flatterning "
            else:
                print "=> Going Down and Falling "
        else:
            if lstSlope[-1] > 0 and lstMAConcavity[0] > 0:
                print "=> ... seems imposssible"
            elif lstSlope[-1] > 0 and lstMAConcavity[0] < 0:
                print "=> Going Up and Flatterning "                
            elif lstSlope[-1] < 0 and lstMAConcavity[0] > 0:
                print "=> Going Down and Flatterning "
            else:
                print "=> ... seems imposssible"
                
        return None

    def show(self):
        plt.plot(self.lstMA, 'r--')
        plt.ylabel("MA")
        plt.show()
