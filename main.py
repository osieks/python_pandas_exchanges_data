import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from datetime import datetime

# Load config file
with open('config.json', 'r') as file:
    config = json.load(file)

short_term_avg = config["moving_averages"]["short_term"]
long_term_avg = config["moving_averages"]["long_term"]
coins = config["coins"]
days = config["date_range"]["days"]


# Function to request data from Binance API
def get_binance_data(symbol, interval='1d', limit=100):
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
        print(f"Error fetching data from Binance: {response.status_code}")
        return None

# Convert raw Binance data into a DataFrame
def binance_data_to_df(data):
    df = pd.DataFrame(data, columns=[
        'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume',
        'Close Time', 'Quote Asset Volume', 'Number of Trades', 
        'Taker Buy Base Asset Volume', 'Taker Buy Quote Asset Volume', 'Ignore'
    ])
    df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
    numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df[numeric_columns] = df[numeric_columns].astype(float)
    return df

# Function to get historical data from CoinGecko API
def get_coingecko_data(symbol_id, vs_currency='usd', days=100):
    base_url = f"https://api.coingecko.com/api/v3/coins/{symbol_id}/market_chart"
    params = {
        'vs_currency': vs_currency,
        'days': days
    }
    
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data['prices']  # Time and price
    elif response.status_code == 404:
        print(f"Error fetching data from CoinGecko: {response.status_code} - Resource not found")
        return None
    else:
        print(f"Error fetching data from CoinGecko: {response.status_code}")
        return None

# Convert CoinGecko data into a DataFrame
def coingecko_data_to_df(data):
    df = pd.DataFrame(data, columns=['Timestamp', 'Price'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df.set_index('Timestamp', inplace=True)
    return df

# Merge Binance and CoinGecko data on timestamps (using outer join)
def combine_dataframes(df_binance, df_coingecko):
    df_combined = pd.merge(df_binance, df_coingecko, how='outer', left_on='Open Time', right_index=True)
    df_combined.rename(columns={'Open': 'Binance Price', 'Price': 'CoinGecko Price'}, inplace=True)

    df_combined['Binance Price'] = pd.to_numeric(df_combined['Binance Price'], errors='coerce')
    df_combined['CoinGecko Price'] = pd.to_numeric(df_combined['CoinGecko Price'], errors='coerce')
    
    df_combined['Average Price'] = df_combined[['Binance Price', 'CoinGecko Price']].mean(axis=1)

    return df_combined

# Function to calculate moving averages and the average of those
def calculate_moving_averages(df_combined, short_term_avg, long_term_avg):
    df_combined[f'MA{short_term_avg} Average'] = df_combined['Average Price'].rolling(window=short_term_avg).mean()
    df_combined[f'MA{long_term_avg} Average'] = df_combined['Average Price'].rolling(window=long_term_avg).mean()
    return df_combined

def calculate_trendline(x, y):
    mask = ~np.isnan(y)
    x_clean = x[mask]
    y_clean = y[mask]
    
    x_numeric = np.arange(len(x_clean)).reshape(-1, 1)
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric.flatten(), y_clean)
    
    full_x_numeric = np.arange(len(x))
    line = slope * full_x_numeric + intercept
    
    return line

# Function to visualize data
def plot_data(df_combined, short_term_avg, long_term_avg, coin_coingecko):
    plt.figure(figsize=(15, 8))
    
    df_combined = df_combined.sort_values('Open Time')
    x = df_combined['Open Time']
    
    average_trendline = calculate_trendline(x, df_combined['Average Price'].values)
    
    plt.plot(x, df_combined['Binance Price'], label='Binance Price', color='yellow', alpha=0.6)
    plt.plot(x, df_combined['CoinGecko Price'], label='CoinGecko Price', color='green', alpha=0.6)
    plt.plot(x, df_combined[f'MA{short_term_avg} Average'], label=f'MA{short_term_avg} Average', color='purple', linestyle='--')
    plt.plot(x, df_combined[f'MA{long_term_avg} Average'], label=f'MA{long_term_avg} Average', color='blue', linestyle='--')
    
    plt.plot(x, average_trendline, label='Binance Trend', color='red', linestyle='-.')
    plt.grid(visible=True, linestyle='--', linewidth=0.5, color='grey', alpha=0.7)

    plt.title(f"{coin_coingecko} price comparison with Moving Averages and Trend Lines")
    plt.xlabel('Date')
    plt.ylabel('Price (USDT)')
    plt.legend()
    plt.tight_layout()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'{coin_coingecko}_analysis_{timestamp}.png'
    
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved as: {filename}")

    plt.show()

# Main function to orchestrate the process
def main():
    for coin_binance, coin_coingecko in coins.items():
        print(f"Fetching data for {coin_binance} from Binance...")
        binance_data = get_binance_data(coin_binance)
        df_binance = binance_data_to_df(binance_data)

        print(f"Fetching data for {coin_coingecko} from CoinGecko...")
        coingecko_data = get_coingecko_data(coin_coingecko, days=days)
        df_coingecko = coingecko_data_to_df(coingecko_data)

        print(f"Combining data for {coin_binance} from Binance and CoinGecko...")
        df_combined = combine_dataframes(df_binance, df_coingecko)

        print("Calculating moving averages...")
        df_combined = calculate_moving_averages(df_combined, short_term_avg, long_term_avg)

        print(f"Plotting data for {coin_binance}...")
        plot_data(df_combined, short_term_avg, long_term_avg, coin_coingecko)

if __name__ == "__main__":
    main()
