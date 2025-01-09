import io
import base64
from anthropic import Anthropic

class MarketAnalysisAgent:
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
            the emas to give a BUY, SELL, or NO_TRADE action. Short term actions are those that are based on the 15m, 1h charts. \
            Long term actions are those that are based on the 4h, 1d charts. Prioritize buying at key levels based on volume confirmation, or RSI divergence etc.\
            output your answer in the format: \
            < Short Term: <BUY, SELL, or NO_TRADE>: <Reasoning for the action> >\
            < Long Term: <BUY, SELL, or NO_TRADE>: <Reasoning for the action> >\
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