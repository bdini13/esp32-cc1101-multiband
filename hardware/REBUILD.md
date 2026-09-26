# A3 regeneration and verification

Use KiCad 10.0.6 and its matching `pcbnew` Python, plus a separate Python
environment containing `kicad-sch-api==0.5.6` from requirements-eda.txt.
Set KICAD_CLI, KICAD_PYTHON, SCHEMATIC_PYTHON, KICAD_SYMBOL_DIR and
KICAD_FP_ROOT to your installation. Do not use system Python for pcbnew
unless that installation provides it.

## Which board is which?

- `esp32-cc1101-multiband.kicad_pcb`: generated placement seed, intentionally unrouted.
- `A3-critical-routes.kicad_pcb`: manually specified RF/clock/USB/power seed.
- `routing/A3-before-local-finishing.kicad_pcb`: preserved imported router checkpoint.
- `routing/A3-before-crystal-refinement.kicad_pcb`: preserved connected layout before the crystal improvement.
- `A3-routing-candidate.kicad_pcb`: current fully connected review candidate.

Every PCB needs its same-basename .kicad_pro so clearances and minimum
track/drill rules are loaded. Loading a checkpoint without its project can
silently apply different defaults. No file is approved for ordering.

## Rebuild the source capture

Run from the repository root. These commands overwrite generated source
capture/placement files. Preserve any manual edits first.

```sh
set -e
"$SCHEMATIC_PYTHON" hardware/generate_symbols.py
"$SCHEMATIC_PYTHON" hardware/generate_a3_footprints.py
"$SCHEMATIC_PYTHON" hardware/generate_schematic.py
"$KICAD_CLI" sch export netlist --format kicadxml --output hardware/esp32-cc1101-multiband.xml hardware/esp32-cc1101-multiband.kicad_sch
"$KICAD_CLI" sch export netlist --format kicadsexpr --output hardware/esp32-cc1101-multiband.net hardware/esp32-cc1101-multiband.kicad_sch
"$SCHEMATIC_PYTHON" tools/sanitize_netlist_paths.py
"$KICAD_PYTHON" hardware/generate_pcb.py
"$SCHEMATIC_PYTHON" hardware/configure_routing.py
"$SCHEMATIC_PYTHON" hardware/generate_bom.py
"$KICAD_PYTHON" hardware/route_critical.py
```

The finishing step shifts C60 0.4 mm north relative to the placement seed.
The later refinement rotates/moves Y1, moves C31/C32 and reroutes the nearby
clock/power/digital geometry. Neither step changes the schematic. The upstream
placement/critical-route seeds intentionally retain their older geometry.

## Reproduce the final crystal refinement

```sh
"$KICAD_PYTHON" hardware/refine_crystal.py hardware/routing/A3-before-crystal-refinement.kicad_pcb hardware/A3-routing-candidate.kicad_pcb
"$KICAD_CLI" pcb drc --format json --output reports/drc-A3-routing-candidate.json hardware/A3-routing-candidate.kicad_pcb
"$KICAD_PYTHON" hardware/audit_connectivity.py hardware/esp32-cc1101-multiband.xml hardware/A3-routing-candidate.kicad_pcb reports/connectivity-A3.json
"$KICAD_PYTHON" hardware/audit_design.py
"$KICAD_PYTHON" hardware/route_metrics.py
"$KICAD_PYTHON" hardware/audit_routing.py
```

The refinement rejects an input whose SHA-256 differs from the preserved
checkpoint and refuses to overwrite its own input. Expected: 180/180 artifact
checks, 6/6 route screens and native DRC 0 violations / 0 unconnected items.
Regenerated UUIDs may differ; do not claim byte-identical output hashes.

## Reproduce the earlier local finishing step

This overwrites the candidate with the **pre-refinement** state. Run the final
refinement above afterward to restore the current geometry.

```sh
"$KICAD_PYTHON" hardware/finish_routes.py hardware/routing/A3-before-local-finishing.kicad_pcb
"$KICAD_CLI" pcb drc --format json --output reports/drc-A3-routing-candidate.json hardware/A3-routing-candidate.kicad_pcb
"$KICAD_PYTHON" hardware/audit_connectivity.py hardware/esp32-cc1101-multiband.xml hardware/A3-routing-candidate.kicad_pcb reports/connectivity-A3.json
"$KICAD_PYTHON" hardware/audit_routing.py
```

Expected: native DRC 0 violations / 0 unconnected items; parity passes.
Never apply this checkpoint-specific finishing script to a different router
output. It is not a generic autorouter.

For a new router run, use `prepare_routing.py hardware/A3-critical-routes.kicad_pcb`
with KiCad Python. It exports `tmp/A3-route-input.dsn`. The A3 experiment used
Freerouting 2.4.1, In1 disabled for traces, minimum neck 0.15 mm, ordinary
via 0.60/0.30 mm, 0.50 mm copper-to-edge and 0.25 mm hole clearance.
RF/analog/USB are top-only except the already locked USB connector crossover.
Preserve all critical routes; a new session requires fresh finishing/review.
Import with `import_routing.py tmp/new-session.ses hardware/A3-critical-routes.kicad_pcb`.
The shipped final candidate, not a claim of deterministic autorouting, is the
review artifact.

## Recheck and reproduce firmware

```sh
"$KICAD_PYTHON" hardware/audit_design.py
"$KICAD_PYTHON" tools/test_connectivity.py
"$KICAD_PYTHON" tools/test_route_metrics.py
"$SCHEMATIC_PYTHON" tools/test_firmware.py
"$SCHEMATIC_PYTHON" tools/test_preflight.py
"$SCHEMATIC_PYTHON" tools/engineering_budget.py
pio run -d firmware/bringup
"$SCHEMATIC_PYTHON" tools/preflight.py --kicad-cli "$KICAD_CLI" --kicad-python "$KICAD_PYTHON" --output reports/preflight-A3.json
```

Artifact audit now passes on the final candidate: both crystal terminals meet
the unchanged 3.5 mm target. Preflight exits 2 for six pending review categories,
with zero machine-screen failures. It freshly reruns schematic parity, the
artifact audit and route metrics. Input hashes include check/generator code
and firmware sources as well as hardware artifacts.
Do not change a threshold or mark a human review approved to make checks green.
Firmware tests/build are host-only; no hardware is flashed by these commands.

## Design images

Use `kicad-cli sch export svg` for the schematic and `pcb export svg` with
`--layers F.Cu,Edge.Cuts --page-size-mode 2 --exclude-drawing-sheet --mode-single`
for the top routing view. Use `pcb render --rotate '330,0,20'` and set
`--define-var KICAD10_3DMODEL_DIR=...` for the 3D image. These are real KiCad
renders, not product photos. USB/SMA/custom-IC 3D bodies are incomplete.

No Gerbers, purchase orders or paid supplier submissions are generated here.
