import os
import io
from PIL import Image
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import re
from get_data import BinanceDataFetcher
from agents.trend_analysis_agent import TrendAnalysisAgent
from agents.market_analysis_agent import MarketAnalysisAgent

class TrendAnalyzer:
    def __init__(
        self,
        load_local=True,
        base_path="data"
    ):
        self.load_local = load_local
        self.base_path = base_path
        self.api_key = os.getenv("API_KEY")
        self.api_secret = os.getenv("API_SECRET")
        self.trend_analysis_agent = TrendAnalysisAgent(os.getenv("ANTHROPIC_API_KEY"))
        self.market_analysis_agent = MarketAnalysisAgent(os.getenv("ANTHROPIC_API_KEY"))
        self.fetcher = BinanceDataFetcher(self.api_key, self.api_secret)
    
    def load_data(self, symbol: str="SOLUSDT", timeframe: str="15m", from_date: str="1 Jan 2024", end_date: str=None):
        if self.load_local:
            df = pd.read_csv(f"{self.base_path}/{symbol}_{timeframe}_data.csv")
            return df
        else:
            return self.fetcher.get_historical_data(symbol, timeframe, from_date, end_date)

    def analyze_trend(
        self, 
        symbol, 
        timeframes, 
        from_date: str="1 Jan 2024", 
        end_date: str=None, 
        indicators: list=['rsi', 'vwap', 'supertrend']
    ):
        data, plots, images = {}, [], []
        for timeframe in timeframes:
            data[timeframe] = self.load_data(symbol, timeframe, from_date, end_date)
            data[timeframe] = self.fetcher.add_indicator(data[timeframe], indicators)
            data[timeframe].to_csv(f"{self.base_path}/{symbol}_{timeframe}_data.csv", index=False)
        
        for timeframe in timeframes:
            img, fig = self.fetcher.plot_candlestick_and_volume(data[timeframe].tail(200), timeframe)
            plots.append(fig)
            images.append(img)
            # convert the figure to a pil image
            # fig.show(title="My Image")
#       
        output_message = self.trend_analysis_agent.analyze(images)
        print(output_message)
        
        # Updated regex to capture levels in both Support and Resistance sections
        # levels = re.findall(r'\d+:', output_message)
        levels = re.findall(r'(\d+\.\d+|\d+):', output_message)
        levels = [float(level.strip(':')) for level in levels]
        print(levels)
        
        stage2_charts = []
        for timeframe in timeframes:
            fig = self.fetcher.plot_indicators(data[timeframe].tail(200), indicators)
            for level in levels:    
                fig.axes[0].axhline(y=level, color='r', linestyle='--')
            img_buf = io.BytesIO()
            plt.savefig(img_buf, format='png')
            img_buf.seek(0)
            img = Image.open(img_buf).convert('RGB')
            # save the image to a file
            img.save(f"trend_analysis_{symbol}_{timeframe}.png")
            stage2_charts.append(img)

        output_message = self.market_analysis_agent.analyze(stage2_charts)
        
        print(output_message)

if __name__ == "__main__":
    load_dotenv('envs/.env')

    load_local = False

    analyzer = TrendAnalyzer(load_local)

    analyzer.analyze_trend("SOLUSDT", ["15m", "1h", "4h", "1d"], from_date="11 Nov 2023", end_date="29 May 2024", indicators=['ema_20', 'ema_200', 'rsi'])
    # analyzer.analyze_trend("SOLUSDT", ["15m", "1h", "4h", "1d"], indicators=['vwap'])
    