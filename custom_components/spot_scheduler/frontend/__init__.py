"""Frontend resource registration for SpotScheduler Lovelace card."""

import hashlib
import logging
import pathlib

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant, callback

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_STATIC_URL = f"/api/{DOMAIN}/static"
_STATIC_DIR = pathlib.Path(__file__).parent
_CARD_FILE = _STATIC_DIR / "spot-scheduler-card.js"


async def _card_url(hass: HomeAssistant) -> str:
    """Build card URL with content-hash cache buster."""
    try:
        content = await hass.async_add_executor_job(_CARD_FILE.read_bytes)
        file_hash = hashlib.md5(content).hexdigest()[:8]
    except OSError:
        file_hash = "0"
    return f"/api/{DOMAIN}/static/spot-scheduler-card.js?v={file_hash}"


async def async_register(hass: HomeAssistant) -> None:
    """Register the static HTTP path and the Lovelace module resource."""
    # ── Static HTTP path (once per HA process) ─────────────────────────────
    if not hass.data.get(f"{DOMAIN}_static_registered"):
        try:
            from homeassistant.components.http import StaticPathConfig
            await hass.http.async_register_static_paths(
                [StaticPathConfig(_STATIC_URL, str(_STATIC_DIR), True)]
            )
        except (ImportError, AttributeError):
            try:
                hass.http.register_static_path(_STATIC_URL, str(_STATIC_DIR), cache_headers=True)
            except Exception as exc:
                _LOGGER.warning("Could not register static path: %s", exc)

        hass.data[f"{DOMAIN}_static_registered"] = True

    # ── Lovelace resource URL ───────────────────────────────────────────────
    if hass.is_running:
        await _register_lovelace_resource(hass)
    else:
        @callback
        def _on_started(_event) -> None:
            hass.async_create_task(_register_lovelace_resource(hass))

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_started)


async def _register_lovelace_resource(hass: HomeAssistant) -> None:
    """Add or update the Lovelace module resource entry."""
    try:
        from homeassistant.components.lovelace.resources import (
            ResourceStorageCollection,
            RESOURCE_STORAGE_KEY,
        )
        lovelace_data = hass.data.get("lovelace")
        resources: ResourceStorageCollection | None = (
            hass.data.get(RESOURCE_STORAGE_KEY)
            or (getattr(lovelace_data, "resources", None) if lovelace_data else None)
        )
        if resources is None:
            card_url = await _card_url(hass)
            _LOGGER.warning(
                "Could not locate Lovelace resources collection – add the card manually: %s",
                card_url,
            )
            return
        card_url = await _card_url(hass)
        existing = [r for r in resources.async_items() if DOMAIN in r.get("url", "")]
        if not existing:
            await resources.async_create_item({"res_type": "module", "url": card_url})
            _LOGGER.info("Registered Lovelace resource: %s", card_url)
        elif existing[0].get("url") != card_url:
            await resources.async_update_item(
                existing[0]["id"], {"res_type": "module", "url": card_url}
            )
            _LOGGER.info("Updated Lovelace resource URL to: %s", card_url)
        else:
            _LOGGER.debug("Lovelace resource already up-to-date: %s", card_url)
    except Exception as exc:
        _LOGGER.warning("Could not register Lovelace resource: %s", exc)
