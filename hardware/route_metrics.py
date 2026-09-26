#!/usr/bin/env python3
"""Extract routed path lengths, assumed DC resistance and oscillator proximity.

Not a field solver, current-capacity rating, or thermal/bench qualification.
Run with KiCad Python. Contact/pad spreading and return resistance are omitted.
"""
import argparse
import heapq
import itertools
import json
import math
from pathlib import Path
import pcbnew as p

ROOT=Path(__file__).resolve().parents[1]
RHO20=1.724e-5  # ohm mm: assumed copper at 20 C
RHO80=RHO20*(1+.00393*60)

def point_segment(q,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=max(0,min(1,((q[0]-a[0])*dx+(q[1]-a[1])*dy)/(dx*dx+dy*dy))) if dx or dy else 0
    z=(a[0]+t*dx,a[1]+t*dy)
    return math.hypot(q[0]-z[0],q[1]-z[1]),t

def segment_rectangle(a,b,hx,hy):
    # Slab intersection, including zero-length segments.
    low,high=0.,1.
    for av,bv,h in ((a[0],b[0],hx),(a[1],b[1],hy)):
        if abs(bv-av)<1e-12:
            if abs(av)>h:low,high=1,0;break
        else:
            u,v=sorted(((-h-av)/(bv-av),(h-av)/(bv-av)))
            low=max(low,u);high=min(high,v)
    if low<=high:return 0.
    distances=[math.hypot(max(abs(q[0])-hx,0),max(abs(q[1])-hy,0)) for q in (a,b)]
    distances += [point_segment(q,a,b)[0] for q in ((-hx,-hy),(-hx,hy),(hx,-hy),(hx,hy))]
    return min(distances)

def copper_resistance(length,width,thickness):
    return RHO80*length/(width*thickness)

def via_resistance(drill,plating=.020,span=1.6):
    return RHO80*span/(math.pi*(drill*plating+plating*plating))

def pos(v):return (round(p.ToMM(v.x),6),round(p.ToMM(v.y),6))
def v2(q):return p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))

class Network:
    def __init__(self,board,net):
        self.g={};self.pads={};self.board=board
        layers=(p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu)
        tracks=[t for t in board.GetTracks() if t.GetNetname()==net]
        def node(q,layer):return ('copper',layer,*q)
        nodes=set()
        for t in tracks:
            if isinstance(t,p.PCB_VIA):nodes.update(node(pos(t.GetPosition()),l) for l in layers)
            else:nodes.update((node(pos(t.GetStart()),t.GetLayer()),node(pos(t.GetEnd()),t.GetLayer())))
        for t in tracks:
            if isinstance(t,p.PCB_VIA):continue
            a,z=pos(t.GetStart()),pos(t.GetEnd());layer=t.GetLayer()
            w=p.ToMM(t.GetWidth());length=p.ToMM(t.GetLength())
            # Same-net T junctions may terminate inside, not on, a centerline.
            contacts=sorted((point_segment(n[2:],a,z)[1],n) for n in nodes if n[1]==layer
                            and point_segment(n[2:],a,z)[0]<=w/2+1e-6)
            thickness=(.035 if layer in (p.F_Cu,p.B_Cu) else .0152)*.8
            for (s,u),(e,v) in zip(contacts,contacts[1:]):
                d=(e-s)*length
                self.edge(u,v,copper_resistance(d,w,thickness),
                          {'kind':'trace','length_mm':d,'width_mm':w,'layer':board.GetLayerName(layer)})
        for t in tracks:
            if not isinstance(t,p.PCB_VIA):continue
            q=pos(t.GetPosition());diameter=p.ToMM(t.GetWidth(p.F_Cu))
            for layer in layers:
                center=node(q,layer)
                for n in nodes:
                    if n[1]==layer and math.dist(n[2:],q)<=diameter/2+1e-6:self.edge(center,n,0,{'kind':'contact'})
            for l1,l2 in itertools.combinations(layers,2):
                self.edge(node(q,l1),node(q,l2),via_resistance(p.ToMM(t.GetDrillValue())),{'kind':'via'})
        for f in board.GetFootprints():
            for pad in f.Pads():
                if pad.GetNetname()!=net or not pad.GetNumber():continue
                key=f.GetReference()+'.'+pad.GetNumber();anchor=('pad',key)
                self.pads[key]=anchor
                for n in nodes:
                    inside=pad.HitTest(v2(n[2:]))
                    if net.startswith('/CC1101_XOSC'):
                        # Clock lengths use actual pin-center to crystal-center
                        # routing, not a shortcut through the pad copper area.
                        inside=math.dist(n[2:],pos(pad.GetPosition()))<1e-5
                    if pad.IsOnLayer(n[1]) and inside:self.edge(anchor,n,0,{'kind':'pad_contact'})
    def edge(self,u,v,r,info):
        self.g.setdefault(u,[]).append((v,r,info));self.g.setdefault(v,[]).append((u,r,info))
    def path(self,start,end):
        source,target=self.pads[start],self.pads[end];counter=itertools.count()
        queue=[(0,next(counter),source,[])];best={source:0}
        while queue:
            d,_,u,path=heapq.heappop(queue)
            if d!=best[u]:continue
            if u==target:return d,path
            for v,r,info in self.g.get(u,[]):
                if d+r<best.get(v,float('inf')):
                    best[v]=d+r;heapq.heappush(queue,(d+r,next(counter),v,path+[info]))
        raise RuntimeError('No modeled copper path '+start+' -> '+end)

def oscillator_clearances(board,classes):
    f=next(f for f in board.GetFootprints() if f.GetReference()=='Y1')
    sensitive=next(q for q in f.Pads() if q.GetNumber()=='1')
    cx,cy=pos(sensitive.GetPosition())
    theta=math.radians(sensitive.GetOrientationDegrees());c,s=math.cos(theta),math.sin(theta)
    def local(q):x,y=q[0]-cx,q[1]-cy;return x*c-y*s,x*s+y*c
    hx,hy=p.ToMM(sensitive.GetSize().x)/2,p.ToMM(sensitive.GetSize().y)/2
    near=[]
    for t in board.GetTracks():
        net=t.GetNetname();cls=classes.get(net,'Default')
        if net=='/GND' or (cls not in ('Default','USB') and net!='/BUCK_SW'):continue
        a,z=pos(t.GetStart()),pos(t.GetEnd())
        width=t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth()
        clearance=segment_rectangle(local(a),local(z),hx,hy)-p.ToMM(width)/2
        if clearance<1:
            near.append({'net':net,'layer':board.GetLayerName(t.GetLayer()),'clearance_mm':round(clearance,4),
                         'start_mm':a,'end_mm':z,'via':isinstance(t,p.PCB_VIA)})
    return sorted(near,key=lambda e:e['clearance_mm'])

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pcb',type=Path,default=ROOT/'hardware/A3-routing-candidate.kicad_pcb')
    ap.add_argument('--output',type=Path,default=ROOT/'reports/route-margins-A3.json')
    args=ap.parse_args();b=p.LoadBoard(str(args.pcb));fps={f.GetReference():f for f in b.GetFootprints()}
    def pad(key):r,n=key.split('.');return next(q for q in fps[r].Pads() if q.GetNumber()==n)
    nets={};paths=[]
    for start,end,current in [('J1.A4','F1.1',.5),('J1.A9','F1.1',.5),('F1.2','U7.1',.5),
        ('F1.2','U5.7',.02),('U7.6','U6.3',.5),('L1.2','U1.2',.5),('L1.2','FB1.1',.1),
        ('FB1.2','U2.4',.1),('FB1.2','U2.9',.1),('FB1.2','U3.16',.1),('FB1.2','U4.16',.1),
        ('U5.6','U5.5',.02),('U2.8','Y1.1',0),('U2.10','Y1.3',0)]:
        net=pad(start).GetNetname();assert net==pad(end).GetNetname(),(start,end)
        if net not in nets:nets[net]=Network(b,net)
        resistance,edges=nets[net].path(start,end)
        paths.append({'from':start,'to':end,'net':net,'assumed_current_A':current,
            'modeled_R_ohm_at_80C':round(resistance,5),'modeled_drop_mV':round(1000*current*resistance,3),
            'copper_path_length_mm':round(sum(e.get('length_mm',0) for e in edges),3),
            'via_transitions':sum(e['kind']=='via' for e in edges),
            'minimum_trace_width_mm':round(min(e['width_mm'] for e in edges if e['kind']=='trace'),3)})
    settings=json.loads(args.pcb.with_suffix('.kicad_pro').read_text())
    classes={n['pattern']:n['netclass'] for n in settings['net_settings']['netclass_patterns']}
    near=oscillator_clearances(b,classes)
    checks=[{'check':'Digital copper clears projected Q1 pad by >=0.20 mm on every layer',
             'pass':all(e['clearance_mm']>=.2 for e in near)}]
    for path in paths:
        if path['to'].startswith('Y1.'):
            checks.append({'check':path['from']+' to '+path['to']+' routed length <5 mm, no vias',
                           'pass':path['copper_path_length_mm']<5 and path['via_transitions']==0})
    mainrail=next(q for q in paths if q['to']=='U1.2')
    checks.append({'check':'Main ESP32 path >=0.8 mm and modeled drop <25 mV at 0.5 A',
                   'pass':mainrail['minimum_trace_width_mm']>=.8 and mainrail['modeled_drop_mV']<25})
    checks.append({'check':'Each USB contact-to-fuse copper path modeled drop <50 mV at 0.5 A',
                   'pass':all(q['modeled_drop_mV']<50 for q in paths if q['to']=='F1.1')})
    checks.append({'check':'RF branch copper paths modeled drop <25 mV at 0.1 A (bead excluded)',
                   'pass':all(q['modeled_drop_mV']<25 for q in paths if q['net']=='/+3V3_RF')})
    report={'status':'PASS_SCREEN_ONLY' if all(c['pass'] for c in checks) else 'FAIL_SCREEN',
        'board':args.pcb.name,'paths':paths,'checks':checks,
        'screen_limits':'Project engineering screens, not quoted manufacturer maxima. Individual load cases are independent, not an approved simultaneous-load budget.',
        'assumptions':{'copper_temperature_C':80,'copper_resistivity_20C_ohm_mm':RHO20,
            'temperature_coefficient_per_C':.00393,'outer_copper_mm':.035*.8,'inner_copper_mm':.0152*.8,
            'via_plating_mm':.020,'via_span_mm':1.6,
            'limitations':'Least-resistance single copper path, parallel paths ignored. Pad/contact spreading, components, cable and ground-return resistance omitted. All layer transitions charged full via-barrel resistance. Clock lengths use pin-center/crystal-center contacts. Not an ampacity/thermal rating or tolerance guarantee.'},
        'oscillator_Q1_pad_projected_digital_clearances_under_1mm':near,
        'digital_copper_projected_under_Q1_pad':[e for e in near if e['clearance_mm']<0],
        'oscillator_screen_scope':'All copper layers projected onto full rectangular pad envelope; rounded corners ignored conservatively. Ground plane shielding does not waive this screen.',
        'oscillator_guidance_source':'https://www.ti.com/lit/ds/symlink/cc1101.pdf'}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(report['status']+': '+str(sum(c['pass'] for c in checks))+'/'+str(len(checks))+' route screens')
    for path in paths:print(path['from']+' -> '+path['to']+': '+str(path['copper_path_length_mm'])+' mm, '+str(path['modeled_drop_mV'])+' mV modeled')

if __name__=='__main__':main()
