from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .coordinator import request_manager
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SYRValveSwitch(coordinator)])

class SYRValveSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_should_poll = False
        self._attr_name = f"{coordinator.name} Absperrung"
        self._attr_unique_id = f"{coordinator.ip}_valve"
        self._busy = False

    @property
    def is_on(self):
        return self.coordinator.data.get("VLV") == 20

    @property
    def icon(self):
        return "mdi:valve-open" if self.is_on else "mdi:valve-closed"

    @property
    def available(self):
        return self.coordinator.last_update_success and not self._busy

    async def async_turn_on(self, **kwargs):
        await self._send_valve_command(True)

    async def async_turn_off(self, **kwargs):
        await self._send_valve_command(False)

    async def _send_valve_command(self, close: bool):
        self._busy = True
        self.async_write_ha_state()

        url = f"http://{self.coordinator.ip}:5333/trio/set/ab/{str(not close).lower()}"
        _LOGGER.info("➡️ Befehl senden: %s", url)

        try:
            await request_manager.set(url)
            _LOGGER.info("✅ Ventilbefehl erfolgreich übermittelt")
        except Exception as e:
            _LOGGER.error("❌ Fehler beim Senden des Ventilbefehls: %s", e)

        self._busy = False
        self.async_write_ha_state()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.ip)},
            "name": self.coordinator.name,
            "manufacturer": "SYR",
            "model": "Leckageschutz Ventil",
            "configuration_url": f"http://{self.coordinator.ip}:5333/"
        }
