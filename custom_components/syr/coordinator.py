from datetime import timedelta
import aiohttp
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import SCAN_INTERVAL, CONF_IP

_LOGGER = logging.getLogger(__name__)

SENSOR_KEYS = [
    "VLV", "FLO", "VOL", "ALA",
    "PV1", "PV2", "PV3",
    "PT1", "PT2", "PT3"
]

class SYRCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config_entry):
        self.hass = hass
        self.ip = config_entry.data[CONF_IP]
        self.name = config_entry.data.get("name", self.ip)

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"SYR - {self.name}",
            update_interval=timedelta(seconds=SCAN_INTERVAL)
        )

    async def _async_update_data(self):
        data = {}
        try:
            async with aiohttp.ClientSession() as session:
                for key in SENSOR_KEYS:
                    try:
                        url = f"http://{self.ip}:5333/trio/get/{key.lower()}"
                        async with session.get(url, timeout=5) as resp:
                            raw = await resp.json()
                            response_key = f"get{key.upper()}"
                            if response_key in raw:
                                data[key] = raw[response_key]
                            else:
                                _LOGGER.warning(f"Missing key '{response_key}' in response from {url}")
                    except Exception as e:
                        _LOGGER.warning(f"Error fetching {key} from {self.ip}: {e}")
            return data
        except Exception as e:
            raise UpdateFailed(f"Error updating data from SYR device: {e}")
