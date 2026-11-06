"""Original reusable CurioLab characters. Blender module; no third-party models."""
import math
import bpy
from mathutils import Vector

DEFAULT_COLORS={'shirt':'#E8BE45','pants':'#285878','shoes':'#2E72B8','hair':'#34251E','skin':'#DFA16D'}

def rgb(value,fallback='#D8EF86'):
    value=value if isinstance(value,str) and len(value)==7 and value.startswith('#') else fallback
    try:
        channels=[int(value[i:i+2],16)/255 for i in (1,3,5)]
        return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in channels)
    except ValueError:return rgb(fallback)

def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb(color),1);return m

def build_character(branding=None,location=(0,0,0),scale=1,pose='wave'):
    branding=branding or {}
    if branding.get('mascot',{}).get('id'):
        from mascot_asset import load_approved_mascot
        return load_approved_mascot(branding['mascot'],location,scale,pose)
    config=branding.get('character',{})
    preset=config.get('preset','explorer');smooth=branding.get('visual_style','rounded')=='rounded'
    colors={k:config.get(k,default) for k,default in DEFAULT_COLORS.items()}
    mats={k:material('CurioLab '+k,v) for k,v in colors.items()}
    mats.update(eye=material('Brilho branco','#FFFFFF'),pupil=material('Pupila','#17202A'),accent=material('Destaque',branding.get('accent_color','#D8EF86')))
    root=bpy.data.objects.new('Personagem CurioLab · '+preset,None);bpy.context.collection.objects.link(root)
    parts=[]
    def sphere(name,loc,size,mat):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24 if smooth else 12,ring_count=12 if smooth else 6,radius=1,location=loc)
        o=bpy.context.object;o.name=name;o.scale=size;o.data.materials.append(mat);o.parent=root;parts.append(o)
        for p in o.data.polygons:p.use_smooth=smooth
        return o
    def rod(name,a,b,radius,mat):
        delta=Vector(b)-Vector(a);mid=(Vector(a)+Vector(b))/2
        bpy.ops.mesh.primitive_cylinder_add(vertices=16 if smooth else 8,radius=radius,depth=delta.length,location=mid)
        o=bpy.context.object;o.name=name;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();o.data.materials.append(mat);o.parent=root;parts.append(o)
        for p in o.data.polygons:p.use_smooth=smooth
        sphere(name+' junta',a,(radius,radius,radius),mat);sphere(name+' ponta',b,(radius,radius,radius),mat)
        return o
    sphere('Torso',(0,0,1.04),(.29,.19,.39),mats['shirt'])
    sphere('Gola',(0,0,1.33),(.17,.14,.09),mats['accent'])
    rod('Pescoco',(0,0,1.3),(0,0,1.48),.10,mats['skin'])
    sphere('Cabeca',(0,-.015,1.65),(.34,.29,.36),mats['skin'])
    for side in [-1,1]:
        sphere('Orelha',(side*.32,-.01,1.64),(.065,.058,.095),mats['skin'])
        sphere('Olho branco',(side*.125,-.274,1.70),(.074,.032,.089),mats['eye'])
        sphere('Pupila',(side*.12,-.300,1.70),(.046,.018,.060),mats['pupil'])
        sphere('Reflexo',(side*.12-.012,-.317,1.725),(.015,.008,.018),mats['eye'])
        rod('Sobrancelha',(side*.125-.055,-.265,1.83),(side*.125+.045,-.266,1.84),.016,mats['hair'])
    sphere('Nariz',(0,-.296,1.60),(.052,.052,.060),mats['skin'])
    # Small original smiling mouth; curve sits on the front of the face.
    curve=bpy.data.curves.new('Sorriso','CURVE');curve.dimensions='3D';curve.bevel_depth=.014;curve.bevel_resolution=2
    spline=curve.splines.new('POLY');pts=[(-.085,-.283,1.53),(-.05,-.299,1.495),(0,-.307,1.485),(.05,-.299,1.495),(.085,-.283,1.53)]
    spline.points.add(len(pts)-1)
    for p,xyz in zip(spline.points,pts):p.co=(*xyz,1)
    mouth=bpy.data.objects.new('Sorriso',curve);bpy.context.collection.objects.link(mouth);mouth.data.materials.append(mats['pupil']);mouth.parent=root;parts.append(mouth)
    for i,(x,y,z,sz) in enumerate([(-.20,-.07,1.94,.16),(0,-.08,1.99,.19),(.19,-.04,1.95,.17),(-.17,.10,1.91,.18),(.14,.11,1.93,.19)]):
        sphere('Cabelo '+str(i),(x,y,z),(sz,sz*.85,sz*.7),mats['hair'])
    for side in [-1,1]:
        x=side*.14
        sphere('Quadril',(x,0,.69),(.14,.15,.17),mats['pants'])
        if pose=='sit':
            rod('Coxa',(x,0,.65),(x,-.38,.62),.11,mats['pants'])
            rod('Canela',(x,-.38,.62),(x,-.38,.24),.085,mats['skin'])
            sphere('Sapato',(x,-.47,.13),(.125,.23,.11),mats['shoes'])
        else:
            rod('Perna',(x,0,.61),(x,-.015,.24),.105,mats['pants'])
            sphere('Sapato',(x,-.075,.13),(.125,.23,.11),mats['shoes'])
        shoulder=(side*.28,0,1.20)
        if pose=='wave' and side==1:elbow=(side*.49,-.015,1.39);hand=(side*.40,-.035,1.70)
        elif pose=='point' and side==1:elbow=(side*.48,-.12,1.14);hand=(side*.70,-.16,1.22)
        else:elbow=(side*.37,0,.99);hand=(side*.37,-.06,.77)
        rod('Manga',shoulder,tuple(Vector(shoulder).lerp(Vector(elbow),.45)),.11,mats['shirt'])
        rod('Braco',tuple(Vector(shoulder).lerp(Vector(elbow),.45)),elbow,.075,mats['skin'])
        rod('Antebraco',elbow,hand,.069,mats['skin']);sphere('Mao',hand,(.082,.065,.095),mats['skin'])
    if preset=='builder':
        sphere('Capacete',(0,.01,1.96),(.37,.31,.20),mats['accent'])
        sphere('Aba capacete',(0,-.07,1.91),(.40,.38,.04),mats['accent'])
    if preset=='scientist':
        # Lab coat has two front strips; glasses in front of both eyes.
        for side in [-1,1]:
            sphere('Jaleco',(side*.14,-.145,1.04),(.13,.07,.31),mats['eye'])
            bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=8,major_radius=.09,minor_radius=.014,location=(side*.125,-.322,1.70),rotation=(math.pi/2,0,0))
            o=bpy.context.object;o.data.materials.append(mats['pupil']);o.parent=root;parts.append(o)
        rod('Ponte oculos',(-.035,-.324,1.70),(.035,-.324,1.70),.012,mats['pupil'])
    root.location=location;root.scale=(scale,)*3
    return {'root':root,'parts':parts,'preset':preset}
