import requests
import json

class AvoindataApiService:

    def fetch_data_from_api(per_page, page):
        """Hae hallituksen esitykset avoindata-rajapinnasta"""
        url = f"https://avoindata.eduskunta.fi/api/v1/vaski/asiakirjatyyppinimi?perPage={per_page}&page={page}&filter=Hallituksen+esitys&languageCode=fi"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print("Fetching data failed:", response.status_code)
            return None
        
    def fetch_asiantuntijalausunnot_from_api(per_page, page):
        """Hae asiantuntijalausunnot avoindata-rajapinnasta"""
        url = f"https://avoindata.eduskunta.fi/api/v1/vaski/asiakirjatyyppinimi?perPage={per_page}&page={page}&languageCode=fi&filter=Asiantuntijalausunto"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print("Fetching data failed: ", response.status_code)
            return None
