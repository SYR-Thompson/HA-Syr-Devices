from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, CONF_IP, CONF_NAME

class SYRConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            # Name definieren oder fallback erzeugen
            name = user_input.get(CONF_NAME, f"SYR {user_input[CONF_IP]}")
            return self.async_create_entry(
                title=name,  # ← dieser Name wird im UI angezeigt
                data={
                    CONF_IP: user_input[CONF_IP],
                    CONF_NAME: name
                }
            )

        # Formular anzeigen
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_IP): str,
                vol.Optional(CONF_NAME, default=""): str
            })
        )
