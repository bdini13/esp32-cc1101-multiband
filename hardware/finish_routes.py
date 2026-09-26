#!/usr/bin/env python3
"""A3 local finishing routes, applied to the imported v3 checkpoint.

Run with an explicit input PCB; native DRC and fresh netlist parity are mandatory.
This is not a generic autorouter or an order-release tool.
"""
from pathlib import Path
import sys
import shutil
import pcbnew as p

HERE=Path(__file__).resolve().parent

def main():
    b=p.LoadBoard(sys.argv[1])
    fps={f.GetReference():f for f in b.GetFootprints()}
    def pt(xy):return p.VECTOR2I(p.FromMM(xy[0]),p.FromMM(xy[1]))
    def xy(q):v=q.GetPosition();return p.ToMM(v.x),p.ToMM(v.y)
    def pad(ref,num):return next(q for q in fps[ref].Pads() if q.GetNumber()==str(num))
    def route(net,points,width=.2,layer=p.F_Cu):
        for a,z in zip(points,points[1:]):
            t=p.PCB_TRACK(b);t.SetStart(pt(a));t.SetEnd(pt(z));t.SetWidth(p.FromMM(width))
            t.SetLayer(layer);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
    def via(net,pos):
        v=p.PCB_VIA(b);v.SetPosition(pt(pos));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.2))
        v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu)
        v.SetNet(b.FindNet(net));v.SetLocked(True);b.Add(v)
    # Shift only the known VBUS fanout to leave clearance for CC1.
    old=pt((6.2,16.25));new=pt((6.2,16.05));moved=0
    for t in b.GetTracks():
        if t.GetNetname()!='/VBUS_IN':continue
        if isinstance(t,p.PCB_VIA):
            if t.GetPosition()==old:t.SetPosition(new);moved+=1
        else:
            if t.GetStart()==old:t.SetStart(new)
            if t.GetEnd()==old:t.SetEnd(new)
    assert moved==1,'Unexpected source checkpoint: VBUS fanout not found exactly once'
    for t in b.GetTracks():
        if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/VBUS_IN' and t.GetLayer()==p.In2_Cu:
            if t.GetStart()==pt((4.6,16.25)):t.SetStart(pt((4.6,15.6)))
            if t.GetEnd()==pt((4.6,16.25)):t.SetEnd(pt((4.6,15.6)))
    # Shift C60 0.4 mm north to make room for the VDD escape.
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA):continue
        for oldxy in ((63.92,14.8),(64.88,14.8)):
            if t.GetStart()==pt(oldxy):t.SetStart(pt((oldxy[0],14.4)))
            if t.GetEnd()==pt(oldxy):t.SetEnd(pt((oldxy[0],14.4)))
    fps['C60'].SetPosition(pt((64.4,14.4)))
    via('/+3V3_RF',(46.5,18.9))
    route('/+3V3_RF',[xy(pad('C21',1)),(46.5,18.9)],.2)
    route('/+3V3_RF',[(46.5,18.9),(46.5,20.8),(47.18,20.8)],.2,p.B_Cu)
    via('/+3V3_RF',(64.6,15.4));via('/+3V3_RF',(63.35,14.38))
    route('/+3V3_RF',[xy(pad('U3',16)),(64.6,15.4)],.2)
    route('/+3V3_RF',[(64.6,15.4),(64.6,14.38),(63.35,14.38)],.2,p.B_Cu)
    route('/GND',[xy(pad('C8',2)),(11.2,20.45)],.2)
    # Thermal via in the exposed ground pad: require filled/capped processing.
    via('/GND',(16,19.4))
    via('/USB_CC1',(5.55,16.675));via('/USB_CC1',(5.2,26.3))
    route('/USB_CC1',[xy(pad('J1','A5')),(6.9,16.75),(6.825,16.675),(5.55,16.675)],.15)
    route('/USB_CC1',[(5.55,16.675),(5.45,16.775),(5.45,19),(4.5,19.95),(4.5,25.6),(5.2,26.3)],.2,p.B_Cu)
    route('/USB_CC1',[(5.2,26.3),xy(pad('R1',1))],.2)
    b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones())
    out=HERE/'A3-routing-candidate.kicad_pcb'
    p.SaveBoard(str(out),b)
    shutil.copyfile(Path(sys.argv[1]).with_suffix('.kicad_pro'),out.with_suffix('.kicad_pro'))
    print(out)

if __name__=='__main__':main()
