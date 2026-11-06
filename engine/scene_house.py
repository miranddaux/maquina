"""Original house assembly illustration; not an engineering specification."""
import json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
config=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())
out=Path(sys.argv[sys.argv.index('--')+2])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=config['width'];scene.render.resolution_y=config['height'];scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl';scene.display.shading.color_type='MATERIAL'
scene.display.shading.background_type='WORLD';scene.world.color=(.78,.88,.91)
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.render_aa='8'
scene.view_settings.view_transform='Standard'
from environment import configure
palette=configure(scene,config.get('branding',{}))
fps=config['fps'];frames=round(config['duration']*fps)

def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
cream=mat('Concreto quente',(.83,.82,.70));green=mat('Terreno menta',palette['ground']);white=mat('Paredes marfim',(.96,.93,.82));orange=mat('Cor de acento',(.98,.45,.15));navy=mat('Estrutura azul',(.10,.22,.32));skin=mat('Pele',(.72,.43,.26));glass=mat('Janelas azuis',(.25,.67,.85));black=mat('Olhos',(.025,.035,.04));leaf=mat('Arvores',(.19,.46,.33))

def box(name,loc,scale,material,bevel=.05):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
 if bevel:
  mod=o.modifiers.new('Bordas suaves','BEVEL');mod.width=bevel;mod.segments=2;o.modifiers.new('Normais','WEIGHTED_NORMAL')
 return o

def sphere(name,loc,radius,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=radius,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o

def enter(obj,second):
 finish=obj.location.copy();scale=obj.scale.copy();start=max(1,round(second*fps));end=min(frames,start+round(.45*fps))
 obj.location.z+=2.5;obj.scale=(0,0,0);obj.keyframe_insert(data_path='location',frame=start);obj.keyframe_insert(data_path='scale',frame=start)
 obj.location=finish;obj.scale=scale;obj.keyframe_insert(data_path='location',frame=end);obj.keyframe_insert(data_path='scale',frame=end)
 if obj.animation_data:
  for fc in obj.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation='BEZIER'

box('Ilha de terreno',(0,0,-.18),(6.8,5.8,.32),green,.18)
slab=box('Base ilustrativa',(0,0,.08),(3.4,2.8,.18),cream);enter(slab,.4)
# Assembly timing is proportional to episode duration, keeping distinct holds.
for x,y,w,d in [(-1.4,0,.18,2.6),(1.4,0,.18,2.6),(0,1.2,2.8,.18)]:
 o=box('Parede',(x,y,.91),(w,d,1.6),white);enter(o,config['duration']*.22)
for x in [-.95,.95]:
 o=box('Parede frontal',(x,-1.2,.91),(.9,.18,1.6),white);enter(o,config['duration']*.32)
for x in [-.95,.95]:
 o=box('Janela',(x,-1.31,1.05),(.52,.035,.55),glass,.03);enter(o,config['duration']*.44)
 o=box('Verga',(x,-1.32,1.37),(.65,.05,.08),navy,.02);enter(o,config['duration']*.44)
o=box('Porta',(0,-1.32,.72),(.62,.07,1.28),orange,.03);enter(o,config['duration']*.52)
# Simple gable roof mesh with clear silhouette.
verts=[(-1.7,-1.55,1.82),(1.7,-1.55,1.82),(0,-1.55,2.65),(-1.7,1.55,1.82),(1.7,1.55,1.82),(0,1.55,2.65)]
mesh=bpy.data.meshes.new('Telhado');mesh.from_pydata(verts,[],[(0,1,2),(3,5,4),(0,3,4,1),(0,2,5,3),(1,4,5,2)]);mesh.update()
o=bpy.data.objects.new('Telhado',mesh);bpy.context.collection.objects.link(o);o.data.materials.append(navy);enter(o,config['duration']*.65)
# Shared original character respects the channel settings.
from characters import build_character
build_character(config.get('branding',{}),location=(-2.25,-1.4,0),scale=.68,pose='wave')
for x,y in [(2.6,1.9),(-2.5,2.1)]:
 box('Tronco arvore',(x,y,.35),(.15,.15,.7),cream,.02)
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.58,location=(x,y,.98));bpy.context.object.data.materials.append(leaf)
for x in [-.9,-.3,.3,.9]:box('Caminho',(x,-2.1,-.005),(.5,.45,.04),cream,.04)
bpy.ops.object.camera_add(location=(6,-10,7))
cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=12.2
focus=Vector((0,0,1.0));cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
# Holds opening and close; one deliberate push between 25% and 65%.
for frac,scale in [(0,12.2),(.25,12.2),(.65,11.5),(1,11.5)]:
 cam.data.ortho_scale=scale;cam.data.keyframe_insert(data_path='ortho_scale',frame=max(1,round(frac*frames)))
scene.render.fps=fps;scene.frame_start=1;scene.frame_end=frames;scene.render.filepath=str(out/'frame_')
bpy.ops.render.render(animation=True)
