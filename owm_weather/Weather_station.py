import logging
import pyowm
from requests import Timeout


logger = logging.getLogger(__name__)

class WeatherStation():
    def __init__(self, owm_api_key=None):
        self._owm_api_key = owm_api_key
        self._owm = None
        self.observers = [] 
    
    @property
    def owm(self):
        try:
            if not self._owm:
                self._owm = pyowm.OWM(self._owm_api_key)
        except Timeout as err:
            logger.error(
                "WeatherStation owm fail with TimeOut error {}".format(err))
        return self._owm
    
    
    def _get_data_by_coord(self, lon, lat):
        mgr = self.owm.weather_manager()
        observations = mgr.weather_around_coords(lat=lat, lon=lon)
        return observations[0].weather.to_dict()



