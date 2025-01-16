import os
import io
from PIL import Image
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import re
import datetime
from get_data import BinanceDataFetcher


class TradingEnvironment:
    def __init__(
        self,
        api_key: str, 
        api_secret: str,
        symbol: str, 
        base_path: str="downloaded_data",
        save_path: str="downloaded_data",
        load_local: bool=True,
        timeframes: list=['15m', '1h', '4h', '1d'],
        from_date: str="1 Jan 2024 00:00", 
        start_time: str="1 Jan 2024 01:00:00",
        end_date: str=None, 
        indicators: list=['rsi', 'vwap', 'supertrend'],
        min_candles: int=100
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.fetcher = BinanceDataFetcher(self.api_key, self.api_secret)
        self.symbol = symbol
        self.base_path = base_path
        self.save_path = save_path
        self.load_local = load_local
        self.timeframes = timeframes
        self.from_date = from_date
        self.start_time = start_time
        self.end_date = end_date
        self.indicators = indicators
        self.min_candles = min_candles
        self.start_time = datetime.datetime.strptime(from_date, "%d %b %Y %H:%M:%S") if from_date is not None else datetime.datetime.now()-datetime.timedelta(days=1)
        self.end_time = datetime.datetime.strptime(end_date, "%d %b %Y %H:%M:%S") if end_date is not None else datetime.datetime.now()
        self.current_idxs = {timeframe: 0 for timeframe in self.timeframes}
        self.cached_data = pd.DataFrame() # contains data on 1 minute timeframe
        os.makedirs(self.save_path, exist_ok=True)

    def load_data(self, symbol: str="SOLUSDT", timeframe: str="15m", from_date: str="1 Jan 2024", end_date: str=None, load_local: bool=False):
        if load_local:
            df = pd.read_csv(f"{self.base_path}/{symbol}_{timeframe}_data.csv")
            return df
        else:
            df = self.fetcher.get_historical_data(symbol, timeframe, from_date, end_date)
            df.to_csv(f"{self.save_path}/{symbol}_{timeframe}_data.csv", index=False)
            return df

    def get_data(self):
        self.data = {}
        for timeframe in self.timeframes:
            df = self.load_data(self.symbol, timeframe, self.from_date, self.end_date, load_local=self.load_local)
            self.data[timeframe] = df
            self.data[timeframe] = self.fetcher.add_indicator(self.data[timeframe], self.indicators)
        return self.data

    def get_index_from_time(self, time:str):
        times = []
        for timeframe in self.timeframes:
            df = self.data[timeframe]
            target_time = datetime.datetime.strptime(time, "%d %b %Y %H:%M:%S")
            df['OpenTimeTemp'] = pd.to_datetime(df['OpenTime'])
            fil = df[df['OpenTimeTemp'] <= target_time]
            idx = fil.index[-1]
            self.current_idxs[timeframe] = idx
            times.append(df['OpenTime'][idx])
            df.drop(columns=['OpenTimeTemp'], inplace=True)
        return self.current_idxs, times
    
    def get_minimum_starting_time(self):
        return self.data[self.timeframes[-1]].iloc[101]['OpenTime']
    
    def get_chart_data(self, time:str):
        # First get the times of each timeframe closest to the target time
        idxs, times = self.get_index_from_time(time)
        
        # Out of all the times, get the furthest time to get the data based on it
        target_time = datetime.datetime.strptime(time, "%d %b %Y %H:%M:%S")
        times = [datetime.datetime.strptime(t, "%d %b %Y %H:%M:%S") for t in times]
        times = [t for t in times if t <= target_time]
        idx = times.index(min(times))
        furthest_time = times[idx]
        start_time_for_data = furthest_time if len(self.cached_data) == 0 else self.cached_data.iloc[-1]['OpenTime']

        # If the start time is not in string format, convert it to string format
        if not isinstance(start_time_for_data, str):
            start_time_for_data = datetime.datetime.strftime(start_time_for_data, "%d %b %Y %H:%M:%S")

        # add 1 second to the time, to get latest data
        time = datetime.datetime.strptime(time, "%d %b %Y %H:%M:%S") + datetime.timedelta(seconds=1)
        time = datetime.datetime.strftime(time, "%d %b %Y %H:%M:%S")
        
        # Get the data on the 1 minute timeframe to be able to create chart at timeframes lower than predefined timeframe.
        # For example if the timeframe is 1day, we get only 1 candle per day, so we use the 1 minute data to create the chart for the current day.
        df = self.load_data(self.symbol, '1m', start_time_for_data, time, load_local=False)
        self.cached_data = pd.concat([self.cached_data, df])
        # For each timeframe, get the data to be the data taken until current query time + last 100 candles. The current candle data has to be taken from query time.
        # Use the idxs to get the current point for each timeframe to take the data from. Then add the new data from cached data for the pending time. Compute open high,low,close, etc etc by aggregating the data.
        imgs, figs = [], []
        
        for i, timeframe in enumerate(self.timeframes):
            current_df = self.data[timeframe].iloc[idxs[timeframe]-self.min_candles:idxs[timeframe]]
            # get the corresponding portion from cached data that lies between times[i] and time
            
            print(times[i], time)
            cached_df = self.cached_data[pd.to_datetime(self.cached_data['OpenTime']) >= times[i]]
            cached_df = cached_df[pd.to_datetime(cached_df['OpenTime']) <= pd.to_datetime(time)]
            print(cached_df)
            # Aggregate the columns
            aggregated = {
                "OpenTime": cached_df["OpenTime"].iloc[0],  # Start time
                "Open": cached_df["Open"].iloc[0],         # First open value
                "High": cached_df["High"].max(),           # Max high
                "Low": cached_df["Low"].min(),             # Min low
                "Close": cached_df["Close"].iloc[-1],      # Last close value
                "Volume": cached_df["Volume"].sum(),       # Total volume
                "CloseTime": cached_df["CloseTime"].iloc[-1],  # End time
                "QuoteAssetVolume": cached_df["QuoteAssetVolume"].sum(),  # Total quote volume
                "NumberOfTrades": cached_df["NumberOfTrades"].sum(),      # Total number of trades
                "TakerBuyBaseAssetVolume": cached_df["TakerBuyBaseAssetVolume"].sum(),  # Total taker buy base
                "TakerBuyQuoteAssetVolume": cached_df["TakerBuyQuoteAssetVolume"].sum(), # Total taker buy quote
                "Ignore": 0.0,
            }

            # Convert the aggregated result to a DataFrame
            aggregated_df = pd.DataFrame([aggregated])
            columns = aggregated_df.columns

            # merge the two dataframes
            df = pd.concat([current_df[columns], aggregated_df[columns]])
            # add indicators
            df = self.fetcher.add_indicator(df, self.indicators)

            print(df['CloseTime'].tail())
            img, fig = self.fetcher.plot_candlestick_and_volume(df, timeframe)
            imgs.append(img)
            figs.append(fig)
        plt.show()
        return imgs, figs

if __name__ == "__main__":
    env = TradingEnvironment(
        api_key="", 
        api_secret="", 
        symbol="SOLUSDT",
        timeframes=['15m', '1h', '4h', '1d'], 
        from_date="1 Jan 2024 00:00:00", 
        start_time="1 Jan 2024 01:00:00",
        end_date="1 Jan 2025 00:00:00",
        indicators=['rsi', 'vwap', 'ema_20', 'ema_200'],
        load_local=True,
        save_path="downloaded_data"
    )
    data = env.get_data()
    start_time = env.get_minimum_starting_time()
    _, times = env.get_index_from_time(start_time)

    env.get_chart_data("1 Nov 2024 11:16:00")
    env.get_chart_data("1 Nov 2024 11:28:00")
