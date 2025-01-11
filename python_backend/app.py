import requests
import requests_cache
import pandas as pd
from retry_requests import retry
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS

# Setup Flask app
app = Flask(__name__)
CORS(app)

# Setup Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)

# Function to get latitude and longitude from city and province using OpenCage Geocoder
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
        raise ValueError("Could not find location. Please check the city and province names.")

# Function to calculate the Always Sunny Score
def calculate_always_sunny_score(clear_skies, wind_speed, rain_quantity, snow_quantity):
    score = clear_skies  # Clear skies percentage
    score -= (wind_speed if wind_speed > 3 else 0)  # Wind speed (subtract only if > 3 km/h)
    score -= rain_quantity * 1.5  # Rain quantity (mm) adjustment
    score -= snow_quantity * 1.5  # Snow quantity (mm) adjustment
    return max(score, 0)  # Ensure score is not negative

# Fetch and process weather data
def fetch_weather_data(latitude, longitude, start_date, end_date):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "cloudcover,wind_speed_10m,precipitation,snowfall,relative_humidity_2m",
        "daily": "precipitation_sum,precipitation_hours,cloudcover_mean",  # Removed wind_speed_10m_mean
        "timezone": "auto"
    }
    try:
        response = retry_session.get(url, params=params).json()
        return response
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

# Process and calculate metrics
def process_weather_data(weather_data):
    hourly_data = pd.DataFrame(weather_data['hourly'])
    hourly_data['time'] = pd.to_datetime(hourly_data['time'])
    daily_data = pd.DataFrame(weather_data['daily'])
    daily_data['time'] = pd.to_datetime(daily_data['time'])

    # Calculate daily summaries from hourly data
    daily_summary = hourly_data.groupby(hourly_data['time'].dt.date).apply(lambda x: pd.Series({
        'Clear skies % of day': 100 - x['cloudcover'].mean(),
        'Wind % of Day': (x['wind_speed_10m'] > 5).mean() * 100,  # Windy hours percentage
        'Avg wind speed': x['wind_speed_10m'].mean(),
        'Rain Quantity': x['precipitation'].sum(),  # Total rain quantity
        'Snow Quantity': x['snowfall'].sum(),  # Total snow quantity
        'Humidity %': x['relative_humidity_2m'].mean()
    }))

    # Convert daily_summary index to datetime and align it with daily_data
    daily_summary = daily_summary.reset_index()
    daily_summary['time'] = pd.to_datetime(daily_summary['time'])

    # Merge the summaries with daily_data (excluding wind_speed_10m_mean)
    final_summary = daily_summary.merge(daily_data[['time', 'precipitation_sum', 'precipitation_hours', 'cloudcover_mean']], on='time', how='inner')

    # Calculate Always Sunny Score and its components
    final_summary['Always Sunny Score'] = final_summary.apply(
        lambda row: calculate_always_sunny_score(
            row['Clear skies % of day'],
            row['Avg wind speed'],
            row['Rain Quantity'],  # Use total rain quantity
            row['Snow Quantity']   # Use total snow quantity
        ), axis=1
    )

    # Add columns for the individual components of the Always Sunny Score
    final_summary['Clear Skies Score'] = final_summary['Clear skies % of day']
    final_summary['Wind Penalty'] = final_summary['Avg wind speed'].apply(lambda x: x if x > 3 else 0)
    final_summary['Rain Penalty'] = final_summary['Rain Quantity'] * 1.5
    final_summary['Snow Penalty'] = final_summary['Snow Quantity'] * 1.5

    # Reorder columns to place 'Always Sunny Score' last
    cols = list(final_summary.columns)
    cols.remove('Always Sunny Score')
    cols.append('Always Sunny Score')
    final_summary = final_summary[cols]

    return final_summary.to_dict(orient="records")  # Convert to dictionary for JSON response

# Flask route to get weather data and score
@app.route('/get_sunny_score', methods=['POST'])
def get_weather_data():
    # Access the incoming JSON data
    data = request.get_json()  
    print("Received Data:", data)  # Debugging line

    city = data.get('city')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')

    # Debugging prints for start_date and end_date
    print(f"Start Date: {start_date_str}, End Date: {end_date_str}")

    # Ensure that all required fields are present
    if not start_date_str or not end_date_str:
        return jsonify({"error": "start_date and end_date are required."}), 400

    # Convert string dates to datetime objects
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

    # Proceed with the rest of your logic
    try:
        latitude, longitude = get_coordinates(city, 'ON')  # Assuming 'ON' as the default for province
        weather_data = fetch_weather_data(latitude, longitude, start_date_str, end_date_str)
        if weather_data:
            weather_table = process_weather_data(weather_data)

            # Extract the first day's 'Always Sunny Score' (or choose your desired logic)
            sunny_score = weather_table[0]['Always Sunny Score'] if weather_table else None
            if sunny_score is not None:
                return jsonify({'sunny_score': sunny_score})  # Only return sunny_score
            else:
                return jsonify({"error": "No sunny score available."}), 500
        else:
            return jsonify({"error": "Error fetching weather data."}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 400



# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)
