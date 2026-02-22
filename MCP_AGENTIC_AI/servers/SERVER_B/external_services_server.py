import uuid
from mcp.server.fastmcp import FastMCP
import requests
from tool_utilities import fetchGeoWeatherDetails
import sqlite3
import pandas as pd
from logger.base_logger import get_logger
logger = get_logger(__name__)
import os
from pathlib import Path
import traceback

mcp = FastMCP("External Services Server", host="0.0.0.0", port=7001)


#tool weather app to get current weather conditions for a city mentioned in the user query
@mcp.tool()
def open_weather_app(query: str) -> str:
    """Get information about current weather conditions for a city in the user query. Only use it when the user asks about current weather and not the conditions over a period"""
    try:
        logger.info(f"In the open_weather_app tool, received query: {query}")
        fetch_weather_details = fetchGeoWeatherDetails(query)
        #extract the city name from the user query
        city = fetch_weather_details.get_city()
        logger.info(f"Extracted city: {city}")
        if city:
            #extract the latitude and logitude of the city using a geocoding API
            location = fetch_weather_details.get_lat_long(city)
            if location:
                lat, long = location.latitude, location.longitude
                logger.info(f"Extracted latitude: {lat}, longitude: {long}")

                #call the weather API using the latitude and longitude to get the current weather conditions
                weather = fetch_weather_details.call_weather_api(lat, long)
                if weather:
                    logger.info("Retrieved weather information successfully using open_weather_app_tool.")
                    return str(weather)              
                
        return "Sorry, I couldn't fetch the weather information at the moment. Please try again later."
    except Exception as e:
        logger.error(f"Error in open_weather_app tool: {e} with traceback:{traceback.format_exc()}")
        return "Sorry, I couldn't fetch the weather information at the moment. Please try again later."

#resource emergency numbers lookup
@mcp.resource("emergency://numbers")
def emergency_numbers() -> dict:
    """emergency helpline numbers"""
    try:
        logger.info("In the emergency_numbers resource tool, returning emergency numbers dictionary.")
        return str({
            "police": "100",
            "ambulance": "102",
            "fire": "101",
            "women_helpline": "1091",
            "national_emergency": "112",
            "child_helpline": "1098",
            "road_accident": "1073",
        })
    except Exception as e:
        logger.error(f"Error in emergency_numbers resource tool: {e} with traceback:{traceback.format_exc()}")
        return "Sorry, I couldn't fetch the emergency numbers at the moment. Please try again later."

#tool to find nearby places like hospital, police, pharmacy etc based on the city/place 
@mcp.tool()
def find_nearby(place: str, category: str, radius: int = 2000) -> dict:
    """b
    Find nearby places like hospital, police, pharmacy.
    Possible categories: hospital, police, pharmacy, school, restaurant, atm, bank, fire_station, parking, fuel, 
    Radius is in meters, default is 2000m.
    """
    try:
        logger.info(f"In the find_nearby tool, received place: {place}, category: {category}, radius: {radius}")
        #fetch the latitude and longitude of the place using a geocoding API
        fetch_geo_weather_details = fetchGeoWeatherDetails(place)
        location = fetch_geo_weather_details.get_lat_long(place)
        if location:
            lat, lon = location.latitude, location.longitude
        else:
            return "Sorry, I couldn't find the location you mentioned. Please try with a different place."
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        node(around:{radius},{lat},{lon})["amenity"="{category}"];
        out;
        """

        response = requests.get(overpass_url, params={'data': query})
        data = response.json()

        places = []

        for el in data["elements"][:5]:
            places.append({
                "name": el["tags"].get("name", "Unknown"),
                "lat": el["lat"],
                "lon": el["lon"]
            })
        logger.info(f"Found nearby places: {places}, returning the top 5 results.")
        return str({"places": places})
    except Exception as e:
        logger.error(f"Error in find_nearby tool: {e} with traceback:{traceback.format_exc()}")
        return "Sorry, I couldn't fetch the nearby places at the moment. Please try again later."

#tool to fetch historical environmental data from Open-Meteo and store into database
@mcp.tool()
def fetch_environmental_data(
    place: str,
    start_date: str,
    end_date: str,
    shared_folder: str
) -> str:
    """
    Fetch historical environmental data from Open-Meteo
    and store into database. Pass the place, start date, end date and shared folder path as parameters.
    Date format: YYYY-MM-DD
    """
    try:
        logger.info(f"In the fetch_environmental_data tool, received place: {place}, start_date: {start_date}, end_date: {end_date}, shared_folder: {shared_folder}")
        fetch_geo_weather_details = fetchGeoWeatherDetails(place)
        location = fetch_geo_weather_details.get_lat_long(place)
        if location:
            latitude, longitude = location.latitude, location.longitude
        else:
            return "Sorry, I couldn't find the location you mentioned. Please try with a different place."

        url = (
            "https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={latitude}"
            f"&longitude={longitude}"
            f"&start_date={start_date}"
            f"&end_date={end_date}"
            "&hourly=temperature_2m,relativehumidity_2m,pm10,pm2_5"
        )

        response = requests.get(url)
        data = response.json()
        if "hourly" not in data:
            return f"Error fetching data: {data}"

        df = pd.DataFrame({
            "timestamp": data["hourly"]["time"],
            "temperature": data["hourly"]["temperature_2m"],
            "humidity": data["hourly"]["relativehumidity_2m"],
            "pm10": data["hourly"]["pm10"],
            "pm2_5": data["hourly"]["pm2_5"],
        })
        if df.empty:
            logger.info("No environmental data available for the given parameters.")
            return "No data available for the given parameters."
        df["latitude"] = latitude
        df["longitude"] = longitude
        #save the dataframe to a csv file in the shared folder
        # Join the static folder with the shared_folder parameter
        logger.info(f"Head of data:{df.head()}")
        shared_folder = Path(shared_folder)   # convert str → Path
        filename = f"{place}_{start_date}_{end_date}_{uuid.uuid4()}.csv"
        file_path = shared_folder / filename
        
        df.to_csv(file_path, index=False)
        columns_info = ", ".join(df.columns)
        logger.info(f"Saved the data at :{file_path}")
        return f"Fetched environmental data and saved as csv filename: {filename} in the shared folder. Columns in the data: {columns_info}"
    except Exception as e:
        logger.error(f"Error in fetch_environmental_data tool: {e} with traceback:{traceback.format_exc()}")
        return "Sorry, I couldn't fetch the environmental data at the moment. Please try again later."

if __name__ == "__main__":
    mcp.run(transport="streamable-http")

    