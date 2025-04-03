from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
import aiohttp

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SYRValveSwitch(coordinator)])

class SYRValveSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_should_poll = False

    @property
    def name(self):
        return f"{self.coordinator.name} Ventil"

    @property
    def is_on(self):
        return self.coordinator.data.get("VLV") == 10

    async def async_turn_on(self):
        await self._send_command(True)

    async def async_turn_off(self):
        await self._send_command(False)

    async def _send_command(self, open_valve: bool):
        url = f"http://{self.coordinator.ip}:5333/trio/set/ab/{str(open_valve).lower()}"
        async with aiohttp.ClientSession() as session:
            await session.get(url)
        await self.coordinator.async_request_refresh()

    @property
    def unique_id(self):
        return f"{self.coordinator.ip}_valve_switch"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.ip)},
            "name": self.coordinator.name,
            "manufacturer": "SYR",
        }
