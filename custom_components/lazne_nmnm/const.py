"""Constants for the Mestske lazne NMnM integration."""

from datetime import timedelta

DOMAIN = "lazne_nmnm"
NAME = "Mestske lazne Nove Mesto na Morave"

OCCUPANCY_URL = "https://lazne.nmnm.cz/data/lazne/navstevnost-homepage.php"
SCHEDULE_URL = "https://lazne.nmnm.cz/provozni-doba/"

OCCUPANCY_INTERVAL = timedelta(minutes=15)
SCHEDULE_INTERVAL = timedelta(hours=24)
