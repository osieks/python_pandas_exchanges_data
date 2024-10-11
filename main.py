import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from datetime import datetime

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
    else:
        print(f"Error fetching data from CoinGecko: {response.status_code}")
        return None

# Convert CoinGecko data into a DataFrame
def coingecko_data_to_df(data):
    df = pd.DataFrame(data, columns=['Timestamp', 'Price'])
    # Correct the timestamp to datetime conversion
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    # Ensure the 'ms' unit is applied correctly
    df.set_index('Timestamp', inplace=True)  # Set the timestamp as the index
    return df

# Merge Binance and CoinGecko data on timestamps (using outer join)
def combine_dataframes(df_binance, df_coingecko):
    df_combined = pd.merge(df_binance, df_coingecko, how='outer', left_on='Open Time', right_index=True)
    df_combined.rename(columns={'Open': 'Binance Price', 'Price': 'CoinGecko Price'}, inplace=True)
    
    #print(df_combined.head())  
    #print(df_combined.tail())
    #print(df_combined.describe)

    # Calculate average price between Binance and CoinGecko
    df_combined['Average Price'] = df_combined[['Binance Price', 'CoinGecko Price']].mean(axis=1)

    return df_combined

# Function to calculate moving averages and the average of those
def calculate_moving_averages(df_combined):
    df_combined['MA20 Average'] = df_combined['Average Price'].rolling(window=20).mean()

    df_combined['MA50 Average'] = df_combined['Average Price'].rolling(window=50).mean()

    return df_combined

def calculate_trendline(x, y):
    # Remove NaN values
    mask = ~np.isnan(y)
    x_clean = x[mask]
    y_clean = y[mask]
    
    # Convert datetime to numerical value for regression
    x_numeric = np.arange(len(x_clean)).reshape(-1, 1)
    
    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        x_numeric.flatten(), y_clean)
    
    # Calculate trend line for the full range of x values
    full_x_numeric = np.arange(len(x))
    line = slope * full_x_numeric + intercept
    
    return line

# Function to visualize data
def plot_data(df_combined):
    plt.figure(figsize=(15, 8))
    
    # Ensure data is sorted by date
    df_combined = df_combined.sort_values('Open Time')
    
    # Get x-axis data
    x = df_combined['Open Time']
    
    # Calculate single trend line based on average price
    average_trendline = calculate_trendline(x, df_combined['Average Price'].values)
    
    # Plot prices and moving averages
    plt.plot(x, df_combined['Binance Price'], label='Binance Price', color='yellow', alpha=0.6)
    plt.plot(x, df_combined['CoinGecko Price'], label='CoinGecko Price', color='green', alpha=0.6)
    plt.plot(x, df_combined['MA20 Average'], label='MA20 Average', color='purple', linestyle='--')
    plt.plot(x, df_combined['MA50 Average'], label='MA50 Average', color='blue', linestyle='--')
    
    # Plot trend lines
    plt.plot(x, average_trendline, label='Binance Trend', color='red', linestyle='-.')

    # Add grid lines
    plt.grid(visible=True, linestyle='--', linewidth=0.5, color='grey', alpha=0.7)

    plt.title("Cryptocurrency Price Comparison with Moving Averages and Trend Lines")
    plt.xlabel('Date')
    plt.ylabel('Price (USDT)')
    plt.legend()
    plt.tight_layout()

     # Generate filename with current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'crypto_analysis_{timestamp}.png'
    
    # Save the plot
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved as: {filename}")

    plt.show()

# Main function to orchestrate the process
def main():
    symbol = "BTCUSDT"
    symbol_id = "bitcoin"
    
    # Fetch data from Binance
    print("Fetching data from Binance...")
    binance_data = get_binance_data(symbol)
    df_binance = binance_data_to_df(binance_data)

    # Fetch data from CoinGecko
    print("Fetching data from CoinGecko...")
    coingecko_data = get_coingecko_data(symbol_id)
    df_coingecko = coingecko_data_to_df(coingecko_data)

    # Combine the two data sources
    print("Combining Binance and CoinGecko data...")
    df_combined = combine_dataframes(df_binance, df_coingecko)

    # Calculate moving averages and the average of those
    print("Calculating moving averages...")
    df_combined = calculate_moving_averages(df_combined)

    # Visualize the data
    print("Plotting the data...")
    plot_data(df_combined)

# The standard Python entry point
if __name__ == "__main__":
    main()
