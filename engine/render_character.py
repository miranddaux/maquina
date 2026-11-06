"""Blender entrypoint for a real character preview with the saved channel colors."""
import json,sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from characters import build_character
from environment import configure
args=sys.argv[sys.argv.index('--')+1:];config=json.loads(Path(args[0]).read_text());target=Path(args[1])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='MATERIAL';scene.display.shading.background_type='WORLD';configure(scene,config.get('branding',{}))
build_character(config.get('branding',{}),pose='wave')
bpy.ops.object.camera_add(location=(3,-8,3));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2.65;cam.rotation_euler=(Vector((0,0,1.05))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
scene.render.resolution_x=384;scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(target)
bpy.ops.render.render(write_still=True)
