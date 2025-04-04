from datetime import timedelta
import aiohttp
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import SCAN_INTERVAL, CONF_IP, CONF_NAME

_LOGGER = logging.getLogger(__name__)

SENSOR_KEYS = [
    "VLV",  # Ventilstatus
    "FLO",  # Durchfluss
    "VOL",  # Gesamtvolumen
    "ALA",  # Alarmstatus
]

class SYRCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config_entry):
        self.hass = hass
        self.ip = config_entry.data[CONF_IP]
        self.name = config_entry.data.get(CONF_NAME, self.ip)

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"SYR - {self.name}",
            update_interval=timedelta(seconds=SCAN_INTERVAL)
        )

    async def _async_update_data(self):
        data = {}
        _LOGGER.debug("🌀 SYR: Start update for fast sensors (%s)", self.ip)

        try:
            async with aiohttp.ClientSession() as session:
                for key in SENSOR_KEYS:
                    url = f"http://{self.ip}:5333/trio/get/{key.lower()}"
                    try:
                        async with session.get(url, timeout=5) as resp:
                            raw = await resp.json()
                            response_key = f"get{key.upper()}"
                            if response_key in raw:
                                data[key] = raw[response_key]
                                _LOGGER.debug("✅ %s = %s", key, raw[response_key])
                            else:
                                _LOGGER.warning("⚠️ %s missing in response", response_key)
                    except Exception as e:
                        _LOGGER.warning("❌ Request failed for %s: %s", key, e)

        except Exception as e:
            _LOGGER.error("🔥 SYRCoordinator failed: %s", e)

        if not data:
            _LOGGER.warning("⚠️ No new data, using previous")
            return self.data or {}

        return data


class SlowSYRCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, ip, name):
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"SYR-Slow {ip}",
            update_interval=timedelta(seconds=60)
        )
        self.ip = ip
        self.name = name

    async def _async_update_data(self):
        data = {}
        CONFIGURABLE_KEYS = [
            "PV1", "PV2", "PV3",
            "PT1", "PT2", "PT3"
        ]
        try:
            async with aiohttp.ClientSession() as session:
                for key in CONFIGURABLE_KEYS:
                    url = f"http://{self.ip}:5333/trio/get/{key.lower()}"
                    try:
                        async with session.get(url, timeout=5) as resp:
                            raw = await resp.json()
                            response_key = f"get{key.upper()}"
                            if response_key in raw:
                                data[key] = raw[response_key]
                                _LOGGER.debug("🐢 Slow [%s] = %s", key, raw[response_key])
                            else:
                                _LOGGER.warning("🐢 Slow: Key missing: %s", response_key)
                    except Exception as e:
                        _LOGGER.warning("🐢 Slow: Request error for %s: %s", key, e)
        except Exception as e:
            _LOGGER.error("🔥 SlowSYRCoordinator failed: %s", e)

        if not data:
            _LOGGER.warning("🐢 No new slow data – using previous values")
            return self.data or {}

        return data
