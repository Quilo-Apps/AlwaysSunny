import requests
import requests_cache
import pandas as pd
from retry_requests import retry
from datetime import datetime

# Setup Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)

# Function to get latitude and longitude from city and province/state
def get_coordinates(city, province):
    geocoding_api_key = "6d24a705c3134c52be93f7492280662f"  # Replace if needed
    geocoding_url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        "q": f"{city}, {province}",
        "key": geocoding_api_key,
    }
    response = requests.get(geocoding_url, params=params)
    response.raise_for_status()
    data = response.json()

    if data["results"]:
        location = data["results"][0]["geometry"]
        return location["lat"], location["lng"]
    else:
        raise ValueError("Could not find location. Please check the city and province/state names.")

# Function to fetch weather data
def fetch_weather_data(latitude, longitude, start_date, end_date):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "cloudcover,wind_speed_10m,precipitation,snowfall,relative_humidity_2m",
        "daily": "precipitation_sum,precipitation_hours,cloudcover_mean",
        "timezone": "auto"
    }
    try:
        response = retry_session.get(url, params=params).json()
        return response
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

# Function to calculate the Always Sunny Score
def calculate_always_sunny_score(clear_skies, wind_speed, rain_quantity, snow_quantity):
    score = clear_skies  # Clear skies percentage
    score -= (wind_speed if wind_speed > 3 else 0)  # Wind speed (subtract only if > 3 km/h)
    score -= rain_quantity * 1.5  # Rain quantity (mm) adjustment
    score -= snow_quantity * 1.5  # Snow quantity (mm) adjustment
    return max(score, 0)  # Ensure score is not negative

# Function to process weather data
def process_weather_data(weather_data):
    hourly_data = pd.DataFrame(weather_data['hourly'])
    hourly_data['time'] = pd.to_datetime(hourly_data['time'])
    daily_data = pd.DataFrame(weather_data['daily'])
    daily_data['time'] = pd.to_datetime(daily_data['time'])

    # Calculate daily summaries from hourly data
    daily_summary = hourly_data.groupby(hourly_data['time'].dt.date).apply(lambda x: pd.Series({
        'Clear skies % of day': 100 - x['cloudcover'].mean(),
        'Avg wind speed': x['wind_speed_10m'].mean(),
        'Rain Quantity': x['precipitation'].sum(),  # Total rain quantity
        'Snow Quantity': x['snowfall'].sum(),  # Total snow quantity
    }))

    # Merge summaries
    daily_summary = daily_summary.reset_index()
    daily_summary['time'] = pd.to_datetime(daily_summary['time'])

    # Calculate Always Sunny Score and its components
    daily_summary['Always Sunny Score'] = daily_summary.apply(
        lambda row: calculate_always_sunny_score(
            row['Clear skies % of day'],
            row['Avg wind speed'],
            row['Rain Quantity'],
            row['Snow Quantity']
        ), axis=1
    )

    # Print data as a table for debugging
    print("\nWeather Metrics and Always Sunny Score:")
    print(daily_summary.to_string(index=False))

# Main function
def main():
    print("Welcome to the Always Sunny Score Calculator!")

    # Prompt the user for input
    while True:
        city = input("Enter the city: ").strip()
        if city:
            break
        print("City name cannot be empty. Please try again.")

    while True:
        province = input("Enter the province/state: ").strip()
        if province:
            break
        print("Province/state name cannot be empty. Please try again.")

    while True:
        start_date = input("Enter the start date (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            break
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")

    while True:
        end_date = input("Enter the end date (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
            break
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")

    try:
        # Get coordinates
        latitude, longitude = get_coordinates(city, province)
        print(f"Coordinates for {city}, {province}: {latitude}, {longitude}")

        # Fetch weather data
        weather_data = fetch_weather_data(latitude, longitude, start_date, end_date)
        if weather_data:
            process_weather_data(weather_data)
        else:
            print("Error: Could not fetch weather data.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
