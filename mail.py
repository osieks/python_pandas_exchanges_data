import requests
import pandas as pd
import matplotlib.pyplot as plt

# Function to request data from Binance
def get_binance_data(symbol, interval='1d', limit=200):
    base_url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol.upper(),
        'interval': interval,
        'limit': limit
    }
    
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data: {response.status_code}")
        return None

# Convert raw data into a DataFrame
def binance_data_to_df(data):
    df = pd.DataFrame(data, columns=[
        'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume',
        'Close Time', 'Quote Asset Volume', 'Number of Trades', 
        'Taker Buy Base Asset Volume', 'Taker Buy Quote Asset Volume', 'Ignore'
    ])
    print(df['Open Time'])
    df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
    print(df['Open Time'])
    df['Close Time'] = pd.to_datetime(df['Close Time'], unit='ms')
    numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df[numeric_columns] = df[numeric_columns].astype(float)
    return df

# Example usage
symbol = "BTCUSDT"
data = get_binance_data(symbol)
df = binance_data_to_df(data)

# Calculate moving averages
df['MA20'] = df['Close'].rolling(window=20).mean()
df['MA50'] = df['Close'].rolling(window=100).mean()

# Visualize the data
plt.figure(figsize=(12,6))
plt.plot(df['Open Time'], df['Close'], label='Close Price', color='blue')
plt.plot(df['Open Time'], df['MA20'], label='20-Day MA', color='orange')
plt.plot(df['Open Time'], df['MA50'], label='100-Day MA', color='green')
plt.title(f"{symbol} Price with Moving Averages")
plt.xlabel('Date')
plt.ylabel('Price (USDT)')
plt.legend()
plt.show()
