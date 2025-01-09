import pandas as pd
import numpy as np

def ema(df, length):
    """
    Calculate Exponential Moving Average (EMA) for a given column.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing the data.
    column (str): The column name for which to calculate the EMA.
    length (int): The span (period) for the EMA.
    
    Returns:
    pd.Series: The EMA values.
    """
    # update the df and return it with the new column
    df[f"ema_{length}"] = df['Close'].ewm(span=length, adjust=False).mean()
    return df


def vwap(df):
    """
    Calculate the Volume Weighted Average Price (VWAP).
    
    Parameters:
    df (pd.DataFrame): DataFrame containing the data with 'High', 'Low', 'Close', 'Volume'.
    
    Returns:
    pd.Series: The VWAP values.
    """
    # vwap = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    # df['vwap'] = vwap
    df['vwap'] = (((df['High'] + df['Low'] + df['Close']) / 3) * df['Volume']).cumsum() / df['Volume'].cumsum()
    return df

def supertrend(df, length=10, multiplier=3):
    
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    # calculate ATR
    price_diffs = [high - low, 
                   high - close.shift(), 
                   close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    # default ATR calculation in supertrend indicator
    atr = true_range.ewm(alpha=1/length,min_periods=length).mean() 
    # df['atr'] = df['tr'].rolling(atr_period).mean()
    
    # HL2 is simply the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    # notice that final bands are set to be equal to the respective bands
    final_upperband = upperband = hl2 + (multiplier * atr)
    final_lowerband = lowerband = hl2 - (multiplier * atr)
    
    # initialize Supertrend column to True
    supertrend = [True] * len(df)
    
    for i in range(1, len(df.index)):
        curr, prev = i, i-1
        
        # if current close price crosses above upperband
        if close[curr] > final_upperband[prev]:
            supertrend[curr] = True
        # if current close price crosses below lowerband
        elif close[curr] < final_lowerband[prev]:
            supertrend[curr] = False
        # else, the trend continues
        else:
            supertrend[curr] = supertrend[prev]
            
            # adjustment to the final bands
            if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                final_lowerband[curr] = final_lowerband[prev]
            if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                final_upperband[curr] = final_upperband[prev]

        # to remove bands according to the trend direction
        if supertrend[curr] == True:
            final_upperband[curr] = np.nan
        else:
            final_lowerband[curr] = np.nan
    
    df['supertrend'] = supertrend
    df['final_lowerband'] = final_lowerband
    df['final_upperband'] = final_upperband

    return df

def supertrend1(df, length=10, multiplier=3):
    # Calculate the True Range (TR)
    df['High_Low'] = df['High'] - df['Low']
    df['High_Close'] = abs(df['High'] - df['Close'].shift(1))
    df['Low_Close'] = abs(df['Low'] - df['Close'].shift(1))
    df['True_Range'] = df[['High_Low', 'High_Close', 'Low_Close']].max(axis=1)

    # Calculate the Average True Range (ATR)
    df['ATR'] = df['True_Range'].rolling(window=length).mean()

    # Calculate the Supertrend
    df['supertrend_upper'] = (df['High'] + df['Low']) / 2 + (multiplier * df['ATR'])
    df['supertrend_lower'] = (df['High'] + df['Low']) / 2 - (multiplier * df['ATR'])

    # Initialize the Supertrend and Trend Direction
    df['Supertrend'] = 0.0
    df['Trend_Direction'] = 0

    for i in range(1, len(df)):
        if df.loc[i - 1, 'Trend_Direction'] == 1:  # Previous trend was up
            df.loc[i, 'Supertrend'] = df.loc[i, 'supertrend_upper'] if df.loc[i, 'Close'] > df.loc[i - 1, 'Supertrend'] else df.loc[i - 1, 'Supertrend']
            df.loc[i, 'Trend_Direction'] = 1 if df.loc[i, 'Close'] > df.loc[i, 'Supertrend'] else -1
        else:  # Previous trend was down
            df.loc[i, 'Supertrend'] = df.loc[i, 'supertrend_lower'] if df.loc[i, 'Close'] < df.loc[i - 1, 'Supertrend'] else df.loc[i - 1, 'Supertrend']
            df.loc[i, 'Trend_Direction'] = -1 if df.loc[i, 'Close'] < df.loc[i, 'Supertrend'] else 1
        
        # Update Upper_Band and Lower_Band
        if df.loc[i, 'Trend_Direction'] == 1:
            df.loc[i, 'supertrend_upper'] = min(df.loc[i, 'supertrend_upper'], df.loc[i - 1, 'supertrend_upper'])
        else:
            df.loc[i, 'supertrend_lower'] = max(df.loc[i, 'supertrend_lower'], df.loc[i - 1, 'supertrend_lower'])

    # Clean up temporary columns
    df.drop(columns=['High_Low', 'High_Close', 'Low_Close', 'True_Range'], inplace=True)

    return df

def rsi(df, length=14):
    """
    Calculate the Relative Strength Index (RSI) for a given column.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing the data.
    column (str): The column name for which to calculate the RSI.
    period (int): The period over which to calculate the RSI (default is 14).
    
    Returns:
    pd.Series: The RSI values.
    """
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    df['rsi'] = rsi
    
    return df

if __name__ == "__main__":
	# Example usage:
	data = {
		'Open': [100, 102, 101, 105, 107, 106, 108, 110, 109, 112],
		'High': [102, 104, 103, 106, 108, 107, 109, 111, 110, 113],
		'Low': [99, 101, 100, 104, 106, 105, 107, 109, 108, 111],
		'Close': [101, 103, 102, 105, 107, 106, 108, 109, 111, 112],
		'Volume': [1000, 1100, 1200, 1300, 1400, 1300, 1200, 1500, 1600, 1700]
	}
	df = pd.DataFrame(data)

	# Calculate EMAs
	df['EMA_20'] = ema(df, 'Close', 20)
	df['EMA_50'] = ema(df, 'Close', 50)
	df['EMA_100'] = ema(df, 'Close', 100)
	df['EMA_200'] = ema(df, 'Close', 200)

	# Calculate VWAP
	df['VWAP'] = vwap(df)

	# Calculate Supertrend
	df = supertrend(df)
 
	# Calculate RSI
	df = calculate_rsi(df, 'Close')

	# Display updated DataFrame with indicators
	print(df)
