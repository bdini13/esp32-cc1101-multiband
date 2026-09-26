#!/usr/bin/env python3
"""Generate the Rev A architecture schematic.

The RF topology and starting values follow the published M5Stack Cap CC1101
Rev 0.3 reference schematic. They are captured as a reproducible design basis,
not treated as proof that a different PCB layout is already tuned. Exact RF
footprints, placement, controlled impedance, and bench/VNA validation remain
pre-order gates. The generated schematic is therefore NOT an order candidate.
"""

from pathlib import Path

import kicad_sch_api as ksa
from kicad_sch_api.library.cache import get_symbol_cache
from kicad_sch_api.core.pin_utils import get_component_pin_info
from generate_symbols import main as generate_symbols


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "esp32-cc1101-multiband.kicad_sch"


def add(sch, lib_id, ref, value, x, y, footprint=None, **props):
    return sch.components.add(
        lib_id,
        reference=ref,
        value=value,
        position=(x, y),
        footprint=footprint,
        **props,
    )


def label(sch, ref, pin, net):
    # Explicit outward stubs keep net names outside IC bodies. The library's
    # pin-label convenience method places names over the pin names in KiCad 10.
    comp=sch.components.get(ref)
    pos, angle=get_component_pin_info(comp,str(pin))
    length=3.81 if ref.startswith(('U','J','B','Y')) else 0
    if ref=='J1': length=0  # Dense symbol has intersecting alternate-pin stubs.
    dx,dy={0:(-length,0),90:(0,length),180:(length,0),270:(0,-length)}[int(angle)%360]
    endpoint=(pos.x+dx,pos.y+dy)
    if length: sch.add_wire((pos.x,pos.y),endpoint)
    sch.labels.add(net,endpoint,rotation=0,size=.85,
                   justify_h='right' if dx<0 else 'left',justify_v='bottom')


def labels(sch, ref, mapping):
    for pin, net in mapping.items():
        label(sch, ref, pin, net)


def nc(sch, ref, pin):
    pos = sch.get_component_pin_position(ref, str(pin))
    if pos is not None:
        sch.no_connects.add(pos)


def passive_to_nets(sch, lib_id, ref, value, x, y, net1, net2, footprint):
    add(sch, lib_id, ref, value, x, y, footprint)
    labels(sch, ref, {"1": net1, "2": net2})


def main():
    get_symbol_cache().add_library_path(generate_symbols())
    sch = ksa.create_schematic("ESP32 CC1101 Multiband Rev A")
    sch.set_paper_size("A2")
    sch.set_title_block(
        title="ESP32-WROOM-32E + CC1101 Multiband",
        date="2026-09-26",
        rev="A3 DRAFT",
        company="Personal prototype",
        comments={
            1: "NOT FOR MANUFACTURE - RF footprints/layout/tuning pending verification",
            2: "USB-C power/programming; software-selected 315/433/868/915 MHz",
        },
    )

    # ------------------------------------------------------------------ USB
    sch.add_text("USB-C INPUT, PROTECTION, AND 3.3 V POWER", (60, 18), size=2.0)
    add(
        sch,
        "Connector:USB_C_Receptacle_USB2.0_16P",
        "J1",
        "USB-C USB2.0",
        40,
        60,
        "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    )
    labels(
        sch,
        "J1",
        {
            "A1": "GND", "A4": "VBUS_IN", "A5": "USB_CC1",
            "A6": "USB_DP_CONN", "A7": "USB_DM_CONN", "A9": "VBUS_IN",
            "A12": "GND", "B1": "GND", "B4": "VBUS_IN",
            "B5": "USB_CC2", "B6": "USB_DP_CONN", "B7": "USB_DM_CONN",
            "B9": "VBUS_IN", "B12": "GND", "SH": "CHASSIS",
        },
    )
    nc(sch, "J1", "A8")
    nc(sch, "J1", "B8")

    passive_to_nets(
        sch, "Device:R", "R1", "5.1k 1%", 75, 45,
        "USB_CC1", "GND", "Resistor_SMD:R_0603_1608Metric"
    )
    passive_to_nets(
        sch, "Device:R", "R2", "5.1k 1%", 75, 55,
        "USB_CC2", "GND", "Resistor_SMD:R_0603_1608Metric"
    )
    passive_to_nets(
        sch, "Device:R", "R4", "1M", 75, 75,
        "CHASSIS", "GND", "Resistor_SMD:R_0603_1608Metric"
    )
    passive_to_nets(
        sch, "Device:C", "C5", "4.7nF 1kV", 75, 87,
        "CHASSIS", "GND", "Capacitor_SMD:C_1206_3216Metric"
    )
    add(
        sch, "Power_Protection:USBLC6-2SC6", "D1", "USBLC6-2SC6",
        95, 72, "Package_TO_SOT_SMD:SOT-23-6"
    )
    labels(
        sch,
        "D1",
        {"1": "USB_DP_CONN", "6": "USB_DP", "3": "USB_DM_CONN",
         "4": "USB_DM", "2": "GND", "5": "VBUS_PROTECTED"},
    )
    passive_to_nets(
        sch, "Device:Polyfuse", "F1", "750mA PTC", 95, 35,
        "VBUS_IN", "VBUS_PROTECTED", "Fuse:Fuse_1206_3216Metric"
    )
    passive_to_nets(
        sch, "Device:D_Zener", "D2", "PESD5V0S1UL", 115, 35,
        "VBUS_PROTECTED", "GND", "Diode_SMD:D_SOD-882"
    )
    add(
        sch, "ESP32_CC1101:AP63203", "U6", "AP63203WU-7",
        145, 45, "ESP32_CC1101_RF:Diodes_TSOT26"
    )
    labels(sch, "U6", {"1": "+3V3", "2": "VBUS_SWITCHED", "3": "VBUS_SWITCHED",
                        "4": "GND", "5": "BUCK_SW", "6": "BUCK_BST"})
    passive_to_nets(sch, "Device:L", "L1", "4.7uH XAL4030", 170, 35,
                    "BUCK_SW", "+3V3", "Inductor_SMD:L_Coilcraft_XAL4030-XXX")
    passive_to_nets(sch, "Device:C", "C13", "22uF 25V", 180, 65,
                    "+3V3", "GND", "Capacitor_SMD:C_1206_3216Metric")
    passive_to_nets(sch, "Device:C", "C14", "100nF", 170, 50,
                    "BUCK_BST", "BUCK_SW", "Capacitor_SMD:C_0402_1005Metric")
    add(sch, "ESP32_CC1101:TPS22918", "U7", "TPS22918DBVR", 430, 45,
        "Package_TO_SOT_SMD:SOT-23-6")
    labels(sch, "U7", {"1":"VBUS_PROTECTED", "2":"GND", "3":"MAIN_POWER_EN",
                        "4":"POWER_SLEW", "5":"VBUS_SWITCHED", "6":"VBUS_SWITCHED"})
    passive_to_nets(sch, "Device:C", "C70", "10nF", 460, 40,
                    "POWER_SLEW", "GND", "Capacitor_SMD:C_0402_1005Metric")
    passive_to_nets(sch, "Device:R", "R70", "10k", 460, 55,
                    "USB_ACTIVE", "GND", "Resistor_SMD:R_0603_1608Metric")
    passive_to_nets(sch, "Device:R", "R71", "100k", 460, 70,
                    "MAIN_POWER_EN", "GND", "Resistor_SMD:R_0603_1608Metric")
    add(sch, "Connector_Generic:Conn_01x03", "J4", "POWER ARM AUTO / EXT", 430, 83,
        "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical")
    labels(sch, "J4", {"1":"USB_ACTIVE", "2":"MAIN_POWER_EN", "3":"+3V3_USB"})
    sch.add_text("J4: ship UNJUMPERED. Configure CP2102N for 500mA before AUTO (1-2).\nEXT (2-3) only with a known adequate 5V source; no USB power negotiation.", (405, 105), size=1)
    passive_to_nets(
        sch, "Device:C", "C1", "22uF 25V", 130, 65,
        "VBUS_SWITCHED", "GND", "Capacitor_SMD:C_1206_3216Metric"
    )
    passive_to_nets(
        sch, "Device:C", "C2", "22uF 25V", 160, 65,
        "+3V3", "GND", "Capacitor_SMD:C_1206_3216Metric"
    )
    for ref, net, x in (("PWR1", "GND", 135),
                        ("PWR2", "VBUS_PROTECTED", 145),
                        ("PWR3", "+3V3_RF", 155), ("PWR4", "+3V3_USB", 165),
                        ("PWR5", "+3V3", 175)):
        add(sch, "power:PWR_FLAG", ref, "PWR_FLAG", x, 82, None)
        label(sch, ref, "1", net)

    # --------------------------------------------------------- USB-to-UART
    sch.add_text("USB-UART AND PROGRAMMING", (190, 18), size=2.0)
    add(
        sch, "Interface_USB:CP2102N-Axx-xQFN24", "U5", "CP2102N-A02-GQFN24",
        225, 62, "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm"
    )
    labels(
        sch,
        "U5",
        {
            "2": "GND", "25": "GND", "3": "USB_DP", "4": "USB_DM",
            "5": "+3V3_USB", "6": "+3V3_USB", "7": "VBUS_PROTECTED",
            "8": "USB_VBUS_SENSE", "9": "CP2102_RST_N",
            "15": "USB_ACTIVE", "19": "AUTO_RTS_N", "20": "UART_RX_USB", "21": "UART_TX_USB",
            "23": "AUTO_DTR_N",
        },
    )
    for pin in ("1", "10", "11", "12", "13", "14", "16", "17", "18", "22", "24"):
        nc(sch, "U5", pin)
    passive_to_nets(
        sch, "Device:C", "C3", "4.7uF", 265, 35,
        "+3V3_USB", "GND", "Capacitor_SMD:C_0603_1608Metric"
    )
    passive_to_nets(
        sch, "Device:C", "C4", "100nF", 265, 47,
        "+3V3_USB", "GND", "Capacitor_SMD:C_0402_1005Metric"
    )
    passive_to_nets(
        sch, "Device:R", "R3", "1k", 265, 60,
        "CP2102_RST_N", "+3V3_USB", "Resistor_SMD:R_0603_1608Metric"
    )
    # CP2102N Figure 2.1: internal regulator powers only USB-side logic.
    # VIO shares VDD bulk C3; a second bulk capacitor is not fitted at VIO.
    for ref, value, x, y, fp in (
        ("C6", "100nF", 365, 35, "Capacitor_SMD:C_0402_1005Metric"),
        ("C7", "100nF", 380, 35, "Capacitor_SMD:C_0402_1005Metric"),
        ("C8", "DNP", 365, 50, "Capacitor_SMD:C_0603_1608Metric"),
        ("C9", "4.7uF", 380, 50, "Capacitor_SMD:C_0603_1608Metric"),
    ):
        passive_to_nets(sch, "Device:C", ref, value, x, y,
                        "VBUS_PROTECTED" if ref in ("C7", "C9") else "+3V3_USB", "GND", fp)
    add(sch, "ESP32_CC1101:SN74LVC2G125", "U8", "SN74LVC2G125DCTR", 430, 145,
        "Package_SO:SSOP-8_2.95x2.8mm_P0.65mm")
    labels(sch, "U8", {"1":"GND", "2":"UART_TX_USB", "3":"UART_RX_USB", "4":"GND",
                        "5":"UART_TX_ESP", "6":"UART_RX_ESP", "7":"GND", "8":"+3V3"})
    passive_to_nets(sch, "Device:C", "C71", "100nF", 460, 145,
                    "+3V3", "GND", "Capacitor_SMD:C_0402_1005Metric")
    passive_to_nets(sch, "Device:R", "R5", "22.1k 1%", 365, 70,
                    "VBUS_PROTECTED", "USB_VBUS_SENSE", "Resistor_SMD:R_0603_1608Metric")
    passive_to_nets(sch, "Device:R", "R6", "47.5k 1%", 380, 70,
                    "USB_VBUS_SENSE", "GND", "Resistor_SMD:R_0603_1608Metric")
    # Espressif DevKitC V4 automatic-download circuit. Cross-connecting each
    # transistor emitter to the opposite handshake input prevents DTR and RTS
    # asserted together from holding the ESP32 in reset.
    passive_to_nets(
        sch, "Device:R", "R20", "10k", 285, 52,
        "AUTO_DTR_N", "AUTO_Q1_BASE", "Resistor_SMD:R_0603_1608Metric"
    )
    passive_to_nets(
        sch, "Device:R", "R21", "10k", 285, 72,
        "AUTO_RTS_N", "AUTO_Q2_BASE", "Resistor_SMD:R_0603_1608Metric"
    )
    add(
        sch, "Transistor_BJT:Q_NPN_BEC", "Q1", "MMBT3904",
        315, 52, "Package_TO_SOT_SMD:SOT-23"
    )
    labels(sch, "Q1", {"1": "AUTO_Q1_BASE", "2": "AUTO_RTS_N",
                        "3": "ESP_EN"})
    add(
        sch, "Transistor_BJT:Q_NPN_BEC", "Q2", "MMBT3904",
        315, 72, "Package_TO_SOT_SMD:SOT-23"
    )
    labels(sch, "Q2", {"1": "AUTO_Q2_BASE", "2": "AUTO_DTR_N",
                        "3": "ESP_IO0"})

    # --------------------------------------------------------------- ESP32
    sch.add_text("ESP32-WROOM-32E", (65, 105), size=2.0)
    add(
        sch, "RF_Module:ESP32-WROOM-32E", "U1", "ESP32-WROOM-32E-N8",
        80, 160, "RF_Module:ESP32-WROOM-32E"
    )
    labels(
        sch,
        "U1",
        {
            "2": "+3V3", "3": "ESP_EN", "6": "EXP_GPIO34",
            "7": "EXP_GPIO35", "8": "RF_SW0", "9": "RF_SW1",
            "10": "STATUS_LED", "11": "CC1101_GDO0", "12": "CC1101_GDO2",
            "13": "EXP_GPIO14", "16": "EXP_GPIO13", "25": "ESP_IO0",
            "26": "RF_DISABLE", "27": "RF_OUT0", "28": "RF_OUT1",
            "30": "SPI_SCLK", "31": "SPI_MISO", "33": "CC1101_CSN",
            "34": "UART_RX_ESP", "35": "UART_TX_ESP", "36": "EXP_GPIO22",
            "37": "SPI_MOSI", "[1,15,38,39]": "GND",
        },
    )
    for pin in ("4", "5", "14", "23", "24", "29"):
        nc(sch, "U1", pin)
    passive_to_nets(
        sch, "Device:R", "R10", "10k", 125, 120,
        "ESP_EN", "+3V3", "Resistor_SMD:R_0603_1608Metric"
    )
    passive_to_nets(
        sch, "Device:C", "C10", "1uF", 145, 120,
        "ESP_EN", "GND", "Capacitor_SMD:C_0603_1608Metric"
    )
    passive_to_nets(
        sch, "Switch:SW_Push", "SW1", "RESET", 165, 120,
        "ESP_EN", "GND", "Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2"
    )
    passive_to_nets(
        sch, "Device:R", "R11", "10k", 125, 135,
        "ESP_IO0", "+3V3", "Resistor_SMD:R_0603_1608Metric"
    )
    passive_to_nets(
        sch, "Switch:SW_Push", "SW2", "BOOT", 165, 135,
        "ESP_IO0", "GND", "Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2"
    )
    passive_to_nets(
        sch, "Device:R", "R12", "330R 1%", 125, 185,
        "STATUS_LED", "STATUS_LED_A", "Resistor_SMD:R_0603_1608Metric"
    )
    passive_to_nets(
        sch, "Device:LED", "D3", "STATUS GREEN", 145, 185,
        "GND", "STATUS_LED_A", "LED_SMD:LED_0603_1608Metric"
    )
    passive_to_nets(
        sch, "Device:R", "R13", "330R 1%", 125, 198,
        "+3V3", "POWER_LED_A", "Resistor_SMD:R_0603_1608Metric"
    )
    passive_to_nets(
        sch, "Device:LED", "D4", "POWER GREEN", 145, 198,
        "GND", "POWER_LED_A", "LED_SMD:LED_0603_1608Metric"
    )
    add(
        sch, "Connector_Generic:Conn_01x10", "J3", "EXPANSION (DNP)",
        195, 175, "Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical"
    )
    labels(
        sch, "J3",
        {"1": "+3V3", "2": "VBUS_PROTECTED", "3": "GND",
         "4": "EXP_GPIO13", "5": "EXP_GPIO14", "6": "RF_OUT0",
         "7": "RF_OUT1", "8": "EXP_GPIO22", "9": "EXP_GPIO34",
         "10": "EXP_GPIO35"},
    )

    # Local ESP32 supply storage; C2 at the regulator is not a substitute.
    passive_to_nets(sch, "Device:C", "C11", "10uF", 210, 205,
                    "+3V3", "GND", "Capacitor_SMD:C_0603_1608Metric")
    passive_to_nets(sch, "Device:C", "C12", "100nF", 225, 205,
                    "+3V3", "GND", "Capacitor_SMD:C_0402_1005Metric")

    # ------------------------------------------------------- CC1101 DIGITAL
    sch.add_text("CC1101 CORE - NAMED ELECTRICAL PINS",
                 (235, 105), size=2.0)
    add(
        sch, "ESP32_CC1101:CC1101", "U2", "CC1101RGPR",
        275, 160,
        "Package_DFN_QFN:Texas_RGP0020H_VQFN-20-1EP_4x4mm_P0.5mm_EP2.4x2.4mm_ThermalVias",
    )
    labels(
        sch,
        "U2",
        {
            "1": "SPI_SCLK", "2": "SPI_MISO", "3": "CC1101_GDO2",
            "4": "+3V3_RF", "5": "CC1101_DCOUPL", "6": "CC1101_GDO0",
            "7": "CC1101_CSN", "8": "CC1101_XOSC_Q1", "9": "+3V3_RF",
            "10": "CC1101_XOSC_Q2", "11": "+3V3_RF", "12": "CC1101_RF_P",
            "13": "CC1101_RF_N", "14": "+3V3_RF", "15": "+3V3_RF",
            "16": "GND", "17": "CC1101_RBIAS", "18": "+3V3_RF",
            "19": "GND", "20": "SPI_MOSI", "21": "GND",
        },
    )
    passive_to_nets(
        sch, "Device:FerriteBead", "FB1", "600R@100MHz", 245, 125,
        "+3V3", "+3V3_RF", "Inductor_SMD:L_0603_1608Metric"
    )
    passive_to_nets(
        sch, "Device:C", "C20", "10uF", 260, 125,
        "+3V3_RF", "GND", "Capacitor_SMD:C_0603_1608Metric"
    )
    for i, x in enumerate((305, 317, 329, 341, 353), start=21):
        passive_to_nets(
            sch, "Device:C", f"C{i}", "100nF", x, 125,
            "+3V3_RF", "GND", "Capacitor_SMD:C_0402_1005Metric"
        )
    passive_to_nets(sch, "Device:C", "C26", "100nF", 368, 125,
                    "+3V3_RF", "GND", "Capacitor_SMD:C_0402_1005Metric")
    passive_to_nets(
        sch, "Device:C", "C30", "100nF", 315, 180,
        "CC1101_DCOUPL", "GND", "Capacitor_SMD:C_0402_1005Metric"
    )
    passive_to_nets(
        sch, "Device:R", "R30", "56k 1%", 335, 180,
        "CC1101_RBIAS", "GND", "Resistor_SMD:R_0402_1005Metric"
    )
    add(
        sch, "ESP32_CC1101:ABM8", "Y1", "ABM8-26.000MHZ-10-1-U-T", 315, 200,
        "ESP32_CC1101_RF:Abracon_ABM8_4Pin_3.2x2.5mm"
    )
    labels(sch, "Y1", {"1": "CC1101_XOSC_Q1", "3": "CC1101_XOSC_Q2",
                       "2": "GND", "4": "GND"})
    passive_to_nets(
        sch, "Device:C", "C31", "15pF C0G", 335, 198,
        "CC1101_XOSC_Q1", "GND", "Capacitor_SMD:C_0402_1005Metric"
    )
    passive_to_nets(
        sch, "Device:C", "C32", "15pF C0G", 350, 198,
        "CC1101_XOSC_Q2", "GND", "Capacitor_SMD:C_0402_1005Metric"
    )
    passive_to_nets(
        sch, "Device:R", "R31", "10k pullup", 315, 215,
        "RF_SW0", "+3V3_RF", "Resistor_SMD:R_0603_1608Metric"
    )
    passive_to_nets(
        sch, "Device:R", "R32", "10k pullup", 335, 215,
        "RF_SW1", "+3V3_RF", "Resistor_SMD:R_0603_1608Metric"
    )
    passive_to_nets(sch, "Device:R", "R33", "10k pullup", 355, 215,
                    "RF_DISABLE", "+3V3_RF", "Resistor_SMD:R_0603_1608Metric")
    for ref, net, x in (("R34", "RF_OUT0", 375), ("R35", "RF_OUT1", 395)):
        passive_to_nets(sch, "Device:R", ref, "10k pullup", x, 215,
                        net, "+3V3_RF", "Resistor_SMD:R_0603_1608Metric")

    # -------------------------------------------------------------- RF PATH
    sch.add_text("MULTIBAND RF PATH - REFERENCE VALUES; VNA TUNING REQUIRED",
                 (85, 230), size=2.0)

    # Differential CC1101 port to the 50-ohm broadband balun. C42 provides
    # differential trim; C40/C41 are the series coupling capacitors used by the
    # M5Stack Rev 0.3 reference design.
    passive_to_nets(
        sch, "Device:C", "C40", "100pF C0G", 28, 250,
        "CC1101_RF_N", "BAL_N", "Capacitor_SMD:C_0402_1005Metric"
    )
    passive_to_nets(
        sch, "Device:C", "C41", "100pF C0G", 28, 275,
        "CC1101_RF_P", "BAL_P", "Capacitor_SMD:C_0402_1005Metric"
    )
    passive_to_nets(
        sch, "Device:C", "C42", "0.6pF C0G", 28, 300,
        "CC1101_RF_N", "CC1101_RF_P", "Capacitor_SMD:C_0402_1005Metric"
    )
    add(
        sch, "ESP32_CC1101:B0310J50100AHF", "B1", "B0310J50100AHF",
        52, 275, "ESP32_CC1101_RF:TTM_B0310J50100AHF"
    )
    labels(sch, "B1", {"1": "BALUN_50R", "2": "GND",
                        "3": "BAL_N", "4": "BAL_P"})
    nc(sch, "B1", "5")
    nc(sch, "B1", "6")

    passive_to_nets(
        sch, "Device:L", "L40", "3.3nH 5%", 72, 250,
        "BALUN_50R", "BALUN_M1", "Inductor_SMD:L_0402_1005Metric"
    )
    passive_to_nets(
        sch, "Device:C", "C43", "DNP", 72, 300,
        "BALUN_M1", "GND", "Capacitor_SMD:C_0402_1005Metric"
    )
    passive_to_nets(
        sch, "Device:L", "L41", "6.8nH 5%", 88, 250,
        "BALUN_M1", "RF_SWITCH_IN", "Inductor_SMD:L_0402_1005Metric"
    )
    passive_to_nets(
        sch, "Device:C", "C44", "1.2pF C0G", 88, 300,
        "RF_SWITCH_IN", "GND", "Capacitor_SMD:C_0402_1005Metric"
    )

    for ref, x in (("U3", 122), ("U4", 292)):
        add(
            sch, "ESP32_CC1101:PE42442", ref,
            "PE42442A-Z", x, 275,
            "ESP32_CC1101_RF:pSemi_PE42442_QFN24",
        )
        labels(sch, ref, {"16": "+3V3_RF", "17": "RF_SW0" if ref=="U3" else "RF_OUT0",
                          "18": "RF_SW1" if ref=="U3" else "RF_OUT1",
                          "19": "RF_DISABLE", "5": ref+"_RF4_TERM"})
        for pin in (1,2,3,4,6,7,9,10,12,13,15,20,21,23,24,25):
            label(sch, ref, pin, "GND")
        passive_to_nets(sch, "Device:R", "R60" if ref=="U3" else "R61", "49.9R 1%", x, 350,
                        ref+"_RF4_TERM", "GND", "Resistor_SMD:R_0402_1005Metric")
    for ref, x in (("C60", 115), ("C61", 280)):
        passive_to_nets(sch, "Device:C", ref, "100nF", x, 330,
                        "+3V3_RF", "GND", "Capacitor_SMD:C_0402_1005Metric")

    labels(sch, "U3", {"22": "RF_SWITCH_IN", "14": "RF_315_IN",
                        "11": "RF_433_IN", "8": "RF_868_915_IN"})
    # Reverse outer branches at the output switch so all RF routes can remain
    # on the top layer without crossings. U4 has independent software controls.
    labels(sch, "U4", {"8": "RF_315_OUT", "11": "RF_433_OUT",
                        "14": "RF868_B", "22": "RF_COMBINED"})

    # 315 MHz branch: series L-L-L plus a series-L/shunt-C trap and DNP trim.
    passive_to_nets(sch, "Device:L", "L42", "10nH 5%", 145, 245,
                    "RF_315_IN", "RF315_A", "Inductor_SMD:L_0402_1005Metric")
    passive_to_nets(sch, "Device:L", "L43", "0R", 175, 245,
                    "RF315_A", "RF315_B", "Inductor_SMD:L_0402_1005Metric")
    passive_to_nets(sch, "Device:L", "L44", "10nH 5%", 205, 245,
                    "RF315_B", "RF_315_OUT", "Inductor_SMD:L_0402_1005Metric")
    passive_to_nets(sch, "Device:L", "L45", "3.6nH 5%", 145, 257,
                    "RF315_A", "RF315_TRAP", "Inductor_SMD:L_0402_1005Metric")
    passive_to_nets(sch, "Device:C", "C45", "8pF C0G", 160, 257,
                    "RF315_TRAP", "GND", "Capacitor_SMD:C_0402_1005Metric")
    passive_to_nets(sch, "Device:C", "C46", "DNP", 205, 257,
                    "RF315_B", "GND", "Capacitor_SMD:C_0402_1005Metric")

    # 433 MHz branch.
    passive_to_nets(sch, "Device:L", "L46", "0R", 145, 275,
                    "RF_433_IN", "RF433_A", "Inductor_SMD:L_0402_1005Metric")
    passive_to_nets(sch, "Device:C", "C47", "10pF C0G", 145, 287,
                    "RF433_A", "GND", "Capacitor_SMD:C_0402_1005Metric")
    passive_to_nets(sch, "Device:L", "L47", "0R", 175, 275,
                    "RF433_A", "RF433_B", "Inductor_SMD:L_0402_1005Metric")
    passive_to_nets(sch, "Device:C", "C48", "DNP", 175, 287,
                    "RF433_B", "GND", "Capacitor_SMD:C_0402_1005Metric")
    passive_to_nets(sch, "Device:L", "L48", "15nH 5%", 205, 275,
                    "RF433_B", "RF433_C", "Inductor_SMD:L_0402_1005Metric")
    passive_to_nets(sch, "Device:C", "C49", "6.2pF C0G", 205, 287,
                    "RF433_C", "GND", "Capacitor_SMD:C_0402_1005Metric")
    passive_to_nets(sch, "Device:L", "L49", "0R", 235, 275,
                    "RF433_C", "RF_433_OUT", "Inductor_SMD:L_0402_1005Metric")

    # Shared 868/915 MHz branch.
    passive_to_nets(sch, "Device:L", "L50", "0R", 145, 305,
                    "RF_868_915_IN", "RF868_A", "Inductor_SMD:L_0402_1005Metric")
    passive_to_nets(sch, "Device:C", "C50", "DNP", 160, 317,
                    "RF868_A", "GND", "Capacitor_SMD:C_0402_1005Metric")
    passive_to_nets(sch, "Device:L", "L51", "10nH 5%", 205, 305,
                    "RF868_A", "RF868_B", "Inductor_SMD:L_0402_1005Metric")
    passive_to_nets(sch, "Device:C", "C51", "DNP", 220, 317,
                    "RF868_B", "GND", "Capacitor_SMD:C_0402_1005Metric")

    # Output trim and antenna interface. D5/C53/C54 are DNP on the first build.
    passive_to_nets(sch, "Device:C", "C52", "DNP", 310, 300,
                    "RF_COMBINED", "GND", "Capacitor_SMD:C_0402_1005Metric")
    passive_to_nets(sch, "Device:L", "L52", "2.2nH 5%", 320, 250,
                    "RF_COMBINED", "RF_FEED", "Inductor_SMD:L_0402_1005Metric")
    passive_to_nets(sch, "Device:R", "R41", "0R", 335, 250,
                    "RF_FEED", "RF_SMA", "Resistor_SMD:R_0402_1005Metric")
    passive_to_nets(sch, "Device:C", "C53", "DNP", 330, 300,
                    "RF_FEED", "GND", "Capacitor_SMD:C_0402_1005Metric")
    passive_to_nets(sch, "Device:C", "C54", "DNP", 345, 300,
                    "RF_SMA", "GND", "Capacitor_SMD:C_0402_1005Metric")
    passive_to_nets(sch, "Device:D_TVS", "D5", "RF ESD DNP", 360, 300,
                    "RF_SMA", "GND", "Diode_SMD:D_0402_1005Metric")

    add(
        sch, "Connector:Conn_Coaxial", "J2", "SMA FEMALE VERTICAL 50 OHM",
        365, 260, "Connector_Coaxial:SMA_Amphenol_132134_Vertical"
    )
    labels(sch, "J2", {"1": "RF_SMA", "2": "GND"})
    sch.add_text(
        "RF VALUES ABOVE ARE STARTING VALUES FROM M5STACK CAP CC1101 REV 0.3, NOT A TUNE CERTIFICATE.\n"
        "Do not order until custom RF footprints, placement, impedance geometry, and peer review are complete.",
        (380, 365), size=1.0,
    )

    # Board-level note.
    sch.add_text(
        "REV A ARCHITECTURE CHECKPOINT\n"
        "Transmit disabled by default. Use the correct removable antenna for each band.\n"
        "Regulatory limits depend on region, modulation, power, and application.",
        (285, 18), size=1.2,
    )

    # --------------------------------------------------------- TEST POINTS
    sch.add_text("BRING-UP TEST POINTS", (85, 365), size=2.0)
    test_points = (
        ("TP1", "GND"),
        ("TP2", "VBUS_PROTECTED"),
        ("TP3", "+3V3"),
        ("TP4", "SPI_SCLK"),
        ("TP5", "SPI_MISO"),
        ("TP6", "SPI_MOSI"),
        ("TP7", "CC1101_CSN"),
        ("TP8", "CC1101_GDO0"),
        ("TP9", "CC1101_GDO2"),
        ("TP10", "RF_SW0"),
        ("TP11", "RF_SW1"),
        ("TP12", "UART_TX_ESP"),
    )
    for index, (ref, net) in enumerate(test_points):
        x = 70 + (index % 6) * 35
        y = 380 + (index // 6) * 18
        add(
            sch, "Connector:TestPoint", ref, net, x, y,
            "TestPoint:TestPoint_Pad_D1.0mm",
        )
        label(sch, ref, "1", net)

    sch.save(OUTPUT)
    issues = sch.validate()
    print(f"Saved {OUTPUT}")
    print(f"API validation issues: {len(issues)}")
    for issue in issues[:20]:
        print(issue)


if __name__ == "__main__":
    main()
