import os
import io
from PIL import Image
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import re
from get_data import BinanceDataFetcher
from agents.trend_analysis_agent import TrendAnalysisAgent

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
        self.fetcher = BinanceDataFetcher(self.api_key, self.api_secret)
    
    def load_data(self, symbol: str="SOLUSDT", timeframe: str="15m", from_date: str="1 Jan 2024"):
        if self.load_local:
            df = pd.read_csv(f"{self.base_path}/{symbol}_{timeframe}_data.csv")
            print(df.dtypes)
            return df
        else:
            return self.fetcher.get_historical_data(symbol, timeframe, from_date)

    def analyze_trend(self, symbol, timeframes, from_date: str="1 Jan 2024"):
        data, plots, images = {}, [], []
        for timeframe in timeframes:
            data[timeframe] = self.load_data(symbol, timeframe, from_date)
        
        for timeframe in timeframes:
            img, fig = self.fetcher.plot_candlestick_and_volume(data[timeframe][-200:], timeframe)
            plots.append(fig)
            images.append(img)
            # convert the figure to a pil image
            # fig.show(title="My Image")
#       
        output_message = self.trend_analysis_agent.analyze(images)
        
        # Updated regex to capture levels in both Support and Resistance sections
        levels = re.findall(r'\d+:', output_message)
        levels = [float(level.strip(':')) for level in levels]

        # Find the index of the "4h" timeframe
        if "4h" in timeframes:
            index_4h = timeframes.index("4h")
            fig_4h = plots[index_4h]
            
            plt.figure(fig_4h.number)
            ax = fig_4h.axes[0]  # Access the first subplot
            for level in levels:
                ax.axhline(y=level, color='r', linestyle='--')
            # convert the figure to a pil image
            img_buf = io.BytesIO()
            plt.savefig(img_buf, format='png')
            img_buf.seek(0)
            img = Image.open(img_buf).convert('RGB')
            # save the image to a file
            img.save(f"trend_analysis_{symbol}_4h.png")
        
        print(output_message)

if __name__ == "__main__":
    load_dotenv('envs/.env')

    load_local = False

    analyzer = TrendAnalyzer(load_local)

    analyzer.analyze_trend("SOLUSDT", ["15m", "1h", "4h", "1d"])
    