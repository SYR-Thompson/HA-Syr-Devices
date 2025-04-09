from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
import aiohttp
import logging
import asyncio

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
        self._last_vlv = None
        self._busy = False

    @property
    def is_on(self):
        """Return True if the valve is closed (Absperrung aktiv)."""
        return self.coordinator.data.get("VLV") == 20

    @property
    def icon(self):
        if self.is_on:
            return "mdi:valve-closed"
        else:
            return "mdi:valve-open"

    @property
    def available(self):
        return self.coordinator.last_update_success and not self._busy

    async def async_turn_on(self, **kwargs):
        """Schalte Ventil zu (Absperrung aktivieren)."""
        await self._send_valve_command(True)

    async def async_turn_off(self, **kwargs):
        """Schalte Ventil auf (Absperrung deaktivieren)."""
        await self._send_valve_command(False)

    async def _send_valve_command(self, close: bool):
        """Sende Steuerbefehl und warte auf Zustand über Koordinator."""
        self._busy = True
        self.async_write_ha_state()  # UI-Update: Sperre

        expected = 20 if close else 10
        url = f"http://{self.coordinator.ip}:5333/trio/set/ab/{str(not close).lower()}"
        _LOGGER.info("➡️ Schalte Ventil (%s): %s", "zu" if close else "auf", url)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        _LOGGER.debug("Befehl gesendet, warte auf Statusaktualisierung...")
                        self._last_vlv = self.coordinator.data.get("VLV")
                        await asyncio.sleep(3)
                        await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error("❌ Fehler beim Schaltvorgang: %s", e)

        self._busy = False
        self.async_write_ha_state()  # UI-Update: Entsperre

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.ip)},
            "name": self.coordinator.name,
            "manufacturer": "SYR",
            "model": "Leckageschutz Ventil",
            "configuration_url": f"http://{self.coordinator.ip}:5333/"
        }
