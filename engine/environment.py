"""Shared color-managed environment presets; preserve the channel's material colors."""
PRESETS={
 'day':{'sky':(.72,.85,.94),'ground':(.39,.64,.44),'wall':(.82,.77,.65),'light':'paint.sl'},
 'interior':{'sky':(.82,.80,.74),'ground':(.55,.36,.21),'wall':(.84,.78,.65),'light':'paint.sl'},
 'night':{'sky':(.022,.039,.090),'ground':(.12,.23,.22),'wall':(.21,.27,.34),'light':'paint.sl'},
}
def configure(scene,branding=None):
    branding=branding or {};preset=PRESETS.get(branding.get('environment','day'),PRESETS['day'])
    from characters import rgb
    colors=branding.get('palette',{})
    if colors:
        sky=rgb(colors.get('sky','#9CCBE0'));ground=rgb(colors.get('ground','#86A99A'))
        name=branding.get('environment','day')
        factor=(.035,.055,.11) if name=='night' else (.80,.78,.70) if name=='interior' else (1,1,1)
        preset=dict(preset,sky=tuple(v*f for v,f in zip(sky,factor)),ground=tuple(v*f for v,f in zip(ground,factor)))
    scene.world.color=preset['sky']
    scene.display.shading.light='STUDIO';scene.display.shading.studio_light=preset['light']
    scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
    scene.display.shading.cavity_type='BOTH';scene.display.render_aa='8'
    # Studio fill deliberately stays active at night: character readability wins.
    scene.view_settings.view_transform='Standard'
    return preset
