"""Project symbols with named, electrically typed pins; no connector stand-ins."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def symbol(name, pins, footprint, url):
    left = pins[:(len(pins) + 1) // 2]
    right = pins[len(left):]
    height = (max(len(left), len(right)) + 1) * 1.27
    out = [f'(symbol "{name}" (pin_names (offset 0.5)) (in_bom yes) (on_board yes)',
           f'(property "Reference" "U" (at 0 {height + 2.54} 0) (effects (font (size 1.27 1.27))))',
           f'(property "Value" "{name}" (at 0 {height + 5.08} 0) (effects (font (size 1.27 1.27))))',
           f'(property "Footprint" "{footprint}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'(property "Datasheet" "{url}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'(symbol "{name}_0_1" (rectangle (start -10.16 {height}) (end 10.16 {-height}) (stroke (width 0.254) (type default)) (fill (type background))))',
           f'(symbol "{name}_1_1"']
    for side, group in enumerate((left, right)):
        for index, (number, label, kind) in enumerate(group):
            y = (len(group) - 1) * 1.27 - index * 2.54
            x, angle = (-12.7, 0) if side == 0 else (12.7, 180)
            out.append(f'(pin {kind} line (at {x} {y} {angle}) (length 2.54) '
                       f'(name "{label}" (effects (font (size 1 1)))) '
                       f'(number "{number}" (effects (font (size 1 1)))))')
    return '\n'.join(out) + '))'


def main():
    cc = [(1, 'SCLK', 'input'), (2, 'SO_GDO1', 'output'),
          (3, 'GDO2', 'output'), (4, 'DVDD', 'power_in'),
          (5, 'DCOUPL', 'power_out'), (6, 'GDO0', 'bidirectional'),
          (7, '~{CSn}', 'input'), (8, 'XOSC_Q1', 'passive'),
          (9, 'AVDD', 'power_in'), (10, 'XOSC_Q2', 'passive'),
          (11, 'AVDD', 'power_in'), (12, 'RF_P', 'passive'),
          (13, 'RF_N', 'passive'), (14, 'AVDD', 'power_in'),
          (15, 'AVDD', 'power_in'), (16, 'GND', 'power_in'),
          (17, 'RBIAS', 'passive'), (18, 'DGUARD', 'power_in'),
          (19, 'GND', 'power_in'), (20, 'SI', 'input'), (21, 'EP_GND', 'power_in')]
    sw = [(1, 'VDD', 'power_in'), (2, 'V2', 'input'), (3, 'V1', 'input'),
          (4, 'RF3', 'passive'), (5, 'RF1', 'passive'), (6, 'RFin', 'passive'),
          (7, 'RF2', 'passive'), (8, 'GND', 'power_in')]
    bal = [(1, 'UNBAL_50R', 'passive'), (2, 'GND', 'passive'),
           (3, 'BAL_N', 'passive'), (4, 'BAL_P', 'passive'),
           (5, 'DNC', 'no_connect'), (6, 'NC', 'no_connect')]
    definitions = [
        symbol('AP63203', [(1, 'FB', 'input'), (2, 'EN', 'input'),
                          (3, 'VIN', 'power_in'), (4, 'GND', 'power_in'),
                          (5, 'SW', 'power_out'), (6, 'BST', 'passive')],
               'ESP32_CC1101_RF:Diodes_TSOT26', 'https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf'),
        symbol('TPS22918', [(1, 'VIN', 'power_in'), (2, 'GND', 'power_in'),
                          (3, 'ON', 'input'), (4, 'CT', 'passive'),
                          (5, 'QOD', 'passive'), (6, 'VOUT', 'power_out')],
               'Package_TO_SOT_SMD:SOT-23-6', 'https://www.ti.com/lit/ds/symlink/tps22918.pdf'),
        symbol('SN74LVC2G125', [(1, '~{1OE}', 'input'), (2, '1A', 'input'),
                              (3, '2Y', 'tri_state'), (4, 'GND', 'power_in'),
                              (5, '2A', 'input'), (6, '1Y', 'tri_state'),
                              (7, '~{2OE}', 'input'), (8, 'VCC', 'power_in')],
               'Package_SO:SSOP-8_2.95x2.8mm_P0.65mm', 'https://www.ti.com/lit/ds/symlink/sn74lvc2g125.pdf'),
        symbol('PE42442', [(n, {5:'RF4',8:'RF3',11:'RF2',14:'RF1',16:'VDD',
                               17:'V1',18:'V2',19:'V3',20:'VSS_EXT',22:'RFC',25:'EP_GND'}.get(n,'GND'),
                           'input' if n in (17,18,19) else 'passive' if n in (5,8,11,14,22) else 'power_in')
                          for n in range(1,26)],
               'ESP32_CC1101_RF:pSemi_PE42442_QFN24', 'https://psemi.com/pdf/datasheets/pe42442ds.pdf'),
        symbol('ABM8', [(1, 'XTAL1', 'passive'), (2, 'GND', 'passive'),
                       (3, 'XTAL2', 'passive'), (4, 'GND', 'passive')],
               'ESP32_CC1101_RF:Abracon_ABM8_4Pin_3.2x2.5mm', 'https://abracon.com/Resonators/abm8.pdf'),
        symbol('CC1101', cc, 'Package_DFN_QFN:Texas_RGP0020H_VQFN-20-1EP_4x4mm_P0.5mm_EP2.4x2.4mm_ThermalVias', 'https://www.ti.com/lit/ds/symlink/cc1101.pdf'),
        symbol('BGS13SN8', sw, 'ESP32_CC1101_RF:Infineon_PG-TSNP-8-1', 'https://www.infineon.com/assets/row/public/documents/24/49/infineon-bgs13sn8-datasheet-en.pdf'),
        symbol('B0310J50100AHF', bal, 'ESP32_CC1101_RF:TTM_B0310J50100AHF', 'https://cdn.ttm.com/repository/products/wireless-xinger/balun-transformers/B0310J50100AHF/B0310J50100AHF.pdf'),
    ]
    target = HERE / 'lib' / 'ESP32_CC1101.kicad_sym'
    target.write_text('(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor")\n' + '\n'.join(definitions) + '\n)\n')
    return target


if __name__ == '__main__':
    print(main())
