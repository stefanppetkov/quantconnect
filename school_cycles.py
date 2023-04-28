from AlgorithmImports import *
from data import SymbolData
import datetime
import time
import requests
import decimal

td = 'minutes'
tdFast = 2
tdSlow = 5
tdExtraSlow = 10
maxAtr   = 0.2
minAtr = 0.05
hardTP = 0.1
pos_size = 100
tickers = ['EYPT', 'LYFT', 'PRST']


class SchaffTimeCycles(QCAlgorithm):



    def Initialize(self):
        
        self.coolDown = False

       

        self.Data = {}

        for ticker in tickers:
            symbol = self.AddEquity(ticker, Resolution.Second, extendedMarketHours = True).Symbol
            self.Data[symbol] = SymbolData(self, symbol)


        self.SetWarmUp(tdSlow*21*30, Resolution.Minute) # WAS 2500



    def OnData(self, data):

        #self.Debug("on data")


        if self.IsWarmingUp: return
            #self.Debug("is warming up")
        

            

        for symbol, symbolData in self.Data.items():

            if symbolData.IsReady and len(self.Data) == len(tickers):
                
                
                currentTime =  datetime.datetime.now().time()

                incRC = symbolData.rcFast.Slope.Current.Value > 0 # or use slope
                incRCslow = symbolData.rcSlow.Slope.Current.Value > 0 # or use slope
                lowRC = symbolData.ha.Current.Value < symbolData.rcFast.Current.Value
                highRCslow = symbolData.haExtraSlow.Current.Value > symbolData.rcExtraSlow.UpperChannel.Current.Value
                hmaFast = symbolData.ha.Current.Value > symbolData.hma.Current.Value
                hmaSlow = symbolData.haSlow.Current.Value > symbolData.hmaSlow.Current.Value
                atr = symbolData.atr.Current.Value > 0.04 and symbolData.atr.Current.Value < maxAtr
                stc_inc = symbolData.stcFast_window[0] > symbolData.stcFast_window[1] or symbolData.stcFast_window[0] > 25
                stc_slow_inc = (symbolData.stcSlow_window[0] > symbolData.stcSlow_window[1]) or hmaSlow and symbolData.stcSlow_window[0] > 25
                maxBreak = self.Securities[symbol].Price > symbolData.maxFast_window[0]

                lowerChan = symbolData.rcFast.LowerChannel.Current.Value        
                
                # time based trading lock
                tradeLock = False if currentTime.strftime('%H:%M') > symbolData['coolDown'].strftime('%H:%M') else True
                rth = True if currentTime > datetime.time(13, 35) and currentTime < datetime.time(19, 31) else False
                

                if self.Portfolio[symbol].Quantity == 0:
                    
                    self.Debug(f"{symbol} -- RC uptrend/inLower {(incRC or incRCslow), lowRC} -- HMA (fast): {hmaFast} -- STC: {stc_inc, stc_slow_inc} --  MaxBreak: {maxBreak}")

                    # enter when price is in the lower half of the regression channel                        
                    if hmaFast and stc_inc and stc_slow_inc and (incRC or incRCslow) and lowRC and not highRCslow and not tradeLock and maxBreak and atr:
                                                                                        
                        symbolData['entryOrderTicket'] = self.MarketOrder(symbol, pos_size)
                        symbolData['takeProfitTicket'] = self.LimitOrder(symbol, -pos_size, (symbolData['entryOrderTicket'].AverageFillPrice + (symbolData.atr.Current.Value if symbolData.atr.Current.Value > minAtr else symbolData.atrSlow.Current.Value)))
                        
                        sl_margin = symbolData['entryOrderTicket'].AverageFillPrice - lowerChan
                        symbolData['stopLossTicket'] = self.StopMarketOrder(symbol, -pos_size, (lowerChan if sl_margin > symbolData.atr.Current.Value and sl_margin <= maxAtr else symbolData['entryOrderTicket'].AverageFillPrice - symbolData.atrSlow.Current.Value))
                        
                        symbolData['coolDown'] =  datetime.datetime.now()
                        time.sleep(2)
                        
                    # # enter when price is in the upper half of the regression channel    
                    # if hmaFast and stc_inc and (incRC or incRCslow) and highRCfast and not tradeLock and maxBreak and atr:
                                                                                        
                    #     symbolData['entryOrderTicket'] = self.MarketOrder(symbol, pos_size)
                    #     symbolData['takeProfitTicket'] = self.LimitOrder(symbol, -pos_size, symbolData.atr.Current.Value)
                        
                    #     sl_margin = symbolData['entryOrderTicket'].AverageFillPrice - lowerChan
                    #     symbolData['stopLossTicket'] = self.StopMarketOrder(symbol, -pos_size, (lowerChan if sl_margin > symbolData.atr.Current.Value and sl_margin <= maxAtr else symbolData['entryOrderTicket'].AverageFillPrice - symbolData.atrSlow.Current.Value))
                        
                    #     symbolData['coolDown'] =  datetime.datetime.now()
                    #     time.sleep(2)   
                            
                elif self.Portfolio[symbol].Quantity > 0:

                    uPL = self.Securities[symbol].Price - symbolData['entryOrderTicket'].AverageFillPrice
                    trailPrice = self.Securities[symbol].Price - (symbolData.atr.Current.Value if symbolData.atr.Current.Value > minAtr else symbolData.atrSlow.Current.Value)
                    slPrice = round(symbolData['stopLossTicket'].Get(OrderField.StopPrice), 2)
                    tpPrice = round(symbolData['takeProfitTicket'].Get(OrderField.LimitPrice), 2)
                     
                        
                    # trailing stopLoss at ATR distance
                    if ((uPL > (symbolData.atr.Current.Value if symbolData.atr.Current.Value > minAtr else minAtr) or\
                        uPL > symbolData['entryOrderTicket'].AverageFillPrice * 0.01)) and\
                        round(self.Transactions.GetOrderById(symbolData['stopLossTicket'].OrderId).Price, 2) < trailPrice:
                        trailingStop = UpdateOrderFields()
                        trailingStop.StopPrice = trailPrice
                        symbolData['stopLossTicket'].Update(trailingStop)
                        self.Debug(f"{symbol} stop price has been increased to {round(trailingStop.StopPrice, 2)}")
                
                        
                    if uPL >= symbolData['entryOrderTicket'].AverageFillPrice * 0.03:
                        symbolData['exitOrderTicket'] = self.MarketOrder(symbol, -pos_size)
                        
        
                    self.Debug(f"***HOLDING - {symbol}: {self.Securities[symbol].Price} -- Unrealized P/L: {round(uPL, 2)} --  SL: {slPrice} -- TP: {tpPrice}")
                
                else:
                    
                    self.Debug(f"NOT READY - {symbol}")
                    
                    
    def OnOrderEvent(self, orderevent): 

            if orderevent.Status == OrderStatus.Filled:
                for symbol, symbolData in self.Data.items():
                    

                    token = ""
                    chatId = ""
                    #message = None
                    #url = None
                    # If limit order has been filled, we cancel our stop loss and reset all order tickets
                    # TODO: If take profit triggers, don't let market sell go off.
                    if symbolData['takeProfitTicket'] is not None and symbolData['takeProfitTicket'].OrderId == orderevent.OrderId:
                        symbolData['stopLossTicket'].Cancel()
                        symbolData['entryOrderTicket'].Cancel()
                        message = f'SOLD (LIMIT): {symbol} @ {symbolData["takeProfitTicket"].AverageFillPrice}. P/L: {round(symbolData["takeProfitTicket"].AverageFillPrice - symbolData["entryOrderTicket"].AverageFillPrice, 2)}'
                        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chatId}&text={message}"
                        print(requests.get(url).json()) # this sends the message
                        symbolData['coolDown'] =  datetime.datetime.now() + datetime.timedelta(**{td : tdSlow})
                        if symbolData['exitOrderTicket'] != None:
                            symbolData['exitOrderTicket'].Cancel()
                        
                        

                    
                    # If stop order has been filled, we cancel our limit order and reset all order tickets
                    elif symbolData['stopLossTicket'] is not None and symbolData['stopLossTicket'].OrderId == orderevent.OrderId:
                        symbolData['takeProfitTicket'].Cancel()
                        symbolData['entryOrderTicket'].Cancel()
                        message = f'STOPPED OUT: {symbol} @ {symbolData["stopLossTicket"].AverageFillPrice}. P/L: {round(symbolData["stopLossTicket"].AverageFillPrice - symbolData["entryOrderTicket"].AverageFillPrice, 2)}'
                        url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chatId}&text={message}'
                        print(requests.get(url).json()) # this sends the message
                        symbolData['coolDown'] =  datetime.datetime.now() +  datetime.timedelta(**{td : tdSlow})
                        if symbolData['exitOrderTicket'] != None:
                            symbolData['exitOrderTicket'].Cancel()



                    
                    # # Notify Telegram when a market order is filled
                    elif symbolData['entryOrderTicket'] is not None and symbolData['entryOrderTicket'].OrderId == orderevent.OrderId:
                        message = f"NEW BUY: {pos_size} {symbol} @ {symbolData['entryOrderTicket'].AverageFillPrice}"
                        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chatId}&text={message}"
                        print(requests.get(url).json()) # this sends the message
                        
                        
                    
                    # market exit is filled    
                    elif symbolData['exitOrderTicket'] is not None and symbolData['exitOrderTicket'].OrderId == orderevent.OrderId:
                        symbolData['takeProfitTicket'].Cancel()
                        symbolData['stopLossTicket'].Cancel()
                        symbolData['entryOrderTicket'].Cancel()
                        message = f'SOLD (MARKET): {pos_size} {symbol} @ {symbolData["exitOrderTicket"].AverageFillPrice}. P/L: {round(symbolData["exitOrderTicket"].AverageFillPrice - symbolData["entryOrderTicket"].AverageFillPrice, 2)}'
                        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chatId}&text={message}"
                        symbolData['coolDown'] =  datetime.datetime.now() +  datetime.timedelta(**{td : tdSlow})
                        print(requests.get(url).json()) # this sends the message
