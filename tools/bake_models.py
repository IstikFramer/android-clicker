"""blender -b --python tools/bake_models.py -- [--out DIR]

Original display miniatures. Blender +Y exports as Godot -Z. All meshes
are authored in attachment-local coordinates, with unit object scales.
"""
import argparse
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Vector

TAU = math.tau
ROOT = Path(__file__).resolve().parents[1]
PAL = {"hull": (.27,.34,.39), "porcelain": (.66,.73,.71), "shadow": (.045,.064,.086),
       "copper": (.72,.33,.13), "lamp": (.20,.85,.92), "glass": (.17,.42,.53),
       "rock": (.28,.22,.18), "radiator": (.065,.13,.21)}
MATERIALS = []


def begin(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MATERIALS.clear()
    for key, color in PAL.items():
        mat = bpy.data.materials.new(key)
        mat.diffuse_color = (*color, 1)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (*color,1)
        bsdf.inputs["Metallic"].default_value = .55 if key not in ("glass","rock") else .12
        bsdf.inputs["Roughness"].default_value = .35 if key != "rock" else .85
        if key == "lamp":
            bsdf.inputs["Emission Color"].default_value = (*color,1)
            bsdf.inputs["Emission Strength"].default_value = 2.2
        MATERIALS.append(mat)
    root = empty(name)
    root["author"] = "SPACE DIE project"
    root["provenance"] = "original_procedural"
    root["rights"] = "Original project asset; redistribution terms set by project owner."
    return root


def empty(name, parent=None, pos=(0,0,0)):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.parent, obj.location = parent, pos
    return obj


class Shell:
    def __init__(self):
        self.vertices = []
        self.faces = []
        self.slots = []

    def patch(self, vertices, faces, material):
        off = len(self.vertices)
        self.vertices.extend(vertices)
        self.faces.extend(tuple(i+off for i in face) for face in faces)
        self.slots.extend([list(PAL).index(material)]*len(faces))

    def block(self, xyz, size, material):
        c = Vector(xyz)
        verts = [c+Vector((x*size[0]/2,y*size[1]/2,z*size[2]/2))
                 for z in (-1,1) for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        self.patch(verts,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material)

    def tube(self, start, end, radii, material, n=12):
        a,b=Vector(start),Vector(end)
        axis=(b-a).normalized()
        side=axis.cross(Vector((0,0,1)) if abs(axis.z)<.9 else Vector((1,0,0))).normalized()
        up=axis.cross(side)
        verts=[c+r*(side*math.cos(i*TAU/n)+up*math.sin(i*TAU/n))
               for c,r in zip((a,b),radii) for i in range(n)]
        faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        faces.extend((i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n))
        self.patch(verts,faces,material)

    def ring(self, radius, width, center, material, segments, sides, vertical=False, span=(0,TAU)):
        verts=[]
        for i in range(segments+1):
            angle=span[0]+(span[1]-span[0])*i/segments
            for j in range(sides):
                u=j*TAU/sides
                r=radius+width*math.cos(u)
                x,y,z=r*math.cos(angle),r*math.sin(angle),width*math.sin(u)
                verts.append(Vector(center)+Vector((x,-z,y) if vertical else (x,y,z)))
        faces=[]
        for i in range(segments):
            for j in range(sides):
                a=i*sides+j
                b=i*sides+(j+1)%sides
                faces.append((a,a+sides,b+sides,b))
        if span!=(0,TAU):
            faces.extend([tuple(range(sides)),tuple(reversed(range(segments*sides,(segments+1)*sides)))])
        self.patch(verts,faces,material)

    def finish(self, name, parent):
        mesh=bpy.data.meshes.new(name)
        mesh.from_pydata(self.vertices,[],self.faces)
        mesh.update()
        obj=bpy.data.objects.new(name,mesh)
        bpy.context.collection.objects.link(obj)
        obj.parent=parent
        for mat in MATERIALS:
            mesh.materials.append(mat)
        for face,slot in zip(mesh.polygons,self.slots):
            face.material_index=slot
        return obj


def railgun(high):
    root=begin("Railgun")
    pivot=empty("RecoilPivot",root)
    shell=Shell()
    shell.block((0,-.4,0),(1.45,3.6,1.05),"hull")
    shell.tube((0,-1.9,0),(0,2.8,0),(.5,.24),"shadow",24)
    for side in (-1,1):
        shell.block((side*.59,1.65,0),(.33,5.4,.44),"porcelain")
        shell.block((side*.59,1.8,.24),(.15,4.8,.06),"lamp")
        for i in range(10):
            shell.block((side*1.13,-1.5+i*.27,-.1),(.9,.11,.57),"radiator")
    for i in range(12):
        shell.ring(.58,.077,(0,-1.55+i*.25,0),"copper",40 if high else 22,9 if high else 5,True)
    shell.finish("CarriageAndRails",pivot)
    engine=Shell()
    engine.tube((0,-2.65,0),(0,-1.8,0),(.92,.61),"hull",32)
    for i in range(3):
        engine.ring(.88-i*.07,.065,(0,-2.6+i*.2,0),"lamp",32 if high else 20,7 if high else 4,True)
    engine.finish("WarpEngine",root)
    empty("WarpOrigin",root,(0,-2.7,0))
    empty("CameraAnchor",root,(1.1,-2.4,1.2))
    empty("Muzzle",pivot,(0,4.36,0))


def gungnir():
    root=begin("Gungnir")
    frame=Shell()
    # Independent annular modules and helical struts surround the gas giant.
    angle = TAU/18
    span = (.016, angle-.016)
    for z in (-.27,.27):
        frame.ring(3.8,.12,(0,0,z),"hull",9,6,span=span)
        frame.ring(3.57,.045,(0,0,z),"lamp",9,5,span=span)
    frame.ring(4.01,.12,(0,0,0),"copper",8,7,span=span)
    frame.tube((3.8,0,-.25),(3.8*math.cos(.18),3.8*math.sin(.18),.25),(.10,.10),"porcelain",6)
    segment = frame.finish("Module00",root)
    for i in range(1,18):
        instance = segment.copy()
        instance.name = "Module%02d" % i
        bpy.context.collection.objects.link(instance)
        instance.rotation_euler.z = i*angle
    gate=empty("LaunchGate",root,(3.85,0,.32))
    module=Shell()
    module.block((0,0,0),(.85,.35,.72),"porcelain")
    module.finish("SlidingGate",gate)
    empty("ProjectileAnchor",root,(3.85,0,0))
    empty("OverviewCamera",root,(5,-7,4))
    empty("ExitAnchor",root,(3.85,2,0))


def vera(high):
    root=begin("Vera")
    pivot=empty("RingPivot",root)
    for i in range(4):
        a=i*TAU/4
        part=Shell()
        span=(a+.035,a+TAU/4-.035)
        for radius,z,material,width in [(3.05,.28,"porcelain",.16),(3.05,-.28,"hull",.18),
                                        (2.72,.15,"lamp",.052),(3.4,0,"copper",.10)]:
            part.ring(radius,width,(0,0,z),material,36 if high else 17,10 if high else 6,span=span)
        for j in range(10):
            t=span[0]+(span[1]-span[0])*j/10
            part.tube((3.05*math.cos(t),3.05*math.sin(t),-.27),
                      (3.3*math.cos(t+.10),3.3*math.sin(t+.10),.27),(.063,.063),"shadow",7)
        part.tube((.48*math.cos(a),.48*math.sin(a),0),(3*math.cos(a),3*math.sin(a),0),(.11,.21),"hull")
        part.finish("ArcSection%d"%i,pivot)
    core=empty("CoreAnchor",root)
    unit=Shell()
    unit.tube((0,0,-.61),(0,0,.61),(.42,.42),"lamp",32)
    unit.ring(.60,.12,(0,0,0),"copper",32,8)
    unit.finish("EnergyCore",core)
    empty("BeamOrigin",core,(0,1.05,0))
    empty("CameraAnchor",root,(1.8,-3.4,1.8))


def small(name,seed):
    root=begin(name)
    mesh=Shell()
    if name=="GungnirProjectile":
        mesh.tube((0,-1.6,0),(0,.95,0),(.13,.23),"copper",16)
        mesh.tube((0,.95,0),(0,2,0),(.23,.015),"porcelain",16)
        mesh.ring(.22,.05,(0,.72,0),"lamp",16,6,True)
    elif name.startswith("Rock"):
        rng=random.Random(seed)
        n=11
        rings=7
        verts=[]
        for i in range(rings+1):
            lat=-math.pi/2+math.pi*i/rings
            for j in range(n):
                lon=TAU*j/n
                r=rng.uniform(.78,1.15)
                verts.append((r*math.cos(lat)*math.cos(lon),.75*r*math.cos(lat)*math.sin(lon),.84*r*math.sin(lat)))
        mesh.patch(verts,[(i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j)
                          for i in range(rings) for j in range(n)],"rock")
    else:
        mesh.tube((0,0,0),(0,0,.33),(.7,.68),"hull",18)
        if name=="MarsDomes":
            for r,z,r2,z2 in [(.66,.33,.56,.63),(.56,.63,.35,.83),(.35,.83,.02,.93)]:
                mesh.tube((0,0,z),(0,0,z2),(r,r2),"glass",24)
        else:
            mesh.block((0,0,.55),(.8,.75,.65),"porcelain")
            for x in (-1,1):
                mesh.block((x,0,.42),(1.05,.57,.09),"radiator")
            mesh.tube((0,0,.55),(0,0,1.35),(.05,.025),"lamp",8)
    mesh.finish(name+"Hull",root)


def ring_band():
    root=begin("SaturnRings")
    shell=Shell()
    count=192
    verts=[]
    for i in range(count+1):
        for r in (1.23,2.09):
            verts.append((r*math.cos(i*TAU/count),r*math.sin(i*TAU/count),0))
    shell.patch(verts,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(count)],"porcelain")
    band=shell.finish("Annulus",root)
    uv=band.data.uv_layers.new(name="Radius_Azimuth")
    for loop in band.data.loops:
        idx=loop.vertex_index
        uv.data[loop.index].uv=(float(idx%2),1.0-(idx//2)/count)


args=argparse.ArgumentParser()
args.add_argument("--out",type=Path,default=ROOT/"godot/assets/models")
out=args.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []).out
out.mkdir(parents=True,exist_ok=True)
for name in ["Railgun","RailgunMedium","Gungnir","GungnirProjectile","Vera","VeraMedium",
             "MercuryStation","MarsDomes","SaturnStation","SaturnRings"]+[f"Rock{i:02d}" for i in range(8)]:
    if name.startswith("Railgun"):
        railgun(name=="Railgun")
    elif name.startswith("Vera"):
        vera(name=="Vera")
    elif name=="SaturnRings":
        ring_band()
    elif name=="Gungnir":
        gungnir()
    else:
        small(name,71023+sum(map(ord,name)))
    bpy.ops.export_scene.gltf(filepath=str(out/(name+".glb")),export_format="GLB",
                              export_yup=True,export_extras=True,export_animations=False)
