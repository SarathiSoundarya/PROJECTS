
from pydantic import BaseModel, Field
from typing import Literal
import requests
from geopy.geocoders import Nominatim
import traceback
from models import azure_chatopenai_model, google_model
from logger.base_logger import get_logger
logger = get_logger(__name__)

class City(BaseModel):
    """City mentioned in the user query."""
    city: str = Field(description="The name of the city mentioned in the user query, return empty string if not found", default="")

class fetchGeoWeatherDetails():
    def __init__(self, query: str):
        self.query = query

    def get_city(self) -> str:
        """Extract the city name from the user query."""
        #steps
        #use a language model to extract the city name from the user query
        structured_llm = google_model.with_structured_output(City)
        result = structured_llm.invoke("Extract the city name/place from the following user query. Return empty string if city not found. User query: " + self.query)
        city_name = result.city
        logger.info(f"Extracted city name: {city_name}")
        return city_name
                
    
    def get_lat_long(self, city: str) -> tuple:
        """Extract the latitude and longitude of the city using a geocoding API."""
        geolocator = Nominatim(user_agent="my_app")

        location = geolocator.geocode(city)
        logger.info(f"Geocoding result for city '{city}': {location}")
        if location:
            logger.info(f"Latitude: {location.latitude}, Longitude: {location.longitude}, Full Address: {location.address}")
            return location
        else:
            logger.error(f"Could not find location for city: {city}")
            return None
           

    def call_weather_api(self, lat: float, lon: float) -> str:
        """Call the weather API using the latitude and longitude to get the current weather conditions."""
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        try:
            r = requests.get(url, timeout=20)
            #typical response from the API
            #         {
            # "latitude": 12.875,
            # "longitude": 77.5,
            # "generationtime_ms": 0.09894371032714844,
            # "utc_offset_seconds": 0,
            # "timezone": "GMT",
            # "timezone_abbreviation": "GMT",
            # "elevation": 840.0,
            # "current_weather_units": {
            #     "time": "iso8601",
            #     "interval": "seconds",
            #     "temperature": "°C",
            #     "windspeed": "km/h",
            #     "winddirection": "°",
            #     "is_day": "",
            #     "weathercode": "wmo code"
            # },
            # "current_weather": {
            #     "time": "2026-02-15T10:45",
            #     "interval": 900,
            #     "temperature": 30.5,
            #     "windspeed": 8.0,
            #     "winddirection": 36,
            #     "is_day": 1,
            #     "weathercode": 1
            # }}

            data = r.json()
            logger.info(f"Weather API response: {data}")
            return data
        except Exception as e:
            logger.error(f"Error fetching weather data: {e} with traceback: {traceback.format_exc()}")
            return {}

    def fetch_archive_data(self, lat: float, lon: float, start_date: str, end_date: str) -> str:
        """Call the weather API using the latitude and longitude to get the historical weather conditions for a specific date range."""

        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&hourly=temperature_2m,relativehumidity_2m,pm10,pm2_5"
        try:
            r = requests.get(url, timeout=20)
            data = r.json()
            logger.info(f"Historical Weather API response: {data}")
            return data
        except Exception as e:
            logger.error(f"Error fetching historical weather data: {e} with traceback: {traceback.format_exc()}")
            return {}

       