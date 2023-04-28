from AlgorithmImports import *
from datetime import timedelta, datetime
import time
import requests
import decimal

td = 'minutes'
tdFast = 2
tdSlow = 5
tdExtraSlow = 10
maxPeriod = 2
maxAtr   = 0.2
minAtr = 0.05


class SymbolData(object):
    

    def __init__(self, algorithm, symbol):


        # fast HA
        # rolling window 1 min HA
        self.ha = HeikinAshi(symbol)
        self.ha_high_window = RollingWindow[Decimal](4)
        self.ha_close_window = RollingWindow[Decimal](4)
        self.ha_open_window = RollingWindow[Decimal](4)
           

        # fast HA registration
        algorithm.RegisterIndicator(symbol, self.ha, timedelta(**{td : tdFast}))
        self.ha.Updated += self.HighHaUpdated
        self.ha.Updated += self.CloseFastHaUpdated
        self.ha.Updated += self.OpenFastHaUpdated
        
        self.atr = AverageTrueRange(symbol, 14)
        algorithm.RegisterIndicator(symbol, self.atr, timedelta(**{td : tdFast}))
        
        self.atrSlow = AverageTrueRange(symbol, 14)
        algorithm.RegisterIndicator(symbol, self.atrSlow, timedelta(**{td : tdSlow}))
        
        # slow HA
        # rolling window slow HA
        self.haSlow = HeikinAshi(symbol)
        self.haSlow_high_window = RollingWindow[Decimal](4)
        self.haSlow_close_window = RollingWindow[Decimal](4)
        
        # slow HA registration
        algorithm.RegisterIndicator(symbol, self.haSlow, timedelta(**{td : tdSlow}))

        self.haSlow.Updated += self.SlowHighHaUpdated
        self.haSlow.Updated += self.SlowCloseHaUpdated
        
        
        # extra slow HA
        self.haExtraSlow = HeikinAshi(symbol)
        self.haExtraSlow_high_window = RollingWindow[Decimal](4)
        self.haExtraSlow_close_window = RollingWindow[Decimal](4)
        
        # extra slow HA registration
        algorithm.RegisterIndicator(symbol, self.haExtraSlow, timedelta(**{td : tdExtraSlow}))

        self.haExtraSlow.Updated += self.ExtraSlowHighHaUpdated
        self.haExtraSlow.Updated += self.ExtraSlowCloseHaUpdated


        # Schaff incidcators
        self.stcFast = SchaffTrendCycle(5, 9, 21)
        self.stcFast_window = RollingWindow[Decimal](5)
        algorithm.RegisterIndicator(symbol, self.stcFast, timedelta(**{td : tdFast}))
        
        self.stcFast.Updated += self.stcFastUpdated
    
        
        self.stcSlow = SchaffTrendCycle(5, 9, 21)
        self.stcSlow_window = RollingWindow[Decimal](5)
        algorithm.RegisterIndicator(symbol, self.stcSlow, timedelta(**{td : tdSlow}))
        
        self.stcSlow.Updated += self.stcSlowUpdated
        
        
        self.stcExtraSlow = SchaffTrendCycle(5, 9, 21)
        self.stcExtraSlow_window = RollingWindow[Decimal](5)
        algorithm.RegisterIndicator(symbol, self.stcExtraSlow, timedelta(**{td : tdExtraSlow}))
        self.stcExtraSlow.Updated += self.stcExtraSlowUpdated
        
        
        # # doji
        # self.doji = CandlestickPatterns.Doji(str(symbol))
        # self.doji_window = RollingWindow[float](5)
        # algorithm.RegisterIndicator(symbol, self.doji, timedelta(**{td : tdFast}))
        # self.doji.Updated += self.dojiUpdated
        
        # # VWAP
        # self.vwap = VolumeWeightedAveragePriceIndicator(20)
        # self.RegisterIndicator(symbol, self.vwap, timedelta(**{td : tdFast}))
        
        
        # HMAs
        self.hma = HullMovingAverage(symbol, 14)
        algorithm.RegisterIndicator(symbol, self.hma, timedelta(**{td : tdFast}))
    
        self.hmaSlow = HullMovingAverage(14)
        algorithm.RegisterIndicator(symbol, self.hmaSlow, timedelta(**{td : tdSlow}))  
    
        self.hmaExtraSlow = HullMovingAverage(symbol, 14)
        algorithm.RegisterIndicator(symbol, self.hmaExtraSlow, timedelta(**{td : tdExtraSlow}))
        
        
        
        # EMA
        self.emaSlow = ExponentialMovingAverage(10)
        algorithm.RegisterIndicator(symbol, self.emaSlow, timedelta(**{td : tdSlow}))
        
        self.emaExtraSlow = ExponentialMovingAverage(10)
        algorithm.RegisterIndicator(symbol, self.emaExtraSlow, timedelta(**{td : tdExtraSlow}))
        
        
        # Regression Channel
        
        self.rcFast = RegressionChannel(60, 2)
        self.rcFast_window = RollingWindow[Decimal](4)
        algorithm.RegisterIndicator(symbol, self.rcFast, timedelta(**{td : tdFast}))
        self.rcFast.Updated += self.rcFastUpdated
        
        self.rcSlow = RegressionChannel(30, 2)
        self.rcSlow_window = RollingWindow[Decimal](4)
        algorithm.RegisterIndicator(symbol, self.rcSlow, timedelta(**{td : tdSlow}))
        self.rcSlow.Updated += self.rcSlowUpdated
        
        self.rcExtraSlow = RegressionChannel(60, 2)
        self.rcExtraSlow_window = RollingWindow[Decimal](4)
        algorithm.RegisterIndicator(symbol, self.rcExtraSlow, timedelta(**{td : tdExtraSlow}))
        self.rcExtraSlow.Updated += self.rcExtraSlowUpdated


        # Regression Lower Channel
        
        self.rcFast_lower_window = RollingWindow[Decimal](4)
        self.rcFast.LowerChannel.Updated += self.rcFastLowerUpdated
        
        
        self.rcSlow_lower_window = RollingWindow[Decimal](4)
        self.rcSlow.LowerChannel.Updated += self.rcSlowLowerUpdated   
        
        
        # maximum
        self.maxFast = Maximum(maxPeriod)
        self.maxFast_window = RollingWindow[Decimal](5)
        algorithm.RegisterIndicator(symbol, self.maxFast, timedelta(**{td : tdFast}), Field.High)
        self.maxFast.Updated += self.maxFastUpdated
        
        
        self.maxSlow = Maximum(maxPeriod)
        algorithm.RegisterIndicator(symbol, self.maxSlow, timedelta(**{td : tdSlow}), Field.High)
        
        self.maxSlowDelay = IndicatorExtensions.Of(Delay(1), self.maxSlow)
        algorithm.RegisterIndicator(symbol, self.maxSlowDelay, timedelta(**{td : tdSlow}), Field.High)

        
        self.maxExtraSlow = Maximum(maxPeriod)
        algorithm.RegisterIndicator(symbol, self.maxExtraSlow, timedelta(**{td : tdExtraSlow}), Field.High)


        
        
        ### consolidators and price widows
        
        self.high_window = RollingWindow[float](6)
        self.low_window = RollingWindow[float](6)
        self.close_window = RollingWindow[float](6)

        self.fastConsolidator = TradeBarConsolidator(timedelta(**{td : tdFast}))
        self.fastConsolidator.DataConsolidated += self.fastHandler
        algorithm.SubscriptionManager.AddConsolidator(symbol, self.fastConsolidator)
    


        self.highSlow_window = RollingWindow[float](6)
        self.lowSlow_window = RollingWindow[float](6)
    
        self.slowConsolidator = TradeBarConsolidator(timedelta(**{td : tdSlow}))
        self.slowConsolidator.DataConsolidated += self.slowHandler
        algorithm.SubscriptionManager.AddConsolidator(symbol, self.slowConsolidator)
        
        

        
        self.highExtraSlow_window = RollingWindow[float](6)
        self.lowExtraSlow_window = RollingWindow[float](6)

        self.extraSlowConsolidator = TradeBarConsolidator(timedelta(**{td : tdExtraSlow}))
        self.extraSlowConsolidator.DataConsolidated += self.extraSlowHandler
        algorithm.SubscriptionManager.AddConsolidator(symbol, self.extraSlowConsolidator)
 
    
        
        
        # order tickets
        self.entryOrderTicket = None
        self.exitOrderTicket = None
        self.takeProfitTicket = None
        self.stopLossTicket = None
        self.coolDown = datetime.now()
        

        
    #### HANDLERS ####    
    
    def fastHandler(self, sender, consolidated):
        '''Event holder to update the close Rolling Window values'''
        
        self.high_window.Add(consolidated.High)
        self.low_window.Add(consolidated.Low)
        self.close_window.Add(consolidated.Close)
        
        
        
    def slowHandler(self, sender, consolidated):
        '''Event holder to update the close Rolling Window values'''
        
        self.highSlow_window.Add(consolidated.High)
        self.lowSlow_window.Add(consolidated.Low)
                
        
    def extraSlowHandler(self, sender, consolidated):
        '''Event holder to update the close Rolling Window values'''
        
        self.highExtraSlow_window.Add(consolidated.High)
        self.lowExtraSlow_window.Add(consolidated.Low)

    



        
    def HighHaUpdated(self, sender, updated):

        '''Event holder to update the close Rolling window values'''
        if self.ha.IsReady:
            self.ha_high_window.Add(self.ha.High.Current.Value)
            
    def CloseFastHaUpdated(self, sender, updated):

        '''Event holder to update the close Rolling window values'''
        if self.ha.IsReady:
            self.ha_close_window.Add(self.ha.Close.Current.Value)
            
    def OpenFastHaUpdated(self, sender, updated):

        '''Event holder to update the close Rolling window values'''
        if self.ha.IsReady:
            self.ha_open_window.Add(self.ha.Open.Current.Value)
            
    def SlowCloseHaUpdated(self, sender, updated):

        '''Event holder to update the close Rolling window values'''
        if self.haSlow.IsReady:
            self.haSlow_close_window.Add(self.haSlow.Close.Current.Value)
            

    def SlowHighHaUpdated(self, sender, updated):

        '''Event holder to update the close Rolling window values'''
        if self.haSlow.IsReady:
            self.haSlow_high_window.Add(self.haSlow.High.Current.Value)
            
    def ExtraSlowHighHaUpdated(self, sender, updatedd):

        '''Event holder to update the close Rolling window values'''
        if self.haExtraSlow.IsReady:
            self.haExtraSlow_high_window.Add(self.haExtraSlow.High.Current.Value)
            


    def ExtraSlowCloseHaUpdated(self, sender, updated):

        '''Event holder to update the close Rolling window values'''
        if self.haExtraSlow.IsReady:
            self.haExtraSlow_close_window.Add(self.haExtraSlow.Close.Current.Value)
            
            
    def stcFastUpdated(self, sender, updated):
        '''Event holder to update the close Rolling window values'''
        if self.stcFast.IsReady:
            self.stcFast_window.Add(updated)
            
    def stcSlowUpdated(self, sender, updated):

        '''Event holder to update the close Rolling window values'''
        if self.stcSlow.IsReady:
            self.stcSlow_window.Add(updated)
            
    def stcExtraSlowUpdated(self, sender, updated):

        '''Event holder to update the close Rolling window values'''
        if self.stcExtraSlow.IsReady:
            self.stcExtraSlow_window.Add(updated)
            
            
    def rcFastUpdated(self, sender, updated):

        '''Event holder to update the close Rolling window values'''
        if self.rcFast.IsReady:
            self.rcFast_window.Add(updated)


    def rcSlowUpdated(self, sender, updated):

        '''Event holder to update the close Rolling window values'''
        if self.rcSlow.IsReady:
            self.rcSlow_window.Add(updated)


    def rcExtraSlowUpdated(self, sender, updated):

        '''Event holder to update the close Rolling window values'''
        if self.rcExtraSlow.IsReady:
            self.rcExtraSlow_window.Add(updated)


    def rcFastLowerUpdated(self, sender, updated):

        '''Event holder to update the close Rolling window values'''
        if self.rcFast.IsReady:
            self.rcFast_lower_window.Add(updated)

    def rcSlowLowerUpdated(self, sender, updated):

        '''Event holder to update the close Rolling window values'''
        if self.rcSlow.IsReady:
            self.rcSlow_lower_window.Add(updated)
            
    def maxFastUpdated(self, sender, updated):

        '''Event holder to update the close Rolling window values'''
        if self.maxFast.IsReady:
            self.maxFast_window.Add(updated)
            
            
            

            
    # def dojiUpdated(self, sender, updated):

    #     '''Event holder to update the close Rolling window values'''
    #     if self.doji.IsReady:
    #         self.doji_window.Add(self.doji.Current.Value)


    @property 

    def IsReady(self):

        return self.ha.IsReady and self.ha_high_window.IsReady and self.ha_close_window.IsReady and self.ha_open_window.IsReady and\
        self.haSlow.IsReady and self.haSlow_high_window.IsReady and self.haSlow_close_window.IsReady and\
        self.haExtraSlow.IsReady and self.haExtraSlow_high_window.IsReady and self.haExtraSlow_close_window.IsReady and\
        self.stcFast.IsReady and self.stcFast_window.IsReady and\
        self.stcSlow.IsReady and self.stcSlow_window.IsReady and\
        self.stcExtraSlow.IsReady and self.stcExtraSlow_window.IsReady and\
        self.hma.IsReady and self.hmaSlow.IsReady and self.hmaExtraSlow.IsReady and\
        self.rcFast.IsReady and self.rcSlow.IsReady and self.rcExtraSlow.IsReady and\
        self.maxFast.IsReady and self.maxSlow.IsReady 


    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)
