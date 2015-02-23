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
        # lstMA : the latest in the beginning, the oldest at the end.
        # lstPrice : the latest in the beginning, the oldest at the end.
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

    def calculate(self):
        lstEMA = []
        addEMA = lstEMA.append
        self.lstPrice.reverse()
        for idx in xrange(len(self.lstPrice)):
            if idx == 0:
                addEMA(self.lstMA[-1])
            else:
                addEMA(lstEMA[idx-1] + (self.lstPrice[idx] - lstEMA[idx-1]) * self.weight)
        
        log_ema("lstEMA: ", lstEMA)
        pass 
