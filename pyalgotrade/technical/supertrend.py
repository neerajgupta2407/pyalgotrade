from pyalgotrade import dataseries
import pyalgotrade.technical.atr as atr


class Supertrend(object):
    def __init__(self, dataSeries, period=7, multiplier=2, useAdjustedValues=False, maxLen=None):
        self.__atr = atr.ATR(dataSeries, period)
        self.__multiplier = multiplier
        self.__prevClose = None
        self.__prevFinalUB = None
        self.__prevFinalLB = None
        self.__prevSuperTrend = None
        self.__SuperTrend = None
        self.__useAdjustedValues = useAdjustedValues
        self.__supertrendSeries = dataseries.SequenceDataSeries(maxLen=maxLen)

        # It is important to subscribe after sma and stddev since we'll use those values.
        dataSeries.getNewValueEvent().subscribe(self.__onNewValue)

    def __onNewValue(self, dataseries, datetime, value):
        self.__SuperTrend = self._super_trend(value)
        self.__supertrendSeries.appendWithDateTime(datetime, self.__SuperTrend)
        self.__prevClose = value.getClose(self.__useAdjustedValues)

    def get_atr(self):
        return self.__atr[-1]

    def getValue(self):
        return self.__supertrendSeries

    def _super_trend(self, value):
        # BASIC UPPERBAND = (HIGH + LOW) / 2 + Multiplier * ATR
        # BASIC LOWERBAND = (HIGH + LOW) / 2 - Multiplier * ATR
        #
        # FINAL UPPERBAND = IF( (Current BASICUPPERBAND < Previous FINAL UPPERBAND) or (Previous Close > Previous FINAL UPPERBAND))
        # THEN (Current BASIC UPPERBAND) ELSE Previous FINALUPPERBAND)
        # FINAL LOWERBAND = IF( (Current BASIC LOWERBAND > Previous FINAL LOWERBAND) or (Previous Close < Previous FINAL LOWERBAND))
        # THEN (Current BASIC LOWERBAND) ELSE Previous FINAL LOWERBAND)
        #
        # SUPERTREND = IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close <= Current FINAL UPPERBAND)) THEN
        # Current FINAL UPPERBAND
        # ELSE
        # IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close > Current FINAL UPPERBAND)) THEN
        # Current FINAL LOWERBAND
        # ELSE
        # IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close >= Current FINAL LOWERBAND)) THEN
        # Current FINAL LOWERBAND
        # ELSE
        # IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close < Current FINAL LOWERBAND)) THEN
        # Current FINAL UPPERBAND

        supertrend = None
        atr = self.get_atr()
        if atr is None:
            return
        high = value.getHigh(self.__useAdjustedValues)
        low = value.getLow(self.__useAdjustedValues)
        close = value.getClose(self.__useAdjustedValues)
        basic_upperband = ((high + low) / 2.0) + (
                    self.__multiplier * atr)  # BASIC UPPERBAND = (HIGH + LOW) / 2 + Multiplier * ATR
        basic_lowerband = ((high + low) / 2.0) - (
                    self.__multiplier * atr)  # BASIC LOWERBAND = (HIGH + LOW) / 2 - Multiplier * ATR
        final_upperband = None
        final_lowerband = None

        if self.__prevFinalLB and self.__prevFinalUB:
            final_upperband = basic_upperband if (
                        basic_upperband < self.__prevFinalUB or self.__prevClose > self.__prevFinalUB) else self.__prevFinalUB
            final_lowerband = basic_lowerband if (
                        basic_lowerband > self.__prevFinalLB or self.__prevClose < self.__prevFinalLB) else self.__prevFinalLB

            supertrend = final_upperband if (
                        self.__prevSuperTrend == self.__prevFinalUB and close <= final_upperband) else \
                final_lowerband if (self.__prevSuperTrend == self.__prevFinalUB and close > final_upperband) else \
                    final_lowerband if (self.__prevSuperTrend == self.__prevFinalLB and close >= final_lowerband) else \
                        final_upperband if (
                                    self.__prevSuperTrend == self.__prevFinalLB and close < final_lowerband) else final_lowerband

            # setting the prevLoweBand , prevUpperBand and supertrend
        self.__prevFinalLB = final_lowerband or basic_lowerband
        self.__prevFinalUB = final_upperband or basic_upperband
        self.__prevSuperTrend = supertrend
        return supertrend
