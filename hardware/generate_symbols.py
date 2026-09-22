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
