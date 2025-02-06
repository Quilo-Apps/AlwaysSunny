from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
#from test_backend_code import get_coordinates, fetch_weather_data, process_weather_data  # Import existing functions
import requests
import requests_cache
import pandas as pd
from retry_requests import retry
from datetime import datetime


app = Flask(__name__)
CORS(app)


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
    

    daily_summary_mean = [daily_summary['Clear skies % of day'].mean(), 
                          daily_summary['Avg wind speed'].mean(),
                          daily_summary['Rain Quantity'].mean(),
                          daily_summary['Snow Quantity'].mean(),
                          daily_summary['Always Sunny Score'].mean()]
    return daily_summary_mean




@app.route('/get_sunny_score', methods=['POST'])
def get_sunny_score():
    data = request.get_json()
    
    city = data.get('city')
    province = data.get('province')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    print(city + ' ' + province + ' ' + start_date + ' ' + end_date)

    if not city or not province or not start_date or not end_date:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        
        latitude, longitude = get_coordinates(city, province)
        
        weather_data = fetch_weather_data(latitude, longitude, start_date, end_date)
        

        if weather_data:
            
            processed_data = process_weather_data(weather_data)
            
            
            sunny_score = round(processed_data[-1], 3)
            
            clear_skies = round(processed_data[0], 3)
            wind_speed = round(processed_data[1], 3)
            rain_amount = round(processed_data[2], 3)
            snow_amount = round(processed_data[3], 3)
            return jsonify({
                "city": city,
                "province": province,
                "latitude": latitude,
                "longitude": longitude,
                "weather_data": weather_data,
                "sunny_score": sunny_score,
                "clear_skies": clear_skies,
                "wind_speed": wind_speed,
                "rain_amount": rain_amount,
                "snow_amount": snow_amount
            })
        else:
            return jsonify({"error": "Could not fetch weather data"}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
