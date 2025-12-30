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
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_coordinates(self, city_name):
        city_name = city_name.strip().title()
        
        if city_name in self.coordinate_cache:
            self.cache_hits += 1
            cached_value = self.coordinate_cache[city_name]
            return cached_value if cached_value != "INVALID" else None
        
        self.cache_misses += 1
        
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
                self.coordinate_cache[city_name] = "INVALID"
                return None
                
        except requests.exceptions.Timeout:
            self.coordinate_cache[city_name] = "INVALID"
            return None
        except requests.exceptions.TooManyRedirects:
            self.coordinate_cache[city_name] = "INVALID"
            return None
        except requests.exceptions.RequestException:
            self.coordinate_cache[city_name] = "INVALID"
            return None
        finally:
            time.sleep(self.rate_limit_delay)
    
    def validate_city(self, city_name):
        city_name = city_name.strip().title()
        if city_name in self.coordinate_cache:
            return self.coordinate_cache[city_name] != "INVALID"
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
    
    def calculate_distance(self, city1, city2, unit='km'):
        coord1 = self.get_coordinates(city1)
        coord2 = self.get_coordinates(city2)
        
        if coord1 and coord2:
            distance_km = geodesic(coord1, coord2).kilometers
            if unit == 'miles':
                return round(distance_km * 0.621371, 2)
            return round(distance_km, 2)
        return None
    
    def create_distance_matrix(self, city_list):
        cleaned_cities = [city.strip().title() for city in city_list]
        coords = {city: self.get_coordinates(city) for city in cleaned_cities}
        
        matrix_data = []
        for city1 in cleaned_cities:
            row = []
            for city2 in cleaned_cities:
                if city1 == city2:
                    row.append(0.0)
                elif coords[city1] and coords[city2]:
                    distance = geodesic(coords[city1], coords[city2]).kilometers
                    row.append(round(distance, 2))
                else:
                    row.append(None)
            matrix_data.append(row)
        
        return pd.DataFrame(matrix_data, index=cleaned_cities, columns=cleaned_cities)
    
    def export_matrix(self, df, filename, format='csv'):
        if format == 'csv':
            df.to_csv(filename)
        elif format == 'excel':
            df.to_excel(filename)
        else:
            raise ValueError("Unsupported format. Use 'csv' or 'excel'")
    
    def get_coordinates_batch(self, city_list):
        results = {}
        for city in city_list:
            clean_city = city.strip().title()
            if clean_city not in self.coordinate_cache:
                results[clean_city] = self.get_coordinates(clean_city)
            else:
                results[clean_city] = self.coordinate_cache[clean_city]
            time.sleep(self.rate_limit_delay)
        return results
    
    def get_cache_stats(self):
        valid_entries = sum(1 for v in self.coordinate_cache.values() if v != "INVALID")
        invalid_entries = sum(1 for v in self.coordinate_cache.values() if v == "INVALID")
        return {
            'total': len(self.coordinate_cache),
            'valid': valid_entries,
            'invalid': invalid_entries,
            'hits': self.cache_hits,
            'misses': self.cache_misses
        }
    
    def clear_cache(self):
        self.coordinate_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0

if __name__ == "__main__":
    try:
        distance_finder = LithuanianCityDistance(user_agent="LT_Distance_Calculator", rate_limit_delay=1)
        
        cities_to_check = ["Vilnius", "Kaunas", "Klaipėda", "Šiauliai", "Panevėžys", "UnknownCity"]
        
        valid_cities = []
        for city in cities_to_check:
            if distance_finder.validate_city(city):
                valid_cities.append(city)
                coords = distance_finder.get_coordinates(city)
                print(f"{city}: {coords}")
            else:
                print(f"Warning: {city} not found")
        
        if len(valid_cities) >= 2:
            dist_matrix = distance_finder.create_distance_matrix(valid_cities)
            print("Distance Matrix (km):")
            print(dist_matrix)
            
            distance_finder.export_matrix(dist_matrix, "lithuanian_city_distances.csv")
            print(f"Matrix saved to lithuanian_city_distances.csv")
            
            print("Cache Statistics:")
            print(distance_finder.get_cache_stats())
            
            vilnius_kaunas = distance_finder.calculate_distance("Vilnius", "Kaunas", unit='miles')
            print(f"Vilnius to Kaunas: {vilnius_kaunas} miles")
        else:
            print("Need at least 2 valid cities to create distance matrix")
            
    except Exception as e:
        print(f"Error: {e}")
