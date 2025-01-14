import io
import base64
from anthropic import Anthropic

class TradingAgent:
    def __init__(self, api_key):
        self.anthropic = Anthropic(api_key=api_key)
        self.agent_instruction = "You are a professional trader. Your role is to analyze the given candlestick charts. \
            Be as accurate as possible with mentioning price values. When given multiple timeframes of the chart, \
            analyze each one individually, and then combine the analysis from all of them into giving a holistic \
            view of that asset. Your role is to identify whether the user should BUY, SELL, or take NO_TRADE action. \
            Each chart contains 3 subplots. The first plot is the candlestick plot containing open, high, \
            low, close information of each candle. Horizontal dashed lines indicate regions of support or resistance \
            The blue line represents the 20 ema, and the orange line represents the 200 ema. \
            The second plot below it contains the volume traded for that given candlestick. \
            The volume plot contains its moving average plotted in orange. \
            Large volumes are highlighted in green, and are determined with the threshold determined by \
            volume_threshold = mean(volume) + 2*std(volume). The volume threshold is indicated on the chart with a dashed line. \
            The third plot below contains the RSI for the chart. \
            Your role is to analyze all the available charts, combine the signals obtained from support-resistance, volume, RSI, and \
            the emas to give a BUY, SELL, or NO_TRADE action. \
            You will receive the following information in addition to the charts: \
            1. An initial analysis from a market_analysis_agent. This will contain a BUY, SELL, or NO_TRADE action in addition to the reasoning. \
			2. The current portfolio of the user as a dictionary with all prices in USD. Eg {USD:900, BTC:100}\
			3. Risk-reward tolerance of the user. Eg 2:1 \
			4. Current trades the user has open. Eg if the user is in no trades, then the value is an empty list. else the input is of format: {<symbol>: <entry_price>, <exit_price>, <stop_loss>, <take_profit>} \
			You must take into account the current portfolio, risk-reward tolerance, and current trades when making your decision. \
			Based on all the infomation available to you, you must give a BUY, SELL, or NO_TRADE action. \
			If at any point you are not sure about the action, you must give a NO_TRADE action. \
			If at any point you feel the current market conditions are against the target of the current trade, you must exit the trade. \
			You must trade to maximize the return on investment. You are allowed to take a loss on a trade if it is a small loss. \
			You can take trades both on short term(<4h) and medium term(4h). You must indicate a BUY or SELL action only when the action can be executed immedietely. \
			When your action is a BUY or SELL, the action is executed immedietely at the current price. \
   			Monitor current portfolio value based on the risk-reward tolerance to exit trades accordingly and exit trades if the price moves against the target. \
   			Your output must strictly be in the following format: \
            <<BUY, SELL, or NO_TRADE>: <Exit Price>: <Reasoning for the action> >\
		"
            
        self.trading_agent_message = {"type": "text", "text": self.agent_instruction}

    def analyze(self, images):
        chart_messages = [self.trading_agent_message]
        for image in images:
            img_buffer = io.BytesIO()
            image.save(img_buffer, format="JPEG")
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            chart_messages.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": img_base64
                }
            })
        
        message = self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=300,
                    temperature=0.0,
                    messages=[
                            {
                            "role": "user",
                            "content": chart_messages
                        }
                    ]
                )
        return message.content[0].text