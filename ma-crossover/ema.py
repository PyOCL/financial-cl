DEBUG = 1

# http://www.moneydj.com/KMDJ/Wiki/wikiViewer.aspx?keyid=23a3c55b-de94-4731-911e-e814469dd2c7
# Calc 10MA, 10EMA @ day 20
# =============================================
# 0 -----------10----------20---------------200, Price
#              10----------20, # 10 MA
#              10----------20, # 10 EMA

def safe_str(obj):
    try:
        return str(obj)
    except UnicodeEncodeError:
        # obj is unicode
        return unicode(obj).encode('unicode_escape') 

def log_ema(*args):
    if DEBUG:
        result = ''
        for x in iter(args):
            result += safe_str(x)
        print result

class EMA:
    def __init__(self, lstMA, lstPrice, aValue, timeBased=True):
        # aValue : Should be the same as timespan
        # lstMA : the oldest in the beginning, the latest at the end.
        # lstPrice : the oldest in the beginning, the latest at the end.
        assert not (len(lstMA) <= 0), "No MA list"
        assert not (len(lstPrice) <= 0), "No Price list"

        self.weight = None
        if timeBased:
            assert (aValue > 0), "aValue for EMA must be greater than 1"
            self.weight = 2.0 / (aValue + 1)
        else:
            assert (0 < aValue <= 1.0), "aValue for EMA must be in 0 ~ 1.0"
            timePeriods = (2.0 / aValue) - 1
            self.weight = 2.0 / (timePeriods + 1)
        
        log_ema("EMA - Weight = %f"%(self.weight))

        self.lstMA = lstMA
        self.lstPrice = lstPrice
        self.lstEMA = []

    def calculate(self):
        self.lstEMA = []
        addEMA = self.lstEMA.append
        for idx in xrange(len(self.lstPrice)):
            if idx == 0:
                addEMA(self.lstMA[idx])
            else:
                addEMA(self.lstEMA[idx-1] + (self.lstPrice[idx] - self.lstEMA[idx-1]) * self.weight)
        
        log_ema("lstEMA: ", self.lstEMA)
        pass

    def show(self):
        import matplotlib.pyplot as plt
        plt.plot(self.lstEMA, 'r')
        plt.ylabel("Values")
        plt.show()
