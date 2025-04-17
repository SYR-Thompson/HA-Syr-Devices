from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfVolume
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN
from .coordinator import SYRCoordinator, SlowSYRCoordinator

VLV_STATE_MAP = {
    10: "Absperrung geschlossen",
    11: "Absperrung schließt",
    20: "Absperrung offen",
    21: "Absperrung öffnet"
}

ALA_STATE_MAP = {
    "ff": "Kein Alarm",
    "a1": "Fehler Endschalter",
    "a2": "Motorstrom überschritten",
    "a3": "Volumenleckage",
    "a4": "Zeitleckage",
    "a5": "Durchflussleckage",
    "a6": "Mikroleckage",
    "a7": "Bodensensorleckage",
    "a8": "Störung Turbine"
    
}


SENSOR_DEFINITIONS = {
    "VLV": {"name": "Ventilstatus", "unit": None, "device_class": None},
    "FLO": {"name": "Durchfluss", "unit": "L/h", "device_class": "water"},
    "VOL": {"name": "Volumen", "unit": UnitOfVolume.LITERS, "device_class": "water", "state_class": "total_increasing"},
    "ALA": {"name": "Alarm", "unit": None, "device_class": None},

    # Diagnosewerte (readonly)
    "PV1": {"name": "Volumen-Grenzwert 1", "unit": UnitOfVolume.LITERS, "device_class": None, "diagnostic": True},
    "PV2": {"name": "Volumen-Grenzwert 2", "unit": UnitOfVolume.LITERS, "device_class": None, "diagnostic": True},
    "PV3": {"name": "Volumen-Grenzwert 3", "unit": UnitOfVolume.LITERS, "device_class": None, "diagnostic": True},
    "PT1": {"name": "Zeitleckage 1", "unit": "s", "device_class": None, "diagnostic": True},
    "PT2": {"name": "Zeitleckage 2", "unit": "s", "device_class": None, "diagnostic": True},
    "PT3": {"name": "Zeitleckage 3", "unit": "s", "device_class": None, "diagnostic": True},
}

async def async_setup_entry(hass, entry, async_add_entities):
    fast = hass.data[DOMAIN][entry.entry_id]
    slow = SlowSYRCoordinator(hass, fast.ip, fast.name)
    await slow.async_config_entry_first_refresh()

    entities = []

    for key, meta in SENSOR_DEFINITIONS.items():
        if meta.get("diagnostic"):
            if key in slow.data:
                entities.append(SYRSensor(slow, key, meta))
        else:
            if key in fast.data:
                entities.append(SYRSensor(fast, key, meta))

    async_add_entities(entities)

class SYRSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, key, meta):
        super().__init__(coordinator)
        self._key = key
        self._meta = meta
        self._attr_name = f"{coordinator.name} {meta['name']}"
        self._attr_native_unit_of_measurement = meta["unit"]
        self._attr_device_class = meta["device_class"]
        self._attr_should_poll = False

        if meta.get("diagnostic"):
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self):
        return f"{self.coordinator.ip}_{self._key.lower()}"

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._key)

        if self._key == "VLV":
            return VLV_STATE_MAP.get(value, value)

        if self._key == "ALA":
            return ALA_STATE_MAP.get(str(value).lower(), value)

        return value

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.ip)},
            "name": self.coordinator.name,
            "manufacturer": "SYR",
        }
