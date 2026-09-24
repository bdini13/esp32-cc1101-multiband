# Regeneration and verification

Run from the project root. These commands regenerate design files, so preserve
any manual KiCad edits first. The Python generators are the editable source for
this checkpoint; `netlist.yaml` is only a human-readable architecture summary.

The A2 checkpoint used KiCad 10.0.6, its bundled `pcbnew` Python, and
`kicad-sch-api==0.5.6`. Install the schematic dependency from
`requirements-eda.txt` into a separate environment. Set the executables and
library paths below for your installation; the macOS system-wide paths are
examples. On Linux, use a Python interpreter with the KiCad `pcbnew` module.
`generate_pcb.py` honors `KICAD_FP_ROOT` and otherwise detects common paths.

```sh
set -e
KICAD_CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
KICAD_PYTHON='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3'
SCHEMATIC_PYTHON='.venv/bin/python'
export KICAD_SYMBOL_DIR='/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols'
export KICAD_FP_ROOT='/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'

"$SCHEMATIC_PYTHON" hardware/generate_schematic.py
"$KICAD_CLI" sch export netlist --format kicadxml --output hardware/esp32-cc1101-multiband.xml hardware/esp32-cc1101-multiband.kicad_sch
"$KICAD_CLI" sch export netlist --format kicadsexpr --output hardware/esp32-cc1101-multiband.net hardware/esp32-cc1101-multiband.kicad_sch
"$KICAD_PYTHON" hardware/generate_pcb.py
"$KICAD_PYTHON" hardware/configure_routing.py
"$SCHEMATIC_PYTHON" hardware/generate_bom.py
"$KICAD_PYTHON" hardware/audit_design.py
"$KICAD_CLI" sch erc --format json --output reports/erc-A2.json hardware/esp32-cc1101-multiband.kicad_sch
"$KICAD_CLI" pcb drc --format json --output reports/drc-A2-placement.json hardware/esp32-cc1101-multiband.kicad_pcb
"$KICAD_CLI" sch export svg --output output/svg-A2/ hardware/esp32-cc1101-multiband.kicad_sch
```

Inspect the JSON findings, not just command exit codes. A2 placement DRC reports
zero violations but 217 unconnected items. Incomplete routing is a release
blocker. Do not generate Gerbers from this checkpoint for ordering.

## Separate routing experiment

Run `prepare_routing.py` with KiCad Python to export `tmp/A2-route-input.dsn`.
It regenerates the project net classes and replaces all DSN classes with
explicit membership and top-only restrictions for RF, analog and USB nets.
Keep In1.Cu disabled for traces in the router. This does not configure controlled
impedance or USB differential-pair routing.

The local test used Freerouting 2.4.1, analytics/API/GUI disabled, layers
`true,false,true,true`, 500 um copper-to-edge, 250 um hole clearance,
150 um neck-down, fanout and optimizer disabled, five passes/two-minute limit.
The final session is `tmp/A2-route-v6.ses`; this is a disposable experimental
artifact, not a release source. It is not included in the public repository;
rerun the router to produce a new session. The imported candidate itself is
included for review. Downloaded application paths are machine-local.

Run `import_routing.py tmp/A2-route-v6.ses` with KiCad Python. It writes only
`A2-routing-candidate.kicad_pcb` and copies the matching project settings to
its basename so native DRC uses the same rules. Then run `audit_routing.py`
and native KiCad DRC on that candidate. Do not promote it based on router
completion or a reduced airwire count alone. Preserve manual routing separately
before running the placement generator, which intentionally recreates the board.

For renders, pass `--define-var KICAD10_3DMODEL_DIR=.../SharedSupport/3dmodels`
to `kicad-cli pcb render`. Use `--rotate '330,0,20'` for the current angled
view. Missing exact SMA/custom-RF models are documented in the update report.

Firmware compilation (with PlatformIO installed): `pio run -d firmware/bringup`.
No board is connected or flashed by this build command.

Host checks: `python3 tools/test_firmware.py` and `python3 tools/test_preflight.py`.
For fresh ERC/candidate DRC plus explicit order blockers, run
`python3 tools/preflight.py --kicad-cli "$KICAD_CLI" --output reports/preflight-A2.json`.
Exit 2 means blocked, not a tool crash. No ordering/fabrication action is performed.
See the [checkpoint report](../reports/overnight-checkpoint-2026-09-23.md) for scope.
