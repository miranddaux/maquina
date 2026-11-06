"""Original staged room/airflow illustration, using shared channel character and palette."""
import json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from characters import build_character,material as color_material
from environment import configure
args=sys.argv[sys.argv.index('--')+1:]
config=json.loads(Path(args[0]).read_text());out=Path(args[1])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=config['width'];scene.render.resolution_y=config['height'];scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.display.shading.color_type='MATERIAL';scene.display.shading.background_type='WORLD'
palette=configure(scene,config.get('branding',{}));fps=config['fps'];frames=round(config['duration']*fps)

def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
floor=mat('Piso quente',palette['ground']);wall=mat('Parede neutra',palette['wall']);blue=color_material('Sofa azul','#285878');wood=color_material('Madeira','#B78653');white=color_material('Branco quente','#F5EEDF');metal=color_material('Ventilador','#4E6878');cyan=color_material('Fluxo do ar','#39B9D2');green=color_material('Vegetacao','#4E8B68');sky=mat('Ceu',palette['sky']);black=color_material('Ponteiros','#29334B')

def box(name,loc,size,material,bevel=.04):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
 if bevel:
  mod=o.modifiers.new('Bordas','BEVEL');mod.width=bevel;mod.segments=3;o.modifiers.new('Normais','WEIGHTED_NORMAL')
 return o

def cyl(name,loc,radius,depth,material,rotation=(0,0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=radius,depth=depth,location=loc,rotation=rotation);o=bpy.context.object;o.name=name;o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o
box('Piso',(0,0,-.13),(5.4,4.5,.22),floor)
# Open-front stage; window is built from bars, not an opaque slab.
box('Parede esquerda',(-2.65,.7,1.5),(.14,3.1,3.1),wall)
box('Parede fundo',(0,2.15,1.5),(5.4,.14,3.1),wall)
box('Vista janela',(-1.35,2.055,1.95),(1.7,.05,1.65),sky,.01)
for x,z,w,h in [(-1.35,1.10,1.86,.12),(-1.35,2.80,1.86,.12),(-2.21,1.95,.12,1.65),(-.49,1.95,.12,1.65),(-1.35,1.95,.07,1.65)]:box('Janela',(x,1.99,z),(w,.12,h),white,.02)
# Stylized tree visible through the glass and a warm wall clock.
box('Arvore tronco',(-1.8,2.01,1.6),(.09,.025,.65),wood,.01)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.38,location=(-1.8,1.98,2.1));bpy.context.object.data.materials.append(green)
cyl('Relogio',(1.15,2.02,2.45),.30,.05,white,(math.pi/2,0,0))
box('Ponteiro1',(1.12,1.976,2.52),(.035,.02,.17),black,.007);box('Ponteiro2',(1.22,1.974,2.45),(.18,.02,.035),black,.007)
box('Sofa assento',(-1.05,.45,.43),(1.5,1.25,.32),blue,.15)
box('Sofa encosto',(-1.05,.99,.96),(1.5,.26,1.02),blue,.14)
for x in [-1.75,-.35]:box('Braco sofa',(x,.45,.73),(.22,1.25,.66),blue,.10)
for x in [-1.6,-.5]:
 for y in [0,.85]:box('Pe sofa',(x,y,.15),(.10,.10,.24),wood,.025)
character=build_character(config.get('branding',{}),location=(-1.05,.40,-.12),scale=.95,pose='sit')
# Fan pieces are parented for a visible arrival, rotor turns independently.
fan=bpy.data.objects.new('Ventilador completo',None);bpy.context.collection.objects.link(fan);parts=[]
parts.append(cyl('Base',(1.35,-.20,.13),.38,.12,metal))
parts.append(cyl('Haste',(1.35,-.20,.65),.045,1.05,metal))
# Fan faces left along -X; rotor lies in the YZ plane.
center=Vector((1.32,-.20,1.30))
rotor=bpy.data.objects.new('Rotor',None);bpy.context.collection.objects.link(rotor);rotor.location=center;rotor.parent=fan
for i in range(3):
 angle=i*math.tau/3
 loc=center+Vector((0,math.cos(angle)*.21,math.sin(angle)*.21))
 blade=box('Pa do ventilador',loc,(.055,.19,.48),metal,.08)
 blade.rotation_euler.x=-angle;blade.parent=rotor;blade.matrix_parent_inverse=rotor.matrix_world.inverted();parts.append(blade)
for r in [.18,.32,.48]:
 bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=6,major_radius=r,minor_radius=.009,location=center,rotation=(0,math.pi/2,0));o=bpy.context.object;o.data.materials.append(white);parts.append(o)
for o in parts:
 if o.parent is None:o.parent=fan
fan.location=(0,0,3.5);fan.keyframe_insert(data_path='location',frame=1);fan.keyframe_insert(data_path='location',frame=round(frames*.20))
fan.location=(0,0,0);fan.keyframe_insert(data_path='location',frame=round(frames*.32))
rotor.rotation_euler.x=0;rotor.keyframe_insert(data_path='rotation_euler',frame=1);rotor.rotation_euler.x=math.tau*18;rotor.keyframe_insert(data_path='rotation_euler',frame=frames)
# Air symbols repeat from fan to character; symbolic flow is not a CFD simulation.
for i in range(9):
 y=-.2+(i%3-.9)*.16;z=1.10+(i//3)*.22
 bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=.045,radius2=0,depth=.18,location=(.9,y,z),rotation=(0,-math.pi/2,0));o=bpy.context.object;o.name='Seta de fluxo';o.data.materials.append(cyan)
 start=max(1,round(frames*.34)+i*2);stop=min(frames,start+round(fps*.7))
 o.scale=(0,0,0);o.keyframe_insert(data_path='scale',frame=max(1,start-1));o.scale=(1,1,1);o.keyframe_insert(data_path='scale',frame=start)
 o.location.x=.9;o.keyframe_insert(data_path='location',frame=start);o.location.x=-.65;o.keyframe_insert(data_path='location',frame=stop)
 if o.animation_data:
  for fc in o.animation_data.action.fcurves:
   if fc.data_path=='location':fc.modifiers.new('CYCLES')
# A small original rug anchors the character; no copied reference artwork.
box('Tapete',(0,-.25,.012),(3.8,2.8,.028),white,.08)
bpy.ops.object.camera_add(location=(6.0,-9.0,5.7));cam=bpy.context.object;cam.data.type='ORTHO'
focus=Vector((-.15,.45,1.35));cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
for frac,scale in [(0,10.0),(.25,10.0),(.65,9.3),(1,9.3)]:cam.data.ortho_scale=scale;cam.data.keyframe_insert(data_path='ortho_scale',frame=max(1,round(frac*frames)))
scene.render.fps=fps;scene.frame_start=1;scene.frame_end=frames;scene.render.filepath=str(out/'frame_')
bpy.ops.render.render(animation=True)
