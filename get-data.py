from binance.client import Client
import pandas as pd
import datetime
import time
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv('envs/.env')

class BinanceDataFetcher:
    def __init__(
        self, 
        api_key, 
        api_secret
    ):
        """
        Initialize the Binance client with the provided API key and secret.
        """
        self.client = Client(api_key, api_secret)
        self.api_limit = 1000
        self.data = {}

    def _get_klines(self, symbol, interval, start_time, end_time):
        """
        Fetch candlestick data from Binance for a specific time range.
        """
        try:
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_time,
                end_str=end_time,
                limit=self.api_limit,  # Max limit per API call
            )
            return klines
        except Exception as e:
            print(f"Error fetching klines: {e}")
            return []

    def get_historical_data(self, symbol, interval, start_date):
        """
        Fetch all historical data from the start date to the current time.
        Args:
            symbol: Trading pair (e.g., "BTCUSDT").
            interval: Timeframe (e.g., "15m", "4h", "1d").
            start_date: Start date as a string (e.g., "1 Jan 2020").
        Returns:
            DataFrame containing the historical data.
        """
        # Convert start_date to timestamp
        if symbol not in self.data:
            self.data[symbol] = {}
        if interval not in self.data[symbol]:
            self.data[symbol][interval] = []
            start_time = datetime.datetime.strptime(start_date, "%d %b %Y")
            start_timestamp = int(start_time.timestamp() * self.api_limit)
        else:
            start_timestamp = self.data[symbol][interval][-1][6] + 1
        
        # Current time
        end_timestamp = int(time.time() * self.api_limit)

        # Placeholder for all data
        all_klines = []
        current_start = start_timestamp

        while current_start < end_timestamp:
            # Fetch klines
            klines = self._get_klines(
                symbol=symbol,
                interval=interval,
                start_time=current_start,
                end_time=end_timestamp
            )
            if not klines:
                break

            # Add data and update current_start to the last fetched timestamp
            all_klines.extend(klines)
            current_start = klines[-1][6] + 1  # CloseTime + 1ms

        self.data[symbol][interval].extend(all_klines)
        
        # Convert to DataFrame
        df = pd.DataFrame(self.data[symbol][interval], columns=[
            "OpenTime", "Open", "High", "Low", "Close", "Volume", 
            "CloseTime", "QuoteAssetVolume", "NumberOfTrades", 
            "TakerBuyBaseAssetVolume", "TakerBuyQuoteAssetVolume", "Ignore"
        ])
        
        # Convert timestamps to datetime
        df["OpenTime"] = pd.to_datetime(df["OpenTime"], unit='ms')
        df["CloseTime"] = pd.to_datetime(df["CloseTime"], unit='ms')
        return df

    def create_rolling_plots(self, symbol, start_date, end_date, output_dir="plots"):
        """
        Create rolling plots with candlesticks and volume subplots.
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Fetch data for all timeframes
        data_1h = self.get_historical_data(symbol, "1h", start_date)
        data_4h = self.get_historical_data(symbol, "4h", start_date)
        data_1d = self.get_historical_data(symbol, "1d", start_date)
        
        # Convert dates to datetime objects
        start_dt = datetime.datetime.strptime(start_date, "%d %b %Y")
        end_dt = datetime.datetime.strptime(end_date, "%d %b %Y")
        
        # Create 4-hour intervals
        current_time = start_dt
        while current_time <= end_dt:
            # Filter data for rolling window (last 200 entries)
            window_end = current_time
            
            df_1h = data_1h[data_1h['OpenTime'] <= window_end].tail(200)
            df_4h = data_4h[data_4h['OpenTime'] <= window_end].tail(200)
            df_1d = data_1d[data_1d['OpenTime'] <= window_end].tail(200)
            
            # Create figure with subplots
            fig = plt.figure(figsize=(15, 18))  # Increased height for volume subplots
            gs = GridSpec(6, 1, figure=fig, height_ratios=[3,1,3,1,3,1])
            
            # Plot each timeframe
            timeframes = [(df_1h, "1h", 0), (df_4h, "4h", 2), (df_1d, "1d", 4)]
            for idx, (df, tf, pos) in enumerate(timeframes):
                # Create price subplot
                ax1 = fig.add_subplot(gs[pos])
                
                # Plot candlesticks
                up_candles = df[df['Close'] >= df['Open']]
                down_candles = df[df['Close'] < df['Open']]
                
                # Up candles
                ax1.bar(up_candles['OpenTime'], 
                       up_candles['Close'] - up_candles['Open'],
                       bottom=up_candles['Open'],
                       width=0.6,
                       color='green',
                       alpha=0.7)
                ax1.bar(up_candles['OpenTime'],
                       up_candles['High'] - up_candles['Close'],
                       bottom=up_candles['Close'],
                       width=0.1,
                       color='green',
                       alpha=0.7)
                ax1.bar(up_candles['OpenTime'],
                       up_candles['Low'] - up_candles['Open'],
                       bottom=up_candles['Open'],
                       width=0.1,
                       color='green',
                       alpha=0.7)
                
                # Down candles
                ax1.bar(down_candles['OpenTime'],
                       down_candles['Close'] - down_candles['Open'],
                       bottom=down_candles['Open'],
                       width=0.6,
                       color='red',
                       alpha=0.7)
                ax1.bar(down_candles['OpenTime'],
                       down_candles['High'] - down_candles['Open'],
                       bottom=down_candles['Open'],
                       width=0.1,
                       color='red',
                       alpha=0.7)
                ax1.bar(down_candles['OpenTime'],
                       down_candles['Low'] - down_candles['Close'],
                       bottom=down_candles['Close'],
                       width=0.1,
                       color='red',
                       alpha=0.7)
                
                ax1.grid(True)
                ax1.set_title(f'{symbol} - {tf} Timeframe')
                ax1.xaxis.set_major_locator(plt.MaxNLocator(10))
                plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
                
                # Create volume subplot
                ax2 = fig.add_subplot(gs[pos+1], sharex=ax1)
                
                # Color volume bars based on price direction
                volume_colors = ['green' if close >= open else 'red' 
                               for close, open in zip(df['Close'], df['Open'])]
                
                ax2.bar(df['OpenTime'], df['Volume'], 
                       color=volume_colors, alpha=0.7)
                ax2.set_ylabel('Volume')
                ax2.grid(True)
                
                # Only show x-axis labels for volume plots
                if pos < 4:  # Hide x-labels for all but the last pair
                    ax1.set_xticklabels([])
                    ax2.set_xticklabels([])
            
            plt.tight_layout()
            timestamp = current_time.strftime("%Y%m%d_%H%M")
            plt.savefig(f"{output_dir}/{symbol}_{timestamp}.png")
            plt.close()
            
            # Increment by 4 hours
            current_time += timedelta(hours=4)

if __name__ == "__main__":
    # Replace these with your Binance API keys
    API_KEY = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")

    fetcher = BinanceDataFetcher(API_KEY, API_SECRET)

    # Example: Fetch BTCUSDT 15-minute data from 1 Jan 2020 to now
    data1 = fetcher.get_historical_data("SOLUSDT", "1h", "1 Jan 2024")
    data1 = fetcher.get_historical_data("SOLUSDT", "1h", "1 Jan 2024")
    data1.to_csv("SOLUSDT_1h_data.csv", index=False)

    # # Example: Create rolling plots
    # fetcher.create_rolling_plots(
    #     "SOLUSDT",
    #     "1 Jan 2024",
    #     "10 Jan 2024",
    #     output_dir="solana_plots"
    # )
