#!/usr/bin/env python3
"""Checkpoint-specific crystal refinement; always rerun DRC and parity."""
from pathlib import Path
import sys
import shutil
import hashlib
import pcbnew as p

def main():
    source=Path(sys.argv[1]);out=Path(sys.argv[2])
    expected='c3a48f205171fc8cc8fbb7b726f8c19429724a8c3ffed2dd2e0aad3a6224120d'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=expected:
        raise ValueError('Use the preserved A3-before-crystal-refinement checkpoint, not a different board')
    if source.resolve()==out.resolve():raise ValueError('Do not overwrite the preserved checkpoint')
    b=p.LoadBoard(str(source));fps={f.GetReference():f for f in b.GetFootprints()}
    def pt(v):return p.VECTOR2I(p.FromMM(v[0]),p.FromMM(v[1]))
    def xy(v):return (p.ToMM(v.x),p.ToMM(v.y))
    def pad(ref,n):return next(q for q in fps[ref].Pads() if q.GetNumber()==str(n))
    def route(net,points,w=.2,layer=p.F_Cu):
        for a,z in zip(points,points[1:]):
            t=p.PCB_TRACK(b);t.SetStart(pt(a));t.SetEnd(pt(z));t.SetWidth(p.FromMM(w))
            t.SetLayer(layer);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
    def via(net,pos):
        v=p.PCB_VIA(b);v.SetPosition(pt(pos));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.2))
        v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu)
        v.SetNet(b.FindNet(net));v.SetLocked(True);b.Add(v)
    oldpads=[q.GetPosition() for q in fps['Y1'].Pads()]
    for t in list(b.GetTracks()):
        if t.GetNetname() in ('/CC1101_XOSC_Q1','/CC1101_XOSC_Q2'):
            b.RemoveNative(t);continue
        if t.GetNetname()=='/GND' and (t.GetStart() in oldpads or t.GetEnd() in oldpads
                                      or t.GetStart()==pt((51.1,21)) or t.GetEnd()==pt((51.1,21))):
            b.RemoveNative(t)
    # Shift three existing escapes without changing their electrical nets.
    shifts=[('/+3V3_RF',(50.27,20.95),(50.2,20.55)),
            ('/CC1101_CSN',(49.05,20.85),(48.35,20.8)),
            ('/CC1101_GDO0',(47.9,20.45),(47.7,20.25))]
    for net,old,new in shifts:
        for t in list(b.GetTracks()):
            if t.GetNetname()!=net:continue
            if isinstance(t,p.PCB_VIA):
                if t.GetPosition()==pt(old):t.SetPosition(pt(new))
            else:
                if t.GetStart()==pt(old):t.SetStart(pt(new))
                if t.GetEnd()==pt(old):t.SetEnd(pt(new))
    # Rebuild short top fanouts instead of retaining the old bend geometry.
    for t in list(b.GetTracks()):
        if isinstance(t,p.PCB_VIA) or t.GetLayer()!=p.F_Cu:continue
        if t.GetNetname() in ('/CC1101_CSN','/CC1101_GDO0'):
            if t.GetStart().x>p.FromMM(47) and p.FromMM(19)<t.GetStart().y<p.FromMM(22):b.RemoveNative(t)
        if t.GetNetname()=='/+3V3_RF' and p.FromMM(50.1)<t.GetStart().x<p.FromMM(50.4) and p.FromMM(19.8)<t.GetStart().y<p.FromMM(21):b.RemoveNative(t)
    for t in list(b.GetTracks()):
        if isinstance(t,p.PCB_VIA):continue
        if (t.GetNetname()=='/CC1101_GDO0' and t.GetLayer()==p.B_Cu and
            t.GetStart() in (pt((50.884,19.56)),pt((48.8787,21.4287)))):b.RemoveNative(t)
        if t.GetNetname()=='/GND' and t.GetStart()==pt((48.2506,25.4244)):b.RemoveNative(t)
    route('/CC1101_GDO0',[(50.884,19.56),(49.85,19.56),(49.5,19.91),(49.5,20.7),(49.66,20.784)],.2,p.B_Cu)
    route('/CC1101_GDO0',[(48.8787,21.4287),(48.8787,21.4),(47.8,21.4),(47.8,20.35),(47.7,20.25)],.2,p.B_Cu)
    for t in list(b.GetTracks()):
        if t.GetNetname()=='/GND' and not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.F_Cu:
            if t.GetStart() in [pt(v) for v in ((45.7218,23.0053),(46.9147,23.0053),(55.1175,24.7798),(53.5598,24.7798))]:b.RemoveNative(t)
    for ref,new in [('C31',(46.5,22.9)),('C32',(54,24.7))]:fps[ref].SetPosition(pt(new))
    route('/GND',[xy(pad('C31',2).GetPosition()),(45.7218,23.0053)])
    route('/GND',[xy(pad('C32',2).GetPosition()),(55.1175,24.7798)])
    fps['Y1'].SetOrientationDegrees(-37.5);fps['Y1'].SetPosition(pt((50.2,23.23)))
    route('/+3V3_RF',[xy(pad('U2',9).GetPosition()),(50.2,20.55)],.15)
    route('/CC1101_CSN',[xy(pad('U2',7).GetPosition()),(49.2,20.53),(48.35,20.8)],.15)
    route('/CC1101_GDO0',[xy(pad('U2',6).GetPosition()),(48.7,20.05),(47.7,20.25)],.15)
    route('/CC1101_XOSC_Q1',[xy(pad('U2',8).GetPosition()),(49.7,20.55),(48,22.25),xy(pad('Y1',1).GetPosition())],.15)
    route('/CC1101_XOSC_Q1',[xy(pad('Y1',1).GetPosition()),xy(pad('C31',1).GetPosition())])
    route('/CC1101_XOSC_Q2',[xy(pad('U2',10).GetPosition()),(50.7,20.4),(52,21.7),(52,22.7),xy(pad('Y1',3).GetPosition())])
    route('/CC1101_XOSC_Q2',[xy(pad('Y1',3).GetPosition()),xy(pad('C32',1).GetPosition())])
    via('/GND',(50.3,23.3))
    for n in (2,4):route('/GND',[xy(pad('Y1',n).GetPosition()),(50.3,23.3)])
    # Keep digital copper out of the projection of the sensitive Q1 pad,
    # including layers below the ground plane (TI oscillator guidance).
    for t in list(b.GetTracks()):
        if isinstance(t,p.PCB_VIA):continue
        if t.GetNetname()=='/CC1101_CSN' and t.GetLayer()==p.In2_Cu:
            if t.GetStart()==pt((49.05,21.8183)):t.SetStart(pt((48.45,21.8183)))
            if t.GetEnd()==pt((49.05,21.8183)):t.SetEnd(pt((48.45,21.8183)))
        if t.GetNetname()=='/CC1101_GDO2' and t.GetLayer()==p.B_Cu and t.GetStart()==pt((50.4772,25.9425)):
            b.RemoveNative(t)
        if t.GetNetname()=='/RF_OUT0' and t.GetLayer()==p.In2_Cu:
            for old in ((47.5411,24.1781),):
                if t.GetStart()==pt(old):t.SetStart(pt((old[0],24.45)))
                if t.GetEnd()==pt(old):t.SetEnd(pt((old[0],24.45)))
            if t.GetStart()==pt((47.5411,24.45)) and t.GetEnd()==pt((55.3667,24.1781)):b.RemoveNative(t)
    route('/RF_OUT0',[(47.5411,24.45),(52.5,24.45),(52.9,24.1781),(55.3667,24.1781)],.2,p.In2_Cu)
    route('/CC1101_GDO2',[(50.4772,25.9425),(49,24.7253),(46.5,22.2253),(45.8,21.2653)],.15,p.B_Cu)
    b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones())
    p.SaveBoard(str(out),b);shutil.copyfile(source.with_suffix('.kicad_pro'),out.with_suffix('.kicad_pro'))
    print(out)

if __name__=='__main__':main()
