import requests
from geopy.distance import geodesic
import pandas as pd
import time

class LithuanianCityDistance:
    def __init__(self, user_agent="CityDistanceApp", rate_limit_delay=1):
        self.geocode_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {'User-Agent': user_agent}
        self.coordinate_cache = {}
        self.rate_limit_delay = rate_limit_delay
    
    def get_coordinates(self, city_name):
        if city_name in self.coordinate_cache:
            return self.coordinate_cache[city_name]
        
        params = {
            'q': f'{city_name}, Lithuania',
            'format': 'json',
            'limit': 1,
            'countrycodes': 'lt'
        }
        
        try:
            response = requests.get(self.geocode_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                self.coordinate_cache[city_name] = (lat, lon)
                return (lat, lon)
            else:
                print(f"No coordinates found for {city_name}")
                return None
        except requests.exceptions.Timeout:
            print(f"Timeout error for {city_name}")
            return None
        except requests.exceptions.TooManyRedirects:
            print(f"Redirect error for {city_name}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"API error for {city_name}: {e}")
            return None
        finally:
            time.sleep(self.rate_limit_delay)
    
    def validate_city(self, city_name):
        coords = self.get_coordinates(city_name)
        return coords is not None
    
    def calculate_distance_km(self, city1, city2):
        coord1 = self.get_coordinates(city1)
        coord2 = self.get_coordinates(city2)
        
        if coord1 and coord2:
            distance = geodesic(coord1, coord2).kilometers
            return round(distance, 2)
        else:
            return None
    
    def create_distance_matrix(self, city_list):
        coords = {city: self.get_coordinates(city) for city in city_list}
        
        matrix_data = []
        for city1 in city_list:
            row = []
            for city2 in city_list:
                if city1 == city2:
                    row.append(0.0)
                elif coords[city1] and coords[city2]:
                    distance = geodesic(coords[city1], coords[city2]).kilometers
                    row.append(round(distance, 2))
                else:
                    row.append(None)
            matrix_data.append(row)
        
        return pd.DataFrame(matrix_data, index=city_list, columns=city_list)
    
    def export_matrix(self, df, filename, format='csv'):
        if format == 'csv':
            df.to_csv(filename)
        elif format == 'excel':
            df.to_excel(filename)
        else:
            raise ValueError("Unsupported format. Use 'csv' or 'excel'")

if __name__ == "__main__":
    distance_finder = LithuanianCityDistance(user_agent="LT_Distance_Calculator", rate_limit_delay=1)
    
    cities_to_check = ["Vilnius", "Kaunas", "Klaipėda", "Šiauliai", "Panevėžys"]
    
    for city in cities_to_check:
        coords = distance_finder.get_coordinates(city)
        if coords:
            print(f"{city}: {coords}")
    
    dist_matrix = distance_finder.create_distance_matrix(cities_to_check)
    print("Distance Matrix (km):")
    print(dist_matrix)
    
    distance_finder.export_matrix(dist_matrix, "lithuanian_city_distances.csv")
