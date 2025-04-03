from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator, UpdateFailed
from datetime import timedelta
import aiohttp
import logging
from .const import DOMAIN, CONF_IP, CONF_NAME

_LOGGER = logging.getLogger(__name__)

CONFIGURABLE_KEYS = {
    "PV1": {"name": "Volumengrenzwert 1", "unit": "L", "min": 0, "max": 10000, "step": 1, "device_class": "volume"},
    "PV2": {"name": "Volumengrenzwert 2", "unit": "L", "min": 0, "max": 10000, "step": 1, "device_class": "volume"},
    "PV3": {"name": "Volumengrenzwert 3", "unit": "L", "min": 0, "max": 10000, "step": 1, "device_class": "volume"},
    "PT1": {"name": "Parameter Zeit 1", "unit": "s", "min": 0, "max": 3600, "step": 1, "device_class": None},
    "PT2": {"name": "Parameter Zeit 2", "unit": "s", "min": 0, "max": 3600, "step": 1, "device_class": None},
    "PT3": {"name": "Parameter Zeit 3", "unit": "s", "min": 0, "max": 3600, "step": 1, "device_class": None},
}

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
        keys = list(CONFIGURABLE_KEYS.keys())
        async with aiohttp.ClientSession() as session:
            for key in keys:
                url = f"http://{self.ip}:5333/trio/get/{key.lower()}"
                try:
                    async with session.get(url, timeout=5) as resp:
                        raw = await resp.json()
                        response_key = f"get{key.upper()}"
                        if response_key in raw:
                            data[key] = raw[response_key]
                except Exception as e:
                    _LOGGER.warning("Failed to update %s: %s", key, e)
        return data

async def async_setup_entry(hass, entry, async_add_entities):
    ip = entry.data[CONF_IP]
    name = entry.data.get(CONF_NAME, ip)
    coordinator = SlowSYRCoordinator(hass, ip, name)
    await coordinator.async_config_entry_first_refresh()

    entities = []
    for key, meta in CONFIGURABLE_KEYS.items():
        if key in coordinator.data:
            entities.append(SYRConfigNumber(coordinator, key, meta))
    async_add_entities(entities)

class SYRConfigNumber(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, key, meta):
        super().__init__(coordinator)
        self._key = key
        self._meta = meta
        self._attr_name = f"{coordinator.name} {meta['name']}"
        self._attr_native_unit_of_measurement = meta["unit"]
        self._attr_min_value = meta["min"]
        self._attr_max_value = meta["max"]
        self._attr_step = meta["step"]
        self._attr_device_class = meta["device_class"]
        self._attr_should_poll = False

    @property
    def unique_id(self):
        return f"{self.coordinator.ip}_{self._key.lower()}"

    @property
    def native_value(self):
        return float(self.coordinator.data.get(self._key, 0))

    async def async_set_native_value(self, value: float):
        key_for_set = "pvt" if self._key == "PV1" else self._key.lower()
        url = f"http://{self.coordinator.ip}:5333/trio/set/{key_for_set}/{value}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        await self.coordinator.async_request_refresh()
        except Exception:
            self._attr_available = False

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.ip)},
            "name": self.coordinator.name,
            "manufacturer": "SYR",
        }
