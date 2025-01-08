import io
import base64
from anthropic import Anthropic

class TrendAnalysisAgent:
    def __init__(self, api_key):
        self.anthropic = Anthropic(api_key=api_key)
        self.agent_instruction = "You are a professional trader. Your role is to analyze the given candlestick charts. \
            Be as accurate as possible with mentioning price values. When given multiple timeframes of the chart, \
            analyze each one individually, and then combine the analysis from all of them into giving a holistic \
            view of that asset. Your role is to identify key areas of support and resistance in the charts. \
            Each chart contains 2 subplots. The first plot is the candlestick plot containing open, high, \
            low, close information of each candle. The second plot below it contains the volume traded \
            for that given candlestick. The volume plot contains its moving average plotted in orange. \
            Large volumes are highlighted in green, and are determined with the threshold determined by \
            volume_threshold = mean(volume) + 2*std(volume). The volume threshold is indicated on the chart with a dashed line. \
            You must identify all the areas of support and resistance, and \
            List all the levels you see in the chart that act as significant support or resistance based on repeated touches. \
            output your answer in the format(Do not include any other text): \
               < Support: [list of support levels: Reasoning for each level], Resistance: [list of resistance levels: Reasoning for each level]> \
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
                    max_tokens=200,
                    temperature=0.0,
                    messages=[
                            {
                            "role": "user",
                            "content": chart_messages
                        }
                    ]
                )
        return message.content[0].text