#!/usr/bin/env python3
"""Complete placement inventory, NOT a procurement-approved assembly BOM."""
import csv
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
EXACT = {
    "U1": "ESP32-WROOM-32E-N8", "U2": "CC1101RGPR",
    "U3": "PE42442A-Z", "U4": "PE42442A-Z",
    "U5": "CP2102N-A02-GQFN24", "U6": "AP63203WU-7",
    "U7": "TPS22918DBVR", "U8": "SN74LVC2G125DCTR",
    "L1": "XAL4030-472MEC", "J4": "TSW-103-07-G-S",
    "D3": "APT1608LZGCK", "D4": "APT1608LZGCK",
    "B1": "B0310J50100AHF", "D1": "USBLC6-2SC6",
    "D2": "PESD5V0S1UL", "Q1": "MMBT3904", "Q2": "MMBT3904",
    "J1": "TYPE-C-31-M-12", "J2": "132134",
    "Y1": "ABM8-26.000MHZ-10-1-U-T",
    "F1": "MF-NSMF075/13X-2", "FB1": "BLM18AG601SN1D",
    "SW1": "KMR221GLFS", "SW2": "KMR221GLFS",
    "L40": "0402HP-3N3XJRW", "L41": "0402HP-6N8XJRW",
    "L42": "0402HP-10NXJRW", "L44": "0402HP-10NXJRW",
    "L45": "0402HP-3N6XJRW", "L48": "0402HP-15NXJRW",
    "L51": "0402HP-10NXJRW", "L52": "0402HP-2N2XJRW",
    "R1": "RC0603FR-075K1L", "R2": "RC0603FR-075K1L",
    "R3": "RC0603FR-071KL", "R4": "RC0603FR-071ML",
    "R5": "RC0603FR-0722K1L", "R6": "RC0603FR-0747K5L", "R10": "RC0603FR-0710KL",
    "R11": "RC0603FR-0710KL", "R12": "RC0603FR-07330RL",
    "R13": "RC0603FR-07330RL", "R20": "RC0603FR-0710KL",
    "R21": "RC0603FR-0710KL", "R30": "RC0402FR-0756KL",
    "R31": "RC0603FR-0710KL", "R32": "RC0603FR-0710KL",
    "C5": "CC1206KKX7RCBB472", "C10": "CC0603KRX7R7BB105",
    "C42": "CC0402BRNPO9BNR60", "C44": "CC0402BRNPO9BN1R2",
    "C45": "CC0402CRNPO9BN8R0", "C47": "CC0402JRNPO9BN100",
    "C49": "CC0402CRNPO9BN6R2", "C70": "CC0402KRX7R9BB103",
    "R70": "RC0603FR-0710KL",
}
for ref in ("C1", "C2", "C13"):
    EXACT[ref] = "CC1206MKX5R8BB226"
for ref in ("C11", "C20"):
    EXACT[ref] = "CC0603KRX5R6BB106"
for ref in ("C31", "C32"):
    EXACT[ref] = "CC0402JRNPO9BN150"
for ref in ("C40", "C41"):
    EXACT[ref] = "CC0402JRNPO9BN101"
for ref in ("R33", "R34", "R35"):
    EXACT[ref] = "RC0603FR-0710KL"
EXACT['R71'] = 'RC0603FR-07100KL'
for ref in ("R60", "R61"):
    EXACT[ref] = "RC0402FR-0749R9L"
for ref in ("R40", "R41", "L43", "L46", "L47", "L49", "L50"):
    EXACT[ref] = "RC0402JR-070RL"
for ref in ("C4", "C6", "C7", "C12", "C14", "C21", "C22", "C23", "C24", "C25", "C26", "C30", "C60", "C61", "C71"):
    EXACT[ref] = "GRM155R71C104KA88D"
for ref in ("C3", "C8", "C9"):
    EXACT[ref] = "GRM188R61A475KE15D"


def main():
    root = ET.parse(HERE / "esp32-cc1101-multiband.xml").getroot()
    rows = []
    for comp in root.findall("components/comp"):
        ref = comp.attrib["ref"]
        value = comp.findtext("value", "")
        footprint = comp.findtext("footprint", "")
        if not footprint:
            continue
        dnp = "DNP" in value.upper()
        bare_pad = ref.startswith("TP")
        populated = not dnp and not bare_pad
        status = "VERIFY_STOCK_AND_ASSEMBLY" if ref in EXACT else "SELECT_EXACT_PART"
        notes = ""
        if ref.startswith(("C", "L", "R")):
            notes = "Verify selected tolerance, voltage/current rating and applicable DC-bias derating."
        if (ref.startswith("L") and ref != "L1") or (ref.startswith(("C", "R")) and 40 <= int(ref[1:]) <= 54):
            notes = "RF starting value; choose RF-rated series/Q/SRF and tune on actual PCB."
        if ref == "J2":
            notes = "Amphenol standard SMA female straight TH, 50 ohm; drawing/physical fit approval pending."
        if ref == "J1":
            notes = "HRO base M-12 variant; do not substitute M-12A/B/C without drawing review."
        if ref == "Y1":
            notes = "26 MHz, four pads, CL 10 pF, ESR 50 ohm; -10 to +60 C part rating. Startup and load trim pending."
        if ref in ("C31", "C32"):
            notes = "15 pF C0G starting value uses TI typical 2.5 pF total stray: 15/2+2.5=10 pF. Measure/trim."
        if ref == "F1":
            notes = "Bourns 1206, hold 0.75 A at 23 C / 0.61 A at 50 C, 13.2 V, R1max 0.35ohm. NOT a USB current limiter; test fault/thermal behavior."
        if ref == "FB1":
            notes = "Murata 0603, 600 ohm at 100 MHz, 0.5 A, DCR <=0.38 ohm."
        if ref == "U6":
            notes = "Fixed 3.3 V buck; input must stay >=3.8 V. 2 A IC rating is NOT USB/board capacity."
        if ref in ("C1", "C2", "C13"):
            notes = "22uF 25V X5R 1206; bias curve reviewed. Verify effective capacitance, aging and transient margin on hardware."
        if ref == "L1":
            notes = "4.7uH +/-20%; 44.1mOhm max DCR; marked terminal 1 toward BUCK_SW. Verify temperature/ripple."
        if ref == "J4":
            notes = "Ship UNJUMPERED; loose SNT-100-BK-G accessory. AUTO 1-2 only after CP2102N 500mA configuration; EXT 2-3 only adequate 5V source."
        if ref in ("U3", "U4"):
            notes = "30MHz-6GHz switch; A3 pinout/control only. Datasheet capability does not validate complete RF chain."
        if dnp:
            status = "DNP_DEFAULT"
        if bare_pad:
            status = "PCB_FEATURE_NO_PURCHASE"
        rows.append({
            "Reference": ref, "Value": value, "Footprint": footprint,
            "Proposed part": EXACT.get(ref, ""), "DNP": "yes" if dnp else "no",
            "Qty per board": int(populated), "Qty for five": 5 * int(populated),
            "Status": status, "Notes": notes,
        })
    with (HERE / "bom-draft.csv").open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    print(f"BOM: {len(rows)} schematic footprints; quantities exclude spares, DNP and bare pads")
    with (HERE / "bom-accessories.csv").open("w", newline="") as out:
        writer = csv.writer(out, lineterminator='\n')
        writer.writerow(["Item", "Proposed part", "Qty per board", "Qty for five", "Notes"])
        writer.writerow(["J4 loose shunt", "SNT-100-BK-G", 1, 5,
                         "Do not fit before CP2102N configuration. Verify stock; no order authorized."])


if __name__ == "__main__":
    main()
