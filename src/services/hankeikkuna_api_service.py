import requests
import json


class HankeikkunaApiService:

    def fetch_data_from_api(per_page: int, page: int):
        request_url = "https://api.hankeikkuna.fi/api/v2/kohteet/haku"
        for i in range(page):
            headers = {
                "accept": "application/json;charset=UTF-8",
                "Content-Type": "application/json",
            }
            if i == 0:
                query = {
                    "muokattuPaivaAlku": "2024-01-01T00:00:00",
                    "muokattuPaivaLoppu": "2025-01-01T23:59:59",
                    "size": per_page,
                    "sort": [
                        {
                            "field": "kohde.muokattu",
                            "order": "ASC",
                        }
                    ],
                    "tyyppi": ["LAINSAADANTO"],
                }
            else:
                query = {
                    "muokattuPaivaAlku": "2024-01-01T00:00:00",
                    "muokattuPaivaLoppu": "2025-01-01T23:59:59",
                    "searchAfter": data["nextSearchAfter"],
                    "size": per_page,
                    "sort": [
                        {
                            "field": "kohde.muokattu",
                            "order": "ASC",
                        }
                    ],
                    "tyyppi": ["LAINSAADANTO"],
                }
            response = requests.post(
                request_url, headers=headers, data=json.dumps(query)
            )
            if response.status_code == 200:
                data = response.json()
            else:
                print("Fetching data failed:", response.status_code)
        return data
