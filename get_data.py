import os
import datetime
import time
import io
from dotenv import load_dotenv
from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt
from binance.client import Client
import mplfinance as mpf

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
        numeric_columns = [
            "Open", "High", "Low", "Close", "Volume",
            "QuoteAssetVolume", "NumberOfTrades",
            "TakerBuyBaseAssetVolume", "TakerBuyQuoteAssetVolume"
        ]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    def plot_candlestick_and_volume(self, df, timeframe,figsize=(20, 10)):
        """
        Creates separate candlestick charts with volume for each dataframe.

        Parameters:
            dataframes (list): List of dataframes, each containing the required columns.
            figsize (tuple): Tuple for figure size.
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, 
                                    gridspec_kw={'height_ratios': [3, 1]}, 
                                    sharex=True)
                        
        # Convert data for mplfinance
        df_mpf = df.copy()
        
        # Convert OpenTime to datetime if it's not already
        df_mpf['OpenTime'] = pd.to_datetime(df_mpf['OpenTime'])
        df_mpf.set_index('OpenTime', inplace=True)
            
        # Plot candlesticks using mplfinance
        mpf.plot(df_mpf, type='candle', style='charles',
            ax=ax1, volume=False, 
            ylabel='Price',
            datetime_format='%Y-%m-%d %H:%M',
            show_nontrading=False
        )
    
        # Precompute volume metrics
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Threshold'] = df['Volume'].mean() + 2 * df['Volume'].std()
        df['IsSpike'] = df['Volume'] > df['Volume_Threshold']
        
        # Plot volume
        colors = ['green' if spike else 'red' for spike in df['IsSpike']]
        ax2.bar(df['OpenTime'], df['Volume'], color=colors, alpha=0.3, label='Volume')
        ax2.plot(df['OpenTime'], df['Volume_MA'], color='orange', label='Volume MA', linewidth=1)
        ax2.axhline(y=df['Volume_Threshold'].iloc[0], color='purple', 
                    linestyle='--', label='Spike Threshold', alpha=0.5)
        
        # Adjust legends and labels
        ax1.legend(loc='upper left', fontsize=10)
        ax2.legend(loc='upper right', fontsize=10)
        ax2.set_ylabel('Volume', fontsize=12)
        
        # Set title
        plt.title(f'{timeframe} Timeframe Analysis', fontsize=14)
            
        # Display every 10th tick on the x-axis for the price chart
        xticks = df['OpenTime'].iloc[::10]  # Every 10th timestamp
        ax1.set_xticks(xticks)
        ax1.set_xticklabels([pd.to_datetime(x).strftime('%Y-%m-%d\n%H:%M') for x in xticks], rotation=90)
        
        # Save figure
        plt.tight_layout()
        plt.savefig(f'market_analysis_{timeframe}.png', bbox_inches='tight', dpi=300)
        
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png')
        img_buf.seek(0)
        img = Image.open(img_buf).convert('RGB')
        
        return img, fig    

if __name__ == "__main__":
    load_dotenv('envs/.env')
    # Replace these with your Binance API keys
    API_KEY = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")

    load_local = True
    fetcher = BinanceDataFetcher(API_KEY, API_SECRET)

    # Example: Fetch BTCUSDT 15-minute data from 1 Jan 2020 to now
    if load_local:
        data_15m = pd.read_csv("SOLUSDT_15m_data.csv")
        data_1h = pd.read_csv("SOLUSDT_1h_data.csv")
        data_4h = pd.read_csv("SOLUSDT_4h_data.csv")
        data_1d = pd.read_csv("SOLUSDT_1d_data.csv")
    else:
        data_15m = fetcher.get_historical_data("SOLUSDT", "15m", "1 Jan 2024")
        data_1h = fetcher.get_historical_data("SOLUSDT", "1h", "1 Jan 2024")
        data_4h = fetcher.get_historical_data("SOLUSDT", "4h", "1 Jan 2024")
        data_1d = fetcher.get_historical_data("SOLUSDT", "1d", "1 Jan 2024")
        
        data_15m.to_csv("SOLUSDT_15m_data.csv", index=False)
        data_1h.to_csv("SOLUSDT_1h_data.csv", index=False)
        data_4h.to_csv("SOLUSDT_4h_data.csv", index=False)
        data_1d.to_csv("SOLUSDT_1d_data.csv", index=False)
        
    fetcher.plot_candlestick_and_volume(data_15m[-200:], "15m")
    fetcher.plot_candlestick_and_volume(data_1h[-200:], "1h")
    fetcher.plot_candlestick_and_volume(data_4h[-200:], "4h")
    fetcher.plot_candlestick_and_volume(data_1d[-200:], "1d")

    # plt.figure(figsize=(12, 6))
    # fetcher.plot_candle_with_volume_profile("BTCUSDT", data1.iloc[0])
    # plt.show()

    # # Example: Create rolling plots
    # fetcher.create_rolling_plots(
    #     "SOLUSDT",
    #     "1 Jan 2024",
    #     "10 Jan 2024",
    #     output_dir="solana_plots"
    # )
