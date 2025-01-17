import os
import io
from PIL import Image
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import re
import yaml
from get_data import BinanceDataFetcher
from agents.trend_analysis_agent import TrendAnalysisAgent
from agents.market_analysis_agent import MarketAnalysisAgent
from trading_env.trading_environment import TradingEnvironment

class Trader:
    def __init__(
        self,
        symbol: str,
        timeframes: list,
        from_date: str,
        current_time: str,
        end_date: str,
        indicators: list,
        load_local: bool,
        save_path: str,
        **kwargs
    ):
        self.symbol = symbol
        self.timeframes = timeframes
        self.from_date = from_date
        self.current_time = current_time
        self.end_date = end_date
        self.indicators = indicators
        self.load_local = load_local
        self.save_path = save_path
        self.env = TradingEnvironment(
			api_key=os.getenv("API_KEY"),
			api_secret=os.getenv("API_SECRET"), 
			symbol=self.symbol,
			timeframes=self.timeframes, 
			from_date=self.from_date, 
			current_time=self.current_time,
			end_date=self.end_date,
			indicators=self.indicators,
			load_local=self.load_local,
			save_path=self.save_path
		)
        self.trend_analysis_agent = TrendAnalysisAgent(os.getenv("ANTHROPIC_API_KEY"))
        self.market_analysis_agent = MarketAnalysisAgent(os.getenv("ANTHROPIC_API_KEY"))
        
if __name__ == "__main__":
    load_dotenv('envs/.env')

    with open('configs/trade.yaml', 'r') as file:
        config = yaml.safe_load(file)

    trader = Trader(**config)
    trader.run()