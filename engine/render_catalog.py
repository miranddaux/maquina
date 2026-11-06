"""Render catalog thumbnails from actual Blender models, not stock illustrations."""
import json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'engine'))
from characters import build_character
from environment import configure
OUT=ROOT/'web/model-thumbs';OUT.mkdir(parents=True,exist_ok=True)
for preset in ['explorer','builder','scientist']:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='MATERIAL';scene.display.shading.background_type='WORLD';configure(scene,{'environment':'day'})
 build_character({'character':{'preset':preset}},pose='wave')
 bpy.ops.object.camera_add(location=(3,-8,3.0));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2.65;cam.rotation_euler=(Vector((0,0,1.05))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
 scene.render.resolution_x=384;scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/(preset+'.png'));bpy.ops.render.render(write_still=True)
for name,source in [('house_assembly','scene_house.py'),('room_airflow','scene_room.py'),('earth_rotation','scene.py')]:
 import tempfile
 with tempfile.TemporaryDirectory(dir=OUT) as temp:
  cfg=Path(temp)/'config.json';cfg.write_text(json.dumps({'width':384,'height':640,'fps':1,'duration':6,'branding':{'character':{'shirt':'#E8BE45'},'visual_style':'rounded','environment':'day'}}))
  code=(ROOT/'engine'/source).read_text().replace('bpy.ops.render.render(animation=True)','')
  namespace={'__file__':str(ROOT/'engine'/source),'__name__':'__main__'}
  sys.argv=['thumbnail','--',str(cfg),temp];exec(compile(code,str(ROOT/'engine'/source),'exec'),namespace)
  bpy.context.scene.frame_set(6);bpy.context.scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
