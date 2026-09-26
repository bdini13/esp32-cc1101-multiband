#!/usr/bin/env python3
"""Reproducible A3 critical-route work-in-progress, before digital autorouting.

Never releases manufacturing files. Native DRC and bench RF validation required.
Geometry is explicit; every pad-to-pad connection asserts schematic net identity.
"""
from pathlib import Path
import shutil
import pcbnew as p

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'esp32-cc1101-multiband.kicad_pcb'
OUT = HERE / 'A3-critical-routes.kicad_pcb'

def main():
    b = p.LoadBoard(str(SOURCE))
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    def pad(name):
        ref, number = name.split('.')
        return next(q for q in fps[ref].Pads() if q.GetNumber() == number)
    def xy(q):
        v = q.GetPosition()
        return p.ToMM(v.x), p.ToMM(v.y)
    def point(v): return p.VECTOR2I(p.FromMM(v[0]), p.FromMM(v[1]))
    def trace(net, points, width=.2, layer=p.F_Cu):
        n = b.FindNet(net)
        assert n, net
        for start, end in zip(points, points[1:]):
            if start == end: continue
            t = p.PCB_TRACK(b)
            t.SetStart(point(start)); t.SetEnd(point(end))
            t.SetWidth(p.FromMM(width)); t.SetLayer(layer); t.SetNet(n)
            t.SetLocked(True)
            b.Add(t)
    def link(a, z, via=(), width=.2, layer=p.F_Cu):
        x, y = pad(a), pad(z)
        assert x.GetNetname() == y.GetNetname(), (a,z,x.GetNetname(),y.GetNetname())
        trace(x.GetNetname(), [xy(x), *via, xy(y)], width, layer)
    def gvia(a, pos):
        q=pad(a); assert q.GetNetname() == '/GND', a
        v = p.PCB_VIA(b); v.SetPosition(point(pos)); v.SetWidth(p.FromMM(.6))
        v.SetDrill(p.FromMM(.3)); v.SetViaType(p.VIATYPE_THROUGH)
        v.SetLayerPair(p.F_Cu,p.B_Cu); v.SetNet(b.FindNet('/GND')); v.SetLocked(True)
        b.Add(v); trace('/GND',[xy(q),pos],.3)
    def via(net, pos, diameter=.6, drill=.3):
        v=p.PCB_VIA(b);v.SetPosition(point(pos));v.SetWidth(p.FromMM(diameter));v.SetDrill(p.FromMM(drill))
        v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu)
        v.SetNet(b.FindNet(net));v.SetLocked(True);b.Add(v)

    # Buck switching loop and local output storage. Feedback runs above circuit.
    link('U6.3','C1.1',width=.65)
    link('U6.2','U6.3',width=.4)
    link('U6.5','L1.1',width=.65)
    link('U6.6','C14.1',width=.25)
    link('C14.2','U6.5',[(16.8,2.72),(16.8,5.5)],.3)
    link('L1.2','C2.1',[(20.385,8.2)],.8)
    link('L1.2','C13.1',[(21.5,5.5),(23,7)],.8)
    link('U6.1','L1.2',[(12.9,4.55),(12.9,3.4),(14.4,3.4),
                           (14.4,.8),(20.5,.8),(21.1,1.4),(21.1,2.8),(20.385,3.515)],.2)
    link('U7.5','U7.6',width=.4)
    link('U7.6','C1.1',[(11.1,8.387),(11.1,7.075)],.5)
    gvia('U6.4',(15.6,7.4)); gvia('C1.2',(7.8,6.5))
    gvia('C2.2',(16.25,9.5)); gvia('C13.2',(24,9.975))
    # Main ESP32 rail has a deliberately wide path; pin-necked auto-routes
    # must not become the only path carrying the module's pulse current.
    for pos in [(24.2,5.825),(27.5,2.31)]: via('/+3V3',pos)
    trace('/+3V3',[xy(pad('C13.1')),(24.2,5.825)],.8)
    trace('/+3V3',[(24.2,5.825),(25,5.025),(25,3.11),(25.8,2.31),(27.5,2.31)],.8,p.B_Cu)
    trace('/+3V3',[(27.5,2.31),xy(pad('U1.2'))],.8)
    # Raw VBUS uses In2 to avoid the short USB contact crossover on B.Cu.
    for pos in [(5.3,10.9),(6.2,16.25),(6.2,19.75)]: via('/VBUS_IN',pos)
    trace('/VBUS_IN',[xy(pad('J1.A4')),(6.9,15.55),(6.2,16.25)],.3)
    trace('/VBUS_IN',[xy(pad('J1.A9')),(6.9,20.45),(6.2,19.75)],.3)
    trace('/VBUS_IN',[xy(pad('F1.1')),(5.3,10.9)],.6)
    trace('/VBUS_IN',[(5.3,10.9),(4.6,11.6),(4.6,19.75),(6.2,19.75)],.6,p.In2_Cu)
    trace('/VBUS_IN',[(4.6,16.25),(6.2,16.25)],.6,p.In2_Cu)
    for pos in [(5.3,8.1),(7.4,8)]: via('/VBUS_PROTECTED',pos)
    trace('/VBUS_PROTECTED',[xy(pad('F1.2')),(5.3,8.1)],.6)
    trace('/VBUS_PROTECTED',[(5.3,8.1),(7.4,8)],.6,p.B_Cu)
    trace('/VBUS_PROTECTED',[(7.4,8),xy(pad('U7.1'))],.6)
    link('D2.1','U7.1',[(7.2,9.35),(7.7,8.85)],.3)
    gvia('D2.2',(6.3,6.9)); gvia('U7.2',(9.4,9.8))

    # Differential RF pair: keep short; these are matching interconnects,
    # not asserted to be 50-ohm microstrip.
    link('U2.13','C42.1',[(52.5,18)],.2)
    link('C42.1','C40.1',[(53.52,17.2)],.2)
    link('U2.12','C42.2',[(52.5,18.5)],.2)
    link('C42.2','C41.1',[(53.52,19.3)],.2)
    link('C40.2','B1.3',[(55.74,17.76)],.2)
    link('C41.2','B1.4',[(55.74,18.74)],.2)
    link('B1.1','L40.1',width=.3)
    link('L40.2','L41.1',width=.35)
    link('C43.1','L40.2',[(59.9,17.975)],.2)
    link('L41.2','U3.22',[(61.8,17.76),(62.29,18.25)],.2)
    link('C44.1','L41.2',width=.2)

    # Filter branches: .20 mm QFN necks; .35 mm microstrip proposal.
    trace('/RF_315_IN',[xy(pad('U3.14')),(65.55,15.45)],.2)
    trace('/RF_315_IN',[(65.55,15.45),(65.55,14.765),xy(pad('L42.1'))],.35)
    link('L42.2','L43.1',width=.35)
    link('L43.2','L44.1',width=.35)
    link('L45.1','L42.2',[(68.8,13.515)],.3)
    link('L45.2','C45.1',width=.3)
    link('C46.1','L44.1',[(71.1,12.785)],.2)
    trace('/RF_315_OUT',[xy(pad('L44.2')),(75.3,13),(75.3,16.4)],.35)
    trace('/RF_315_OUT',[(75.3,16.4),(75.45,16.55),(75.45,17.25),xy(pad('U4.8'))],.2)
    link('U3.11','L46.1',width=.2)
    link('L46.2','L47.1',width=.35)
    link('L47.2','L48.1',width=.35)
    link('L48.2','L49.1',width=.35)
    for cap, component in [('C47','L46'),('C48','L47'),('C49','L48')]:
        x,y=xy(pad(cap+'.1'))
        link(cap+'.1',component+'.2',[(x,17.55)],.3)
    link('L49.2','U4.11',[(74.85,17.415),(74.85,18.5),(75.1,18.75)],.2)
    trace('/RF_868_915_IN',[xy(pad('U3.8')),(67.4,18.75)],.2)
    trace('/RF_868_915_IN',[(67.4,18.75),(67.7,19.05),(67.7,21),(67.015,21.685),xy(pad('L50.1'))],.35)
    link('L50.2','L51.1',width=.35)
    link('C50.1','L50.2',[(68.3,23.315)],.3)
    trace('/RF868_B',[xy(pad('L51.2')),(77.25,23),(77.25,20.5)],.35)
    trace('/RF868_B',[(77.25,20.5),xy(pad('U4.14'))],.2)
    link('C51.1','L51.2',[(71,23.515)],.3)
    link('U3.5','R60.1',[(65.55,20.4),(64.65,21.3)],.2)
    link('U4.5','R61.1',[(77.25,15.24)],.2)
    trace('/RF_COMBINED',[xy(pad('U4.22')),(80.6,17.75)],.2)
    trace('/RF_COMBINED',[(80.6,17.75),(80.7,17.65),(80.7,12.3),(82,11),xy(pad('L52.1'))],.35)
    link('C52.1','L52.1',[(81.5,10.5),(82,11)],.3)
    link('L52.2','R41.1',width=.35)
    link('R41.2','J2.1',[(85.7,11.19)],.35)
    link('C53.1','R41.1',[(84,10.51)],.3)
    link('C54.1','R41.2',[(86.5,10.01)],.3)
    link('D5.1','R41.2',[(86.01,11.5)],.3)

    # Ground each RF-switch perimeter land into the exposed ground paddle.
    for ref in ('U3','U4'):
        for q in fps[ref].Pads():
            if q.GetNetname() == '/GND' and q.GetNumber() != '25':
                cx,cy=xy(pad(ref+'.25')); x,y=xy(q)
                corner=(cx,y) if abs(x-cx)>abs(y-cy) else (x,cy)
                link(ref+'.25',ref+'.'+q.GetNumber(),[corner],.2)
    gvia('U3.1',(63.55,20.75)); gvia('U3.13',(66.4,15.3))
    gvia('U4.1',(79.25,15.25)); gvia('U4.13',(75.9,20.6))
    gvia('B1.2',(57,16.8))
    gvia('C46.2',(71.1,9.72))
    gvia('C45.2',(70.5,13.85))
    for ref in ('C52','C53','C54'):
        x,y=xy(pad(ref+'.2')); gvia(ref+'.2',(x,y-.8))
    for ref in ('C43','C44','C47','C48','C49','C50','C51'):
        x,y=xy(pad(ref+'.2')); gvia(ref+'.2',(x,y+.8))

    # Crystal and bias bypass stay on top, without vias or digital crossovers.
    link('U2.8','Y1.1',[(49.7,22.05)],.2)
    link('U2.10','Y1.3',[(50.7,20.35),(52.1,20.35),(52.1,24.35)],.2)
    link('Y1.1','C31.1',[(48.3,22.05),(47.98,22.37)],.2)
    link('Y1.3','C32.1',width=.2)
    gvia('Y1.4',(51.1,21.0))
    link('U2.17','R30.1',[(50.2,15.11)],.2)
    link('U2.5','C30.1',[(47.25,19),(46.48,19.77)],.2)
    # Pin 9 is between the crystal pins. A short supply via avoids crossing
    # either oscillator trace. The local capacitor returns through L2 ground.
    for pos in [(50.27,20.95),(47.18,20.8)]:
        v=p.PCB_VIA(b);v.SetPosition(point(pos));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.2))
        v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu)
        v.SetNet(b.FindNet('/+3V3_RF'));v.SetLocked(True);b.Add(v)
    trace('/+3V3_RF',[xy(pad('U2.9')),(50.2,20.4),(50.27,20.47),(50.27,20.95)],.15)
    trace('/+3V3_RF',[(50.27,20.95),(50.27,22),(47.18,22),(47.18,20.8)],.3,p.B_Cu)
    trace('/+3V3_RF',[(47.18,20.8),xy(pad('C22.1'))],.3)
    for pin, cap, path in [(4,'C21',[]),
                           (11,'C23',[(52.25,19),(52.92,19.67)]),
                           (14,'C24',[(52.15,17.5),(52.72,16.93)]),
                           (15,'C25',[(51.3,16.713)]),(18,'C26',[(49.7,15.3),(48.92,15.3)])]:
        link('U2.'+str(pin),cap+'.1',path,.2)

    # Pre-escape digital pins before the surrounding oscillator/power routes.
    for pin, net, pos, path in [
        (7,'/CC1101_CSN',(49.05,20.85),[(49.2,20.7)]),
        (6,'/CC1101_GDO0',(47.9,20.45),[(48.7,20.45)]),
        (3,'/CC1101_GDO2',(45.8,18),[]),
        (2,'/SPI_MISO',(46.2,17.1),[(46.6,17.5)]),
    ]:
        via(net,pos,.5,.2)
        trace(net,[xy(pad('U2.'+str(pin))),*path,pos],.15)

    # USB full-speed: short paired section, no data routing through ESD body.
    # Mirrored receptacle D- contacts require a short bottom-layer crossover.
    link('D1.6','U5.3',[(13.25,15.05),(13.25,17.5),(12.9,17.85),(12.9,19.75)],.3)
    link('D1.4','U5.4',[(12.4,17.3),(12.4,20.25)],.3)
    link('J1.A6','J1.B6',[(6.65,17.75),(6.65,18.75)],.2)
    link('J1.A6','D1.1',[(8.4,17.75),(8.85,17.3),(8.85,15.7),(9.5,15.05)],.2)
    link('J1.A7','D1.3',[(8.45,18.25),(9.75,16.95)],.2)
    for pos in [(6.1,17.25),(8.7,18.25)]: via('/USB_DM_CONN',pos,.5,.2)
    trace('/USB_DM_CONN',[xy(pad('J1.B7')),(6.1,17.25)],.15)
    trace('/USB_DM_CONN',[xy(pad('J1.A7')),(8.7,18.25)],.15)
    trace('/USB_DM_CONN',[(6.1,17.25),(6.1,18.25),(8.7,18.25)],.2,p.B_Cu)
    gvia('D1.2',(10.9,16.0))
    gvia('U1.1',(27.5,1.04))
    gvia('C61.2',(78.25,24.1))
    gvia('R61.2',(79.65,14.2))
    gvia('C4.2',(11.2,20.45))
    link('U5.2','U5.25',[(16,19.25)],.2)
    via('/RF_OUT0',(78.75,20.7),.5,.2)
    trace('/RF_OUT0',[xy(pad('U4.17')),(78.75,20.7)],.15)
    link('U4.16','C61.1',[(78.25,20.35),(78.1,20.5),(78.1,21.6),(78.25,21.75)],.2)
    gvia('U4.20',(80.9,18.7))
    for pos in [(3.7,17.25),(9,19.2)]: via('/GND',pos)

    b.BuildConnectivity()
    assert p.ZONE_FILLER(b).Fill(b.Zones())
    p.SaveBoard(str(OUT),b)
    shutil.copyfile(SOURCE.with_suffix('.kicad_pro'),OUT.with_suffix('.kicad_pro'))
    print(OUT)

if __name__ == '__main__': main()
