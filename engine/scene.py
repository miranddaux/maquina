"""Blender-only scene builder; invoked by render.py."""
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
config = json.loads(Path(args[0]).read_text())
out = Path(args[1])
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = config["width"]
scene.render.resolution_y = config["height"]
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.display.shading.light = "STUDIO"
scene.display.shading.studio_light = "paint.sl"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.background_type = "WORLD"
scene.world.color = (0.018, 0.025, 0.065)
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "BOTH"
scene.display.render_aa = "8"
scene.view_settings.view_transform = "Standard"


def material(name, rgb):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    return mat


blue = material("Ocean · azul", (0.07, 0.47, 0.94))
green = material("Land · menta", (0.18, 0.86, 0.56))
yellow = material("Orbit · amarelo", (1, 0.78, 0.15))
white = material("Estrelas", (0.80, 0.91, 1))
sunmat = material("Sol", (1, 0.47, 0.16))


def ico(name, loc, radius, mat, subdivision=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivision, radius=radius, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


planet = ico("Terra estilizada", (0, 0, 0), 1.35, blue, 3)
# Continent patches follow an irregular spherical mask; intentionally schematic.
for poly in planet.data.polygons:
    n = poly.center.normalized()
    longitude = math.atan2(n.y, n.x)
    latitude = math.asin(n.z)
    land = math.sin(2.9 * longitude + 1.2 * math.sin(latitude * 3)) + math.cos(latitude * 5 - longitude) > 0.6
    if land and abs(latitude) < 1.2:
        if len(planet.data.materials) == 1:
            planet.data.materials.append(green)
        poly.material_index = 1

planet.rotation_euler = (math.radians(15), math.radians(12), 0)
planet.keyframe_insert(data_path="rotation_euler", frame=1)
planet.rotation_euler.z = math.tau
frames = round(config["duration"] * config["fps"])
planet.keyframe_insert(data_path="rotation_euler", frame=frames + 1)
if planet.animation_data:
    for fc in planet.animation_data.action.fcurves:
        for key in fc.keyframe_points:
            key.interpolation = "LINEAR"

# Orbit ring and a moving marker make rotation legible in the silent preview.
bpy.ops.mesh.primitive_torus_add(major_segments=64, minor_segments=8, location=(0, 0, -0.15), major_radius=1.7, minor_radius=0.027)
ring = bpy.context.object
ring.rotation_euler = (math.radians(16), math.radians(12), 0)
ring.data.materials.append(yellow)
marker = ico("Marcador da rotação", (0, 0, 0), .115, yellow, 2)
for frame in range(1, frames + 2):
    angle = (frame - 1) / frames * math.tau
    marker.location = (1.7 * math.cos(angle), 1.7 * math.sin(angle), -.15)
    marker.keyframe_insert(data_path="location", frame=frame)

ico("Sol esquemático", (-2.0, .6, 1.35), .40, sunmat, 2)
random.seed(19)
for i in range(30):
    ico("Estrela", (random.uniform(-3.4, 3.4), 2.5, random.uniform(-3.2, 3.2)), random.uniform(.018, .045), white)

bpy.ops.object.camera_add(location=(3.8, -8, 3.0))
camera = bpy.context.object
camera.rotation_euler = (Vector((0, 0, .05)) - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.type = "ORTHO"
camera.data.ortho_scale = 8.3
scene.camera = camera
scene.render.fps = config["fps"]
scene.frame_start = 1
scene.frame_end = frames
scene.render.filepath = str(out / "frame_")
bpy.ops.render.render(animation=True)
