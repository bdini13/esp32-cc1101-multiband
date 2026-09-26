#!/usr/bin/env python3
"""Geometry, resistance and cross-layer fault injection; KiCad Python required."""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'hardware'))
import route_metrics as m
import pcbnew as p

class MetricsTests(unittest.TestCase):
    def test_crossing_and_tangent(self):
        self.assertEqual(m.segment_rectangle((-2,0),(2,0),1,1),0)
        self.assertEqual(m.segment_rectangle((-2,1),(2,1),1,1),0)
    def test_zero_length_and_outside(self):
        self.assertAlmostEqual(m.segment_rectangle((2,2),(2,2),1,1),2**.5)
        self.assertEqual(m.segment_rectangle((0,0),(0,0),1,1),0)
        self.assertAlmostEqual(m.segment_rectangle((-2,2),(2,2),1,1),1)
    def test_near_corner(self):
        self.assertAlmostEqual(m.segment_rectangle((2,0),(0,2.2),1,1),.1/(1+1.1**2)**.5)
    def test_resistance_units(self):
        self.assertAlmostEqual(m.copper_resistance(10,.2,.035),.0304359885714,places=10)
        self.assertGreater(m.via_resistance(.2),m.via_resistance(.3))
    def test_graph_chooses_single_lower_resistance_path(self):
        n=m.Network.__new__(m.Network);n.g={};n.pads={'A':'a','B':'b','C':'c'}
        n.edge('a','b',10,{'kind':'trace'});n.edge('a','c',2,{'kind':'trace'});n.edge('c','b',3,{'kind':'trace'})
        self.assertEqual(n.path('A','B')[0],5)
    def test_disconnected_graph_rejected(self):
        n=m.Network.__new__(m.Network);n.g={};n.pads={'A':'a','B':'b'}
        with self.assertRaises(RuntimeError):n.path('A','B')
    def test_actual_board_and_injected_bottom_layer_intrusion(self):
        pcb=ROOT/'hardware/A3-routing-candidate.kicad_pcb';b=p.LoadBoard(str(pcb))
        settings=json.loads(pcb.with_suffix('.kicad_pro').read_text())
        classes={e['pattern']:e['netclass'] for e in settings['net_settings']['netclass_patterns']}
        self.assertTrue(all(e['clearance_mm']>=.2 for e in m.oscillator_clearances(b,classes)))
        crystal=next(f for f in b.GetFootprints() if f.GetReference()=='Y1')
        point=next(q for q in crystal.Pads() if q.GetNumber()=='1').GetPosition()
        t=p.PCB_TRACK(b);t.SetStart(point);t.SetEnd(point+p.VECTOR2I(p.FromMM(.1),0))
        t.SetLayer(p.B_Cu);t.SetWidth(p.FromMM(.2));t.SetNet(b.FindNet('/SPI_MISO'));b.Add(t)
        self.assertTrue(any(e['net']=='/SPI_MISO' and e['clearance_mm']<0
                            for e in m.oscillator_clearances(b,classes)))

if __name__=='__main__':unittest.main()
