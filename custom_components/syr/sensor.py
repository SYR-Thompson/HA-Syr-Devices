from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, VALVE_STATE_MAP

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SYRSensor(coordinator, "FLO", "Durchfluss", "L/h", "water", "measurement"),
        SYRSensor(coordinator, "VOL", "Gesamtvolumen", "L", "water", "total_increasing"),
        SYRSensor(coordinator, "ALA", "Alarmcode", None, None, None, is_enum=True),
        SYRSensor(coordinator, "VLV", "Ventilstatus", None, None, None, is_status=True),
        
    ])

class SYRSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, key, name, unit, device_class, state_class, is_status=False, is_enum=False):
        super().__init__(coordinator)
        self._key = key
        self._name = name
        self._unit = unit
        self._device_class = device_class
        self._state_class = state_class
        self._is_status = is_status
        self._is_enum = is_enum
        self._attr_should_poll = False

    @property
    def name(self):
        return f"{self.coordinator.name} {self._name}"

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def device_class(self):
        return self._device_class

    @property
    def state_class(self):
        return self._state_class

    @property
    def state(self):
        val = self.coordinator.data.get(self._key)
        if self._is_status:
            return VALVE_STATE_MAP.get(val, val)
        return val

    @property
    def unique_id(self):
        return f"{self.coordinator.ip}_{self._key}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.ip)},
            "name": self.coordinator.name,
            "manufacturer": "SYR",
        }
