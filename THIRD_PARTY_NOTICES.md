# Third-party notices and design provenance

LICENSE applies only to project material to the extent its rights are held by
the owner. It does not replace third-party terms, license trademarks/patents,
or establish ownership of technical facts.

## KiCad

Saved designs embed standard-library symbol/footprint data, and renders use
installed component models. KiCad libraries use CC BY-SA 4.0 with an exception
for electronic designs and generated files. The exception does not apply to
republishing libraries as a collection. Full standard libraries/models are not
vendored here. See the [official license and exception](https://www.kicad.org/libraries/license/).
Custom footprints and sources are described in [hardware/lib/README.md](hardware/lib/README.md).

## Reference circuitry and datasheets

- **Espressif:** module and development-board programming/reset conventions.
  [Module datasheet](https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.html),
  [DevKitC documentation](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html).
- **Texas Instruments:** CC1101 interfaces, oscillator and layout guidance.
  [CC1101 documentation](https://www.ti.com/product/CC1101).
- **M5Stack:** Cap CC1101 schematic, recorded basis Rev 0.3, informed the switched
  RF topology and starting filter/matching values.
  [Original reference](https://docs.m5stack.com/en/cap/Cap_CC1101).
  No claim is made that its separately hosted hardware PDF inherits a software
  repository license. Source PDF/images are not republished here. Confirm any
  applicable hardware reuse rights before commercial release.
- **Infineon (historical A1/A2), TTM/Anaren, Abracon:** drawings informed local RF/crystal footprints.
  [BGS13SN8](https://www.infineon.com/assets/row/public/documents/24/49/infineon-bgs13sn8-datasheet-en.pdf),
  [balun](https://cdn.ttm.com/repository/products/wireless-xinger/balun-transformers/B0310J50100AHF/B0310J50100AHF.pdf),
  [ABM8](https://abracon.com/Resonators/abm8.pdf).
- **pSemi and Diodes:** A3 switch/regulator pins and land patterns, from
  [PE42442](https://psemi.com/pdf/datasheets/pe42442ds.pdf) and
  [AP63203](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf).
- **Silicon Labs and TI:** A3 USB power sequencing, load switch and UART buffer,
  linked with exact component sources in the engineering notes.
- Other sources are linked in [A3 engineering notes](docs/06-A3-prototype-engineering.md)
  and design reports. Datasheets remain their publishers' material.

Circuit functions and component facts are distinguished from copyrighted
drawings/documentation. Public availability is not assumed to grant a blanket
right to relicense material. This inventory is not legal clearance or a
freedom-to-operate analysis.

## README image credits

| Image | Source and scope |
|---|---|
| `output/routing-A3-3d.png`, `output/routing-A3-top.svg`, `output/svg-A3/` | Current project KiCad renders/exports, 2026-09-26; unapproved prototype candidate |
| `output/placement-A2-3d.png`, `output/placement-A2-top.png` | Project KiCad renders, 2026-09-22; library/model terms above |
| `output/routing-A2-top.svg`, schematic SVG | Exports from project design files; experimental/draft status retained |
| ESP32-WROOM-32E reference | Externally hosted [Espressif image](https://www.espressif.com/sites/default/files/modules/ESP32-WROOM-32E%20S_0.png); owner's copyright, excluded from project license |
| CC1101 representative package | Externally hosted [TI RGP0020H image](https://www.ti.com/content/dam/ticom/images/products/package/r/rgp0020h.png); owner's copyright, excluded from project license |

Manufacturer images identify reference parts and link to their source pages.
They are not redistributed as locally licensed assets. External images may
change or fail to load. Names and marks belong to their owners; no endorsement
or sponsorship is implied.

## Software and tools

Firmware depends on Arduino/SPI and the ESP32 framework through PlatformIO.
Their licenses are not replaced by LICENSE. Build caches, dependencies and
binaries are excluded; review notices before distributing firmware binaries.

KiCad, kicad-sch-api, PlatformIO and Freerouting were development tools, not
reviewers/endorsers. Their executables and source distributions are not included
or relicensed here.
