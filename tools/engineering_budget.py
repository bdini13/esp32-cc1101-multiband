#!/usr/bin/env python3
"""Reproducible A3 screening calculations, NOT measured hardware guarantees.

Sources and assumptions are explained in docs/06-A3-prototype-engineering.md.
No typical curve is promoted to a guaranteed worst-case specification here.
"""
import json
from math import exp,log,sqrt
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def microstrip(w,h=.2104,t=.035,er=4.4):
    # IPC-style first-order equation, also published in TI DP83848Q-Q1.
    # Omits mask, etch trapezoid, pads, coplanar copper and dispersion.
    return 87/sqrt(er+1.41)*log(5.98*h/(.8*w+t))

def input_current(v_connector, i_output, efficiency=.85, overhead=.020,
                  series_resistance=.50):
    # Conservative screening allowance: fuse + load switch + PCB resistance.
    current=.4
    for _ in range(100):
        vin=v_connector-current*series_resistance
        current=3.3*i_output/(efficiency*vin)+overhead
    return {'connector_v':v_connector,'output_a':i_output,
            'input_a':round(current,4),'buck_input_v':round(vin,4),
            'within_500mA_screen':current<=.5}

def main():
    rf=microstrip(.35)
    usb=2*microstrip(.30)*(1-.48*exp(-.96*.20/.2104))
    assert 45<rf<55 and 81<usb<99
    report={
        'revision':'A3','status':'CALCULATED_ASSUMPTIONS_NOT_BENCH_VALIDATION',
        'impedance_screen':{'model':'first-order, bare microstrip; NOT a field solver',
            'rf_width_mm':.35,'rf_ohm_estimate':round(rf,2),
            'usb_width_mm':.30,'usb_gap_mm':.20,'usb_ohm_estimate':round(usb,2),
            'stackup_target':'JLC04161H-7628, L1-L2 0.2104mm, Dk4.4, outer Cu35um',
            'limitations':'Pad necks, USB contact crossover and uncoupled bends differ; confirm with fabricator.'},
        'input_power_screens':[input_current(v,i) for v in (5.0,4.75,4.4) for i in (.5,.55)],
        'power_assumptions':{'buck_efficiency':.85,'usb_overhead_a':.020,
            'input_series_resistance_ohm':.50,'buck_loss_at_550mA_w':round(3.3*.55*(1/.85-1),3),
            'old_ldo_loss_at_550mA_w':round((5-3.3)*.55,3),
            'warning':'Efficiency/resistance are assumptions, not certified worst-case. USB full load is not guaranteed at low cable-end voltage.'},
        'inductor_ripple':{'vin_v':5.25,'vout_v':3.3,'l_min_uH':4.7*.8,'f_min_MHz':.9,
            'ripple_pp_a':round(3.3*(1-3.3/5.25)/(4.7e-6*.8*.9e6),3),
            'peak_at_550mA_a':round(.55+3.3*(1-3.3/5.25)/(2*4.7e-6*.8*.9e6),3)},
        'capacitor_screen':{'c1_c2_c13':'CC1206MKX5R8BB226',
            'assumed_bias_retention_at_3v3':.80,'assumed_bias_retention_at_5v':.65,
            'tolerance_multiplier':.8,'x5r_temperature_multiplier':.85,
            'estimated_two_output_caps_uF':round(44*.8*.85*.8,2),
            'estimated_input_cap_uF':round(22*.8*.85*.65,2),
            'warning':'Bias factors are approximate typical-curve readings. Aging and lot variation need measurement/margin review.'},
        'slew_screen':{'ct_pF':10000,'typical_10_to_90_rise_ms_at_5V':(0.55*10000+30)*5/1000,
            'warning':'Not a current limiter. Buck soft-start/load steps and USB attach charge require scope measurement.'},
        'rf_reset_screen':{'external_pullup_ohm':10000,'assumed_internal_pulldown_ohm':45000,
            'logic_v_with_2uA_leakage_at_3V':round(3*45000/55000-2e-6*(10000*45000/55000),3),
            'required_switch_vih_v':1.17,'warning':'Internal pull is typical, not a bound. Verify reset/boot waveforms.'},
        'prototype_envelope':'Indoor bench, nominal 5V; no transmit, no USB power-budget claim for arbitrary loads/ports.',
    }
    (ROOT/'reports/engineering-budget-A3.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
