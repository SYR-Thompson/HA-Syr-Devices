from datetime import timedelta
import aiohttp
import logging
import asyncio
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import SCAN_INTERVAL, CONF_IP, CONF_NAME

_LOGGER = logging.getLogger(__name__)

SENSOR_KEYS = [
    "VLV",  # Ventilstatus
    "FLO",  # Durchfluss
    "VOL",  # Gesamtvolumen
    "ALA",  # Alarmstatus
]

# 🔒 Globaler Zugriffsschutz für alle GETs/SETs
global_request_lock = asyncio.Lock()

# 🔄 Zentraler Request-Manager mit Lock + 5s Pause
class SYRRequestManager:
    def __init__(self):
        self._lock = asyncio.Lock()

    async def get(self, url: str):
        async with self._lock:
            _LOGGER.debug("🔒 [GET] %s", url)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    result = await resp.json()
            await asyncio.sleep(1)
            return result

    async def set(self, url: str):
        async with self._lock:
            _LOGGER.debug("🔒 [SET] %s", url)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    result = await resp.text()
            await asyncio.sleep(1)
            return result

# 🧱 Instanz des Managers
request_manager = SYRRequestManager()


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
        async with global_request_lock:
            data = {}
            _LOGGER.debug("🌀 SYR: Start update for fast sensors (%s)", self.ip)

            try:
                for key in SENSOR_KEYS:
                    url = f"http://{self.ip}:5333/trio/get/{key.lower()}"
                    try:
                        raw = await request_manager.get(url)
                        response_key = f"get{key.upper()}"
                        if response_key in raw:
                            data[key] = raw[response_key]
                            _LOGGER.debug("✅ %s = %s", key, raw[response_key])
                        else:
                            _LOGGER.warning("⚠️ %s fehlt in Antwort", response_key)
                    except Exception as e:
                        _LOGGER.warning("❌ Fehler beim Abrufen von %s: %s", key, e)

            except Exception as e:
                _LOGGER.error("🔥 SYRCoordinator Fehler: %s", e)

            if not data:
                _LOGGER.warning("⚠️ Keine neuen Daten – verwende vorherige")
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
        async with global_request_lock:
            data = {}
            CONFIGURABLE_KEYS = ["PV1", "PV2", "PV3", "PT1", "PT2", "PT3"]
            _LOGGER.debug("🐢 Slow-Polling startet für %s", self.ip)

            try:
                for key in CONFIGURABLE_KEYS:
                    url = f"http://{self.ip}:5333/trio/get/{key.lower()}"
                    try:
                        raw = await request_manager.get(url)
                        response_key = f"get{key.upper()}"
                        if response_key in raw:
                            data[key] = raw[response_key]
                            _LOGGER.debug("🐢 %s = %s", key, raw[response_key])
                        else:
                            _LOGGER.warning("🐢 %s fehlt in Antwort", response_key)
                    except Exception as e:
                        _LOGGER.warning("🐢 Fehler bei %s: %s", key, e)

            except Exception as e:
                _LOGGER.error("🔥 SlowCoordinator Fehler: %s", e)

            if not data:
                _LOGGER.warning("🐢 Keine neuen Daten – verwende alte")
                return self.data or {}

            return data
