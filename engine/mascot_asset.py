"""Blender bridge: import the pinned approved GLB; never rebuild NICO per video."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from mascot_registry import MascotRegistry,MascotValidationError

def load_approved_mascot(selection,location=(0,0,0),scale=1,pose='idle'):
    import bpy
    registry=MascotRegistry(ROOT)
    config=registry.resolve(selection,require_approved=True)
    record=next((v for v in registry.catalog()['mascots'] if v['id']==selection['id'] and v['version']==selection['version']),None)
    model=next((a for a in (record or {}).get('assets',[]) if a.get('kind')=='model' and str(a.get('path','')).endswith('.glb')),None)
    if not model:raise MascotValidationError('A versão aprovada não contém o GLB canônico.')
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/model['path']))
    imported=set(bpy.data.objects)-before
    root=bpy.data.objects.new(f"{selection['id']}@{selection['version']}",None);bpy.context.collection.objects.link(root)
    for obj in imported:
        if obj.parent not in imported:obj.parent=root
        if obj.animation_data:
            for track in obj.animation_data.nla_tracks:track.mute=pose not in track.name.lower()
    root.location=location;root.scale=(scale,)*3
    root['mascot_id']=selection['id'];root['mascot_version']=selection['version'];root['config_sha256']=selection['config_sha256']
    return {'root':root,'parts':list(imported),'preset':selection['id'],'version':selection['version'],'immutable_asset':True}
