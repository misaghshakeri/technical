"""
This file contains a collection of common indicators, which are based on third party or custom libraries

"""
from numpy.core.records import ndarray
from pandas import Series, DataFrame
from math import log

#import numpy as np


def aroon(dataframe, period=25, field='close', colum_prefix="aroon") -> DataFrame:
    from pyti.aroon import aroon_up as up
    from pyti.aroon import aroon_down as down
    dataframe["{}_up".format(colum_prefix)] = up(dataframe[field], period)
    dataframe["{}_down".format(colum_prefix)] = down(dataframe[field], period)
    return dataframe


def atr(dataframe, period, field='close') -> ndarray:
    from pyti.average_true_range import average_true_range
    return average_true_range(dataframe[field], period)


def atr_percent(dataframe, period, field='close') -> ndarray:
    from pyti.average_true_range_percent import average_true_range_percent
    return average_true_range_percent(dataframe[field], period)


def bollinger_bands(dataframe, period=21, stdv=2, field='close', colum_prefix="bb") -> DataFrame:
    from pyti.bollinger_bands import lower_bollinger_band, middle_bollinger_band, upper_bollinger_band
    dataframe["{}_lower".format(colum_prefix)] = lower_bollinger_band(dataframe[field], period, stdv)
    dataframe["{}_middle".format(colum_prefix)] = middle_bollinger_band(dataframe[field], period, stdv)
    dataframe["{}_upper".format(colum_prefix)] = upper_bollinger_band(dataframe[field], period, stdv)

    return dataframe


def cmf(dataframe, period=14) -> ndarray:
    from pyti.chaikin_money_flow import chaikin_money_flow

    return chaikin_money_flow(dataframe['close'], dataframe['high'], dataframe['low'], dataframe['volume'], period)


def accumulation_distribution(dataframe) -> ndarray:
    from pyti.accumulation_distribution import accumulation_distribution as acd

    return acd(dataframe['close'], dataframe['high'], dataframe['low'], dataframe['volume'])


def osc(dataframe, periods=14) -> ndarray:
    """
    1. Calculating DM (i).
        If HIGH (i) > HIGH (i - 1), DM (i) = HIGH (i) - HIGH (i - 1), otherwise DM (i) = 0.
    2. Calculating DMn (i).
        If LOW (i) < LOW (i - 1), DMn (i) = LOW (i - 1) - LOW (i), otherwise DMn (i) = 0.
    3. Calculating value of OSC:
        OSC (i) = SMA (DM, N) / (SMA (DM, N) + SMA (DMn, N)).

    :param dataframe:
    :param periods:
    :return:
    """
    df = dataframe
    df['DM'] = (df['high'] - df['high'].shift()).apply(lambda x: max(x, 0))
    df['DMn'] = (df['low'].shift() - df['low']).apply(lambda x: max(x, 0))
    return Series.rolling_mean(df.DM, periods) / (
            Series.rolling_mean(df.DM, periods) + Series.rolling_mean(df.DMn, periods))


def cmo(dataframe, period, field='close') -> ndarray:
    from pyti.chande_momentum_oscillator import chande_momentum_oscillator
    return chande_momentum_oscillator(dataframe[field], period)


def cci(dataframe, period) -> ndarray:
    from pyti.commodity_channel_index import commodity_channel_index

    return commodity_channel_index(dataframe['close'], dataframe['high'], dataframe['low'], period)


def vfi(dataframe, length=130, coef=0.2, vcoef=2.5, signalLength=5, smoothVFI=False):
    """
    Volume Flow Indicator conversion

    Author: creslinux, June 2018 - Python
    Original Author: Chris Moody, TradingView - Pinescript
    To return vfi, vfima and histogram

    A simplified interpretation of the VFI is:
    * Values above zero indicate a bullish state and the crossing of the zero line is the trigger or buy signal.
    * The strongest signal with all money flow indicators is of course divergence.
    * A crossover of vfi > vfima is uptrend
    * A crossunder of vfima > vfi is downtrend
    * smoothVFI can be set to smooth for a cleaner plot to ease false signals
    * histogram can be used against self -1 to check if upward or downward momentum


    Call from strategy to populate vfi, vfima, vfi_hist into dataframe

    Example how to call:
    # Volume Flow Index: Add VFI, VFIMA, Histogram to DF
    dataframe['vfi'], dataframe['vfima'], dataframe['vfi_hist'] =  \
        vfi(dataframe, length=130, coef=0.2, vcoef=2.5, signalLength=5, smoothVFI=False)

    :param dataframe:
    :param length: - VFI Length - 130 default
    :param coef:  - price coef  - 0.2 default
    :param vcoef: - volume coef  - 2.5 default
    :param signalLength: - 5 default
    :param smoothVFI:  bool - False detault
    :return: vfi, vfima, vfi_hist
    """

    """"
    Original Pinescript 
    From: https://www.tradingview.com/script/MhlDpfdS-Volume-Flow-Indicator-LazyBear/

    length = input(130, title="VFI length")
    coef = input(0.2)
    vcoef = input(2.5, title="Max. vol. cutoff")
    signalLength=input(5)
    smoothVFI=input(false, type=bool)

    #### Conversion summary to python 
      - ma(x,y) => smoothVFI ? sma(x,y) : x // Added as smoothVFI test on vfi

      - typical = hlc3  // Added to DF as HLC
      - inter = log(typical) - log(typical[1]) // Added to DF as inter
      - vinter = stdev(inter, 30) // Added to DF as vinter
      - cutoff = coef * vinter * close // Added to DF as cutoff
      - vave = sma(volume, length)[1] // Added to DF as vave
      - vmax = vave * vcoef // Added to Df as vmax
      - vc = iff(volume < vmax, volume, vmax) // Added np.where test, result in DF as vc
      - mf = typical - typical[1] // Added into DF as mf - typical is hlc3
      - vcp = iff(mf > cutoff, vc, iff(mf < -cutoff, -vc, 0)) // added in def vcp, in DF as vcp

      - vfi = ma(sum(vcp, length) / vave, 3) // Added as DF vfi. Will sma vfi 3 if smoothVFI flag set
      - vfima = ema(vfi, signalLength) // added to DF as vfima
      - d = vfi-vfima // Added to df as histogram

    ### Pinscript plotout - nothing to do here for freqtrade.
    plot(0, color=gray, style=3)
    showHisto=input(false, type=bool)
    plot(showHisto ? d : na, style=histogram, color=gray, linewidth=3, transp=50)
    plot( vfima , title="EMA of vfi", color=orange)
    plot( vfi, title="vfi", color=green,linewidth=2)
    """
    import talib as ta
    from math import log
    from pyti.simple_moving_average import simple_moving_average as sma
    from numpy import where

    length = length
    coef = coef
    vcoef = vcoef
    signalLength = signalLength
    smoothVFI = smoothVFI
    df = dataframe
    # Add hlc3 and populate inter to the dataframe
    df['hlc'] = ((df['high'] + df['low'] + df['close']) / 3).astype(float)
    df['inter'] = df['hlc'].map(log) - df['hlc'].shift(+1).map(log)
    df['vinter'] = df['inter'].rolling(30).std(ddof=0)
    df['cutoff'] = (coef * df['vinter'] * df['close'])
    # Vave is to be calculated on volume of the past bar
    df['vave'] = sma(df['volume'].shift(+1), length)
    df['vmax'] = df['vave'] * vcoef
    df['vc'] = where((df['volume'] < df['vmax']), df['volume'], df['vmax'])
    df['mf'] = df['hlc'] - df['hlc'].shift(+1)

    # more logic for vcp, so create a def and df.apply it
    def vcp(x):
        if x['mf'] > x['cutoff']:
            return x['vc']
        elif x['mf'] < -(x['cutoff']):
            return -(x['vc'])
        else:
            return 0

    df['vcp'] = df.apply(vcp, axis=1)
    # vfi has a smooth option passed over def call, sma if set
    df['vfi'] = (df['vcp'].rolling(length).sum()) / df['vave']
    if smoothVFI == True:
        df['vfi'] = sma(df['vfi'], 3)
    df['vfima'] = ta.EMA(df['vfi'], signalLength)
    df['vfi_hist'] = df['vfi'] - df['vfima']

    # clean up columns used vfi calculation but not needed for strat
    df.drop('hlc', axis=1, inplace=True)
    df.drop('inter', axis=1, inplace=True)
    df.drop('vinter', axis=1, inplace=True)
    df.drop('cutoff', axis=1, inplace=True)
    df.drop('vave', axis=1, inplace=True)
    df.drop('vmax', axis=1, inplace=True)
    df.drop('vc', axis=1, inplace=True)
    df.drop('mf', axis=1, inplace=True)
    df.drop('vcp', axis=1, inplace=True)

    return df['vfi'], df['vfima'], df['vfi_hist']


def mmar(self, dataframe, matype="EMA", src="close", debug=False):
    """
    Madrid Moving Average Ribbon

    Returns: MMAR
    """
    """
    Author(Freqtrade): Creslinux
    Original Author(TrdingView): "Madrid"

    Pinescript from TV Source Code and Description 
    //
    // Madrid : 17/OCT/2014 22:51M: Moving Average Ribbon : 2.0 : MMAR
    // http://madridjourneyonws.blogspot.com/
    //
    // This plots a moving average ribbon, either exponential or standard.
    // This study is best viewed with a dark background.  It provides an easy
    // and fast way to determine the trend direction and possible reversals.
    //
    // Lime : Uptrend. Long trading
    // Green : Reentry (buy the dip) or downtrend reversal warning
    // Red : Downtrend. Short trading
    // Maroon : Short Reentry (sell the peak) or uptrend reversal warning
    //
    // To best determine if this is a reentry point or a trend reversal
    // the MMARB (Madrid Moving Average Ribbon Bar) study is used.
    // This is the bar located at the bottom.  This bar signals when a
    // current trend reentry is found (partially filled with opposite dark color)
    // or when a trend reversal is ahead (completely filled with opposite dark color).
    //

    study(title="Madrid Moving Average Ribbon", shorttitle="MMAR", overlay=true)
    exponential = input(true, title="Exponential MA")

    src = close

    ma05 = exponential ? ema(src, 05) : sma(src, 05)
    ma10 = exponential ? ema(src, 10) : sma(src, 10)
    ma15 = exponential ? ema(src, 15) : sma(src, 15)
    ma20 = exponential ? ema(src, 20) : sma(src, 20)
    ma25 = exponential ? ema(src, 25) : sma(src, 25)
    ma30 = exponential ? ema(src, 30) : sma(src, 30)
    ma35 = exponential ? ema(src, 35) : sma(src, 35)
    ma40 = exponential ? ema(src, 40) : sma(src, 40)
    ma45 = exponential ? ema(src, 45) : sma(src, 45)
    ma50 = exponential ? ema(src, 50) : sma(src, 50)
    ma55 = exponential ? ema(src, 55) : sma(src, 55)
    ma60 = exponential ? ema(src, 60) : sma(src, 60)
    ma65 = exponential ? ema(src, 65) : sma(src, 65)
    ma70 = exponential ? ema(src, 70) : sma(src, 70)
    ma75 = exponential ? ema(src, 75) : sma(src, 75)
    ma80 = exponential ? ema(src, 80) : sma(src, 80)
    ma85 = exponential ? ema(src, 85) : sma(src, 85)
    ma90 = exponential ? ema(src, 90) : sma(src, 90)
    ma100 = exponential ? ema(src, 100) : sma(src, 100)

    leadMAColor = change(ma05)>=0 and ma05>ma100 ? lime
                : change(ma05)<0  and ma05>ma100 ? maroon
                : change(ma05)<=0 and ma05<ma100 ? red
                : change(ma05)>=0 and ma05<ma100 ? green
                : gray
    maColor(ma, maRef) =>
                  change(ma)>=0 and ma05>maRef ? lime
                : change(ma)<0  and ma05>maRef ? maroon
                : change(ma)<=0 and ma05<maRef ? red
                : change(ma)>=0 and ma05<maRef ? green
                : gray

    plot( ma05, color=leadMAColor, style=line, title="MMA05", linewidth=3)
    plot( ma10, color=maColor(ma10,ma100), style=line, title="MMA10", linewidth=1)
    plot( ma15, color=maColor(ma15,ma100), style=line, title="MMA15", linewidth=1)
    plot( ma20, color=maColor(ma20,ma100), style=line, title="MMA20", linewidth=1)
    plot( ma25, color=maColor(ma25,ma100), style=line, title="MMA25", linewidth=1)
    plot( ma30, color=maColor(ma30,ma100), style=line, title="MMA30", linewidth=1)
    plot( ma35, color=maColor(ma35,ma100), style=line, title="MMA35", linewidth=1)
    plot( ma40, color=maColor(ma40,ma100), style=line, title="MMA40", linewidth=1)
    plot( ma45, color=maColor(ma45,ma100), style=line, title="MMA45", linewidth=1)
    plot( ma50, color=maColor(ma50,ma100), style=line, title="MMA50", linewidth=1)
    plot( ma55, color=maColor(ma55,ma100), style=line, title="MMA55", linewidth=1)
    plot( ma60, color=maColor(ma60,ma100), style=line, title="MMA60", linewidth=1)
    plot( ma65, color=maColor(ma65,ma100), style=line, title="MMA65", linewidth=1)
    plot( ma70, color=maColor(ma70,ma100), style=line, title="MMA70", linewidth=1)
    plot( ma75, color=maColor(ma75,ma100), style=line, title="MMA75", linewidth=1)
    plot( ma80, color=maColor(ma80,ma100), style=line, title="MMA80", linewidth=1)
    plot( ma85, color=maColor(ma85,ma100), style=line, title="MMA85", linewidth=1)
    plot( ma90, color=maColor(ma90,ma100), style=line, title="MMA90", linewidth=3)
    :return:
    """
    import talib as ta

    matype = matype
    src = src
    df = dataframe
    debug = debug

    # Default to EMA, allow SMA if passed to def.
    if matype == "EMA" or matype == "ema":
        ma = ta.EMA
    elif matype == "SMA" or matype == "sma":
        ma = ta.SMA
    else:
        ma = ta.EMA

    # Get MAs, also last MA in own column to pass to def later
    df["ma05"] = ma(df[src], 5)
    df['ma05l'] = df['ma05'].shift(+1)
    df["ma10"] = ma(df[src], 10)
    df['ma10l'] = df['ma10'].shift(+1)
    df["ma20"] = ma(df[src], 20)
    df['ma20l'] = df['ma20'].shift(+1)
    df["ma30"] = ma(df[src], 30)
    df['ma30l'] = df['ma30'].shift(+1)
    df["ma40"] = ma(df[src], 40)
    df['ma40l'] = df['ma40'].shift(+1)
    df["ma50"] = ma(df[src], 50)
    df['ma50l'] = df['ma50'].shift(+1)
    df["ma60"] = ma(df[src], 60)
    df['ma60l'] = df['ma60'].shift(+1)
    df["ma70"] = ma(df[src], 70)
    df['ma70l'] = df['ma70'].shift(+1)
    df["ma80"] = ma(df[src], 80)
    df['ma80l'] = df['ma80'].shift(+1)
    df["ma90"] = ma(df[src], 90)
    df['ma90l'] = df['ma90'].shift(+1)
    df["ma100"] = ma(df[src], 100)
    df['ma100l'] = df['ma100'].shift(+1)

    """ logic for LeadMA
    : change(ma05)>=0 and ma05>ma100 ? lime    +2
    : change(ma05)<0  and ma05>ma100 ? maroon  -1
    : change(ma05)<=0 and ma05<ma100 ? red     -2
    : change(ma05)>=0 and ma05<ma100 ? green   +1
    : gray
    """

    def leadMAc(x):
        if (x['ma05'] - x['ma05l']) >= 0 and (x['ma05'] > x['ma100']):
            # Lime: Uptrend.Long trading
            x["leadMA"] = "lime"
            return x["leadMA"]
        elif (x['ma05'] - x['ma05l']) < 0 and (x['ma05'] > x['ma100']):
            # Maroon : Short Reentry (sell the peak) or uptrend reversal warning
            x["leadMA"] = "maroon"
            return x["leadMA"]
        elif (x['ma05'] - x['ma05l']) <= 0 and (x['ma05'] < x['ma100']):
            # Red : Downtrend. Short trading
            x["leadMA"] = "red"
            return x["leadMA"]
        elif (x['ma05'] - x['ma05l']) >= 0 and (x['ma05'] < x['ma100']):
            # Green: Reentry(buy the dip) or downtrend reversal warning
            x["leadMA"] = "green"
            return x["leadMA"]
        else:
            # If its great it means not enough ticker data for lookback
            x["leadMA"] = "grey"
            return x["leadMA"]

    df['leadMA'] = df.apply(leadMAc, axis=1)

    """   Logic for MAs 
    : change(ma)>=0 and ma05>ma100 ? lime
    : change(ma)<0  and ma05>ma100 ? maroon
    : change(ma)<=0 and ma05<ma100 ? red
    : change(ma)>=0 and ma05<ma100 ? green
    : gray
    """

    def maColor(x, ma):
        col_label = '_'.join([ma, "c"])
        col_lable_l = ''.join([ma, "l"])

        if (x[ma] - x[col_lable_l]) >= 0 and (x[ma] > x['ma100']):
            # Lime: Uptrend.Long trading
            x[col_label] = "lime"
            return x[col_label]
        elif (x[ma] - x[col_lable_l]) < 0 and (x[ma] > x['ma100']):
            # Maroon : Short Reentry (sell the peak) or uptrend reversal warning
            x[col_label] = "maroon"
            return x[col_label]

        elif (x[ma] - x[col_lable_l]) <= 0 and (x[ma] < x['ma100']):
            # Red : Downtrend. Short trading
            x[col_label] = "red"
            return x[col_label]

        elif (x[ma] - x[col_lable_l]) >= 0 and (x[ma] < x['ma100']):
            # Green: Reentry(buy the dip) or downtrend reversal warning
            x[col_label] = "green"
            return x[col_label]
        else:
            # If its great it means not enough ticker data for lookback
            x[col_label] = 'grey'
            return x[col_label]

    df['ma05_c'] = df.apply(maColor, ma="ma05", axis=1)
    df['ma10_c'] = df.apply(maColor, ma="ma10", axis=1)
    df['ma20_c'] = df.apply(maColor, ma="ma20", axis=1)
    df['ma30_c'] = df.apply(maColor, ma="ma30", axis=1)
    df['ma40_c'] = df.apply(maColor, ma="ma40", axis=1)
    df['ma50_c'] = df.apply(maColor, ma="ma50", axis=1)
    df['ma60_c'] = df.apply(maColor, ma="ma60", axis=1)
    df['ma70_c'] = df.apply(maColor, ma="ma70", axis=1)
    df['ma80_c'] = df.apply(maColor, ma="ma80", axis=1)
    df['ma90_c'] = df.apply(maColor, ma="ma90", axis=1)

    if debug:
        from pandas import set_option
        set_option('display.max_rows', 2000)
        print(df[["date", "leadMA",
                  "ma05", "ma05l", "ma05_c",
                  "ma10", "ma10l", "ma10_c",
                  # "ma20", "ma20l", "ma20_c",
                  # "ma30", "ma30l", "ma30_c",
                  # "ma40", "ma40l", "ma40_c",
                  # "ma50", "ma50l", "ma50_c",
                  # "ma60", "ma60l", "ma60_c",
                  # "ma70", "ma70l", "ma70_c",
                  # "ma80", "ma80l", "ma80_c",
                  "ma90", "ma90l", "ma90_c",
                  "ma100", "leadMA"]].tail(200))

        print(df[["date", 'close',
                  "leadMA",
                  "ma10_c",
                  "ma20_c",
                  "ma30_c",
                  "ma40_c",
                  "ma50_c",
                  "ma60_c",
                  "ma70_c",
                  "ma80_c",
                  "ma90_c"
                  ]].tail(684))

    return df['leadMA'], df['ma10_c'], df['ma20_c'], df['ma30_c'], \
           df['ma40_c'], df['ma50_c'], df['ma60_c'], df['ma70_c'], \
           df['ma80_c'], df['ma90_c']


def madrid_sqz(self, datafame, length=34, src='close', ref=13, sqzLen=5):
    """
    Squeeze Madrid Indicator

    Author: Creslinux
    Original Author: Madrid - Tradingview
    https://www.tradingview.com/script/9bUUSzM3-Madrid-Trend-Squeeze/

    :param datafame:
    :param lenght: min 14 - default 34
    :param src: default close
    :param ref: default 13
    :param sqzLen: default 5
    :return: df['sqz_cma_c'], df['sqz_rma_c'], df['sqz_sma_c']


    There are seven colors used for the study

    Green : Uptrend in general
    Lime : Spots the current uptrend leg
    Aqua : The maximum profitability of the leg in a long trade
    The Squeeze happens when Green+Lime+Aqua are aligned (the larger the values the better)

    Maroon : Downtrend in general
    Red : Spots the current downtrend leg
    Fuchsia: The maximum profitability of the leg in a short trade
    The Squeeze happens when Maroon+Red+Fuchsia are aligned (the larger the values the better)

    Yellow : The trend has come to a pause and it is either a reversal warning or a continuation. These are the entry, re-entry or closing position points.
    """

    """ 
    Original Pinescript source code

    ma = ema(src, len)
    closema = close - ma
    refma = ema(src, ref) - ma
    sqzma = ema(src, sqzLen) - ma

    hline(0)
    plotcandle(0, closema, 0, closema, color=closema >= 0?aqua: fuchsia)
    plotcandle(0, sqzma, 0, sqzma, color=sqzma >= 0?lime: red)
    plotcandle(0, refma, 0, refma, color=(refma >= 0 and closema < refma) or (
                refma < 0 and closema > refma) ? yellow: refma >= 0 ? green: maroon)
    """
    import talib as ta
    from numpy import where

    len = length
    src = src
    ref = ref
    sqzLen = sqzLen
    df = datafame
    ema = ta.EMA

    """ Original code logic
    ma = ema(src, len)
    closema = close - ma
    refma = ema(src, ref) - ma
    sqzma = ema(src, sqzLen) - ma
    """
    df['sqz_ma'] = ema(df[src], len)
    df['sqz_cma'] = df['close'] - df['sqz_ma']
    df['sqz_rma'] = ema(df[src], ref) - df['sqz_ma']
    df['sqz_sma'] = ema(df[src], sqzLen) - df['sqz_ma']

    """ Original code logic
    plotcandle(0, closema, 0, closema, color=closema >= 0?aqua: fuchsia)
    plotcandle(0, sqzma, 0, sqzma, color=sqzma >= 0?lime: red)

    plotcandle(0, refma, 0, refma, color=
    (refma >= 0 and closema < refma) or (refma < 0 and closema > refma) ? yellow: 
    refma >= 0 ? green: maroon)
    """

    # print(df[['sqz_cma', 'sqz_rma', 'sqz_sma']])

    def sqz_cma_c(x):
        if x['sqz_cma'] >= 0:
            x['sqz_cma_c'] = "aqua"
            return x['sqz_cma_c']
        else:
            x['sqz_cma_c'] = "fuchsia"
            return x['sqz_cma_c']

    df['sqz_cma_c'] = df.apply(sqz_cma_c, axis=1)

    def sqz_sma_c(x):
        if x['sqz_sma'] >= 0:
            x['sqz_sma_c'] = "lime"
            return x['sqz_sma_c']
        else:
            x['sqz_sma_c'] = "red"
            return x['sqz_sma_c']

    df['sqz_sma_c'] = df.apply(sqz_sma_c, axis=1)

    def sqz_rma_c(x):
        if x['sqz_rma'] >= 0 and x['sqz_cma'] < x['sqz_rma']:
            x['sqz_rma_c'] = "yellow"
            return x['sqz_rma_c']
        elif x['sqz_rma'] < 0 and x['sqz_cma'] > x['sqz_rma']:
            x['sqz_rma_c'] = "yellow"
            return x['sqz_rma_c']
        elif x['sqz_rma'] >= 0:
            x['sqz_rma_c'] = "green"
            return x['sqz_rma_c']
        else:
            x['sqz_rma_c'] = "maroon"
            return x['sqz_rma_c']

    df['sqz_rma_c'] = df.apply(sqz_rma_c, axis=1)

    # print(df[['sqz_cma_c', 'sqz_rma_c', 'sqz_sma_c']])
    return df['sqz_cma_c'], df['sqz_rma_c'], df['sqz_sma_c']


def super_trend(df, period=14, multiplier=3):
    """
    Author: Misagh
    :param datafame:
    :param period: default 14
    :param multiplier: default 3
    :return: df['st'], df['stx']

    SuperTrend Algorithm :

    BASIC UPPERBAND = (HIGH + LOW) / 2 + Multiplier * ATR
    BASIC LOWERBAND = (HIGH + LOW) / 2 - Multiplier * ATR

    FINAL UPPERBAND = IF( (Current BASICUPPERBAND < Previous FINAL UPPERBAND) or (Previous Close > Previous FINAL UPPERBAND) )
                        THEN (Current BASIC UPPERBAND)
                        ELSE Previous FINALUPPERBAND
                        )
    FINAL LOWERBAND = IF( (Current BASIC LOWERBAND > Previous FINAL LOWERBAND) or (Previous Close < Previous FINAL LOWERBAND) )
                        THEN (Current BASIC LOWERBAND)
                        ELSE Previous FINAL LOWERBAND)

    SUPERTREND = IF( (Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close <= Current FINAL UPPERBAND)) THEN
                    Current FINAL UPPERBAND
                    ELSE
                    IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close > Current FINAL UPPERBAND)) THEN
                        Current FINAL LOWERBAND
                    ELSE
                        IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close >= Current FINAL LOWERBAND)) THEN
                            Current FINAL LOWERBAND
                        ELSE
                            IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close < Current FINAL LOWERBAND)) THEN
                                Current FINAL UPPERBAND
    """

    df['atr'] = atr(df, period)

    # Compute basic upper and lower bands
    df['basic_ub'] = (df['high'] + df['low']) / 2 + multiplier * df["atr"]
    df['basic_lb'] = (df['high'] + df['low']) / 2 - multiplier * df["atr"]

    # Compute final upper and lower bands
    df['final_ub'] = 0.00
    df['final_lb'] = 0.00
    for i in range(period, len(df)):
        if df['basic_ub'].iat[i] < df['final_ub'].iat[i - 1] or df['close'].iat[i - 1] > df['final_ub'].iat[i - 1]:
            df['final_ub'].iat[i] = df['basic_ub'].iat[i]
        else:
            df['final_ub'].iat[i - 1]
        if df['basic_lb'].iat[i] > df['final_lb'].iat[i - 1] or df['close'].iat[i - 1] < df['final_lb'].iat[i - 1]:
            df['final_lb'].iat[i] = df['basic_lb'].iat[i]
        else:
            df['final_lb'].iat[i - 1]

    # Set the Supertrend value
    df['st'] = 0.00

    for i in range(period, len(df)):
        if df['st'].iat[i - 1] == df['final_ub'].iat[i - 1] and df['close'].iat[i] <= df['final_ub'].iat[i]:
            df['st'].iat[i] = df['final_ub'].iat[i]
        else:
            if df['st'].iat[i - 1] == df['final_ub'].iat[i - 1] and df['close'].iat[i] > df['final_ub'].iat[i]:
                df['final_lb'].iat[i]
            else:
                if df['st'].iat[i - 1] == df['final_lb'].iat[i - 1] and df['close'].iat[i] >= df['final_lb'].iat[i]:
                    df['final_lb'].iat[i]
                else:
                    if df['st'].iat[i - 1] == df['final_lb'].iat[i - 1] and df['close'].iat[i] < df['final_lb'].iat[i]:
                        df['final_ub'].iat[i]
                    else:
                        0.00

    # Mark the trend direction up/down
    #df['stx'] = np.where((df['st'] > 0.00), np.where((df['close'] < df['st']), 'down',  'up'), np.NaN)

    # Remove basic and final bands from the columns
    df.drop(['basic_ub', 'basic_lb', 'final_ub', 'final_lb'], inplace=True, axis=1)

    df.fillna(0, inplace=True)

    return df['st'] #, df['stx']
