from django.conf import settings
from amadeus import Client, ResponseError


class AmadeusService:
    def __init__(self):
        self.amadeus = Client(
            client_id=settings.AMADEUS_API_KEY,
            client_secret=settings.AMADEUS_API_SECRET,
        )

    def search_city(self, keyword, country_code, max_results):
        try:
            params = {
                'keyword': keyword,
                'max': max_results,
            }

            if country_code:
                params['country_code'] = country_code
            response = self.amadeus.reference_data.locations.cities.get(**params)
            if response.data is None:
                return []
        except ResponseError as e:
            return {"error": e.response.body}
        except Exception as e:
            return {"error": str(e)}
