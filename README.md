# Městské lázně Nové Město na Moravě for Home Assistant

A HACS custom integration exposing current visitor counts, opening status, and sauna access from [Městské lázně Nové Město na Moravě](https://lazne.nmnm.cz/).

The integration is unofficial and is not affiliated with the City of Nové Město na Moravě.

## Features

- Seven live visitor-count sensors.
- Pool, fitness, and wellness open/closed binary sensors.
- Current men's, women's, shared, or closed sauna access.
- Opening-hours parsing from the published regular and seasonal schedules.
- Czech and English entity names.
- Visible Home Assistant Repair issues and logs when fetching or parsing fails.
- No third-party Python dependencies.

## Data sources and polling

| Data | Source | Network interval |
| --- | --- | --- |
| Visitor counts | `https://lazne.nmnm.cz/data/lazne/navstevnost-homepage.php` | 15 minutes |
| Opening hours and sauna access | `https://lazne.nmnm.cz/provozni-doba/` | 24 hours |

Opening-status and sauna entities are recalculated locally once per minute. This does not generate additional website requests.

The website returns HTML rather than an API response. The integration parses the visitor table and every opening-hours table with the columns `Bazén`, `Fitness`, and `Wellness`. A bounded seasonal schedule takes precedence over the newest applicable open-ended schedule. Both hyphens and en dashes are accepted in time ranges.

The site's visitor labels currently include the icon-font remnants `GWellness` and `LMasáže`; these are normalized to `Wellness` and `Masáže`.

## Entities

Exact entity IDs can receive a numeric suffix if the same ID already exists in Home Assistant.

| Entity | Meaning |
| --- | --- |
| `sensor.mestske_lazne_nove_mesto_na_morave_visitors_complex` | Visitors in the whole complex |
| `sensor.mestske_lazne_nove_mesto_na_morave_visitors_pool` | Visitors in the pool |
| `sensor.mestske_lazne_nove_mesto_na_morave_visitors_fitness` | Visitors in fitness |
| `sensor.mestske_lazne_nove_mesto_na_morave_visitors_wellness` | Visitors in wellness |
| `sensor.mestske_lazne_nove_mesto_na_morave_visitors_baths` | Visitors in baths |
| `sensor.mestske_lazne_nove_mesto_na_morave_visitors_massages` | Visitors in massages |
| `sensor.mestske_lazne_nove_mesto_na_morave_visitors_solarium` | Visitors in the solarium |
| `binary_sensor.mestske_lazne_nove_mesto_na_morave_pool_open` | Whether the pool is currently open |
| `binary_sensor.mestske_lazne_nove_mesto_na_morave_fitness_open` | Whether fitness is currently open |
| `binary_sensor.mestske_lazne_nove_mesto_na_morave_wellness_open` | Whether wellness is currently open |
| `sensor.mestske_lazne_nove_mesto_na_morave_sauna_access` | `pánská`, `dámská`, `společná`, or `zavřeno` |

Each opening-status binary sensor has an `hours_today` attribute containing the website's schedule text for that area and day.

## Installation with HACS

Until the repository is included in the default HACS catalog:

1. Open HACS in Home Assistant.
2. Open the three-dot menu and select **Custom repositories**.
3. Add `https://github.com/pdostal/lazne_nmnm` as an **Integration** repository.
4. Find and download **Městské lázně Nové Město na Moravě**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration**.
7. Search for **Městské lázně Nové Město na Moravě** and confirm the dialog.

Only one configuration entry is allowed because the integration has no configurable endpoint or credentials.

## Manual installation

Copy `custom_components/lazne_nmnm` into the Home Assistant `custom_components` directory, restart Home Assistant, and add the integration from **Settings → Devices & services**.

## Errors and recovery

Visitor counts and opening hours use independent coordinators. If one source fails, only its entities become unavailable.

For a network or parsing error, the integration:

1. Logs the source URL, error, and up to 200 characters of the unexpected response under **Settings → System → Logs**.
2. Creates a warning under **Settings → System → Repairs** with the source URL and error.
3. Marks entities backed by that source unavailable rather than displaying stale data as current.
4. Deletes the Repair issue automatically after the next successful update.

The opening-hours parser intentionally fails if expected weekdays, columns, time ranges, or applicable dates are missing. This makes website format changes visible instead of silently producing incorrect opening states.

## Current parsing assumptions

- Opening-hours tables have four columns: weekday, pool, fitness, and wellness.
- Each schedule has one row for every Czech weekday from Monday through Sunday.
- A schedule heading contains either `od DD. M. YYYY` or a bounded `DD.M.-DD.M.YYYY` range.
- Wellness time ranges may include `pánská`, `dámská`, or `společná` sauna text.
- A wellness range without a gender annotation is treated as shared, matching the site's summer schedule.
- Opening intervals include their start time and exclude their closing time.

## Development

The parsers use only the Python standard library and can be tested without installing Home Assistant:

```bash
python3 tests/test_occupancy_parsing.py
python3 tests/test_schedule_parsing.py
python3 -m compileall -q custom_components tests
```

Fixtures under `tests/fixtures` are trimmed snapshots of actual website responses. Tests cover complete occupancy extraction, required-row validation, regular and summer schedule parsing, seasonal precedence, sauna access transitions, opening-boundary behavior, and dates outside all schedules.

## Continuous integration

`.github/workflows/validate.yml` runs on every push and pull request:

- Dependency-free parser tests and Python byte-code compilation.
- [Home Assistant hassfest](https://github.com/home-assistant/actions) validation.
- [HACS action](https://github.com/hacs/action) validation as an integration repository.

## Releases and HACS updates

The integration version is stored in `custom_components/lazne_nmnm/manifest.json`. To release a version:

1. Change `version` in `manifest.json` using semantic versioning.
2. Merge or push the change to `master`.
3. Wait for the **Validate** workflow to pass.

`.github/workflows/release.yml` then checks for a matching `v<version>` GitHub Release. If none exists, it creates the tag and release with generated notes at the validated commit. Documentation-only changes with an unchanged version do not create another release. HACS detects the new GitHub Release and offers it as an update.

Do not reuse or move a published version tag. Increase the manifest version for every integration release.

## Project structure

```text
custom_components/lazne_nmnm/
├── __init__.py          # entry setup and local clock updates
├── binary_sensor.py     # opening-status entities
├── config_flow.py       # UI setup and single-instance guard
├── const.py             # URLs and polling intervals
├── coordinator.py       # fetching, Repairs, and update handling
├── entity.py            # shared device metadata
├── manifest.json        # Home Assistant and release metadata
├── parser.py            # dependency-free HTML and schedule parsing
├── sensor.py            # visitor-count and sauna entities
├── strings.json
└── translations/
    ├── cs.json
    └── en.json
tests/
├── fixtures/
├── test_occupancy_parsing.py
└── test_schedule_parsing.py
```

## License

[MIT](LICENSE)
