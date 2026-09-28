"""Data coordinators for Mestske lazne NMnM."""

import logging
from collections.abc import Callable
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    NAME,
    OCCUPANCY_INTERVAL,
    OCCUPANCY_URL,
    SCHEDULE_INTERVAL,
    SCHEDULE_URL,
)
from .parser import parse_occupancy, parse_schedules, select_schedule

_LOGGER = logging.getLogger(__name__)


class LazneCoordinator(DataUpdateCoordinator[Any]):
    """Fetch and parse one lazne.nmnm.cz resource."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: ClientSession,
        config_entry: ConfigEntry,
        *,
        key: str,
        url: str,
        interval: Any,
        parser: Callable[[str], Any],
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{NAME} {key}",
            update_interval=interval,
        )
        self._session = session
        self._key = key
        self._url = url
        self._parser = parser

    async def _async_update_data(self) -> Any:
        body = ""
        try:
            async with self._session.get(
                self._url, timeout=ClientTimeout(total=15)
            ) as response:
                response.raise_for_status()
                body = await response.text()
            data = self._parser(body)
            if self._key == "schedule":
                select_schedule(data, dt_util.now().date())
        except (ClientError, TimeoutError, ValueError) as error:
            snippet = " ".join(body.split())[:200]
            _LOGGER.error(
                "Failed to update %s from %s: %s%s",
                self._key,
                self._url,
                error,
                f"; response: {snippet}" if snippet else "",
            )
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                f"{self._key}_update_failed",
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=f"{self._key}_update_failed",
                translation_placeholders={"error": str(error), "url": self._url},
            )
            raise UpdateFailed(str(error)) from error

        ir.async_delete_issue(self.hass, DOMAIN, f"{self._key}_update_failed")
        return data


def occupancy_coordinator(
    hass: HomeAssistant, session: ClientSession, config_entry: ConfigEntry
) -> LazneCoordinator:
    return LazneCoordinator(
        hass,
        session,
        config_entry,
        key="occupancy",
        url=OCCUPANCY_URL,
        interval=OCCUPANCY_INTERVAL,
        parser=parse_occupancy,
    )


def schedule_coordinator(
    hass: HomeAssistant, session: ClientSession, config_entry: ConfigEntry
) -> LazneCoordinator:
    return LazneCoordinator(
        hass,
        session,
        config_entry,
        key="schedule",
        url=SCHEDULE_URL,
        interval=SCHEDULE_INTERVAL,
        parser=parse_schedules,
    )
