import bpy
import os
import math
import random
from mathutils import Vector

# ==============================================================================
# GLOBAL CONFIGURATION
# ==============================================================================

TEXTURE_DIR = r"C:\COLLEGE\THIRD TERM\MAA\Planets\textures"

# Scale factor for physical sizing (1 Blender Unit = 1,000 km for this showcase)
# Pluto is tiny! Upscaled slightly here for cinematic visibility.
PLUTO_RADIUS = 3.5
PLUTO_TILT   = 122.5                   # Pluto spins on its side AND retrograde!

# Animation timeline configuration
# Pluto takes 153 hours to rotate (6.38 Earth days). 
TOTAL_FRAMES = 360 
# If 360 frames = 24 hours, Pluto rotates ~56 degrees in that time.
# However, to make the animation visually interesting for the showcase, we'll speed it up slightly.
ROTATION_RATIO = 1.0 

PLANET_TEXTURES = {
    "Pluto": {"map": "pluto_map.jpg", "bump": "pluto_bump.jpg"},
    "GenericMoon": {"surface": "moon_surface.jpg", "bump": "moon_bump.jpg"}
}

# Pluto has 5 moons, but Charon is massive (half the size of Pluto). 
# It forms a binary system with Pluto!
MAJOR_MOONS = [
    {"name": "Charon", "radius": 1.7, "distance": PLUTO_RADIUS * 3.5, "rotations": 1.0, "tex": "GenericMoon"},
    {"name": "Styx", "radius": 0.15, "distance": PLUTO_RADIUS * 5.0, "rotations": 2.0, "tex": "GenericMoon"},
    {"name": "Nix", "radius": 0.25, "distance": PLUTO_RADIUS * 6.5, "rotations": 1.5, "tex": "GenericMoon"},
    {"name": "Kerberos", "radius": 0.2, "distance": PLUTO_RADIUS * 8.0, "rotations": 2.5, "tex": "GenericMoon"},
    {"name": "Hydra", "radius": 0.3, "distance": PLUTO_RADIUS * 9.5, "rotations": 3.0, "tex": "GenericMoon"},
]

# ==============================================================================
# HELPERS
# ==============================================================================
def load_tex(name, colorspace="sRGB"):
    for ext in (".jpg", ".png", ".jpeg", ".tif"):
        path = os.path.join(TEXTURE_DIR, name + ext)
        if os.path.exists(path):
            img = bpy.data.images.load(path)
            img.colorspace_settings.name = colorspace
            return img
    if "." in name:
        path = os.path.join(TEXTURE_DIR, name)
        if os.path.exists(path):
            img = bpy.data.images.load(path)
            img.colorspace_settings.name = colorspace
            return img
    return None

def set_linear_cycles(obj):
    if not (obj.animation_data and obj.animation_data.action):
        return
    for fc in obj.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
        if not fc.modifiers:
            fc.modifiers.new("CYCLES")

def add_keyframe_rotation_z(obj, frame, angle_deg):
    obj.rotation_euler[2] = math.radians(angle_deg)
    obj.keyframe_insert("rotation_euler", index=2, frame=frame)

# ==============================================================================
# SCENE SETUP
# ==============================================================================
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in [bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.lights, bpy.data.cameras]:
        for item in block:
            block.remove(item)

def setup_rendering():
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end   = TOTAL_FRAMES
    scene.render.engine               = "BLENDER_EEVEE"
    
    eevee = scene.eevee
    eevee.taa_render_samples          = 64
    eevee.taa_samples                 = 16
    eevee.use_soft_shadows            = True   

    # Pluto has a very faint blue haze atmosphere
    eevee.use_bloom                   = True
    eevee.bloom_threshold             = 0.9    
    eevee.bloom_intensity             = 0.02   
    eevee.bloom_color                 = (0.5, 0.7, 1.0)  

    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look            = "High Contrast" 
    scene.view_settings.exposure        = -0.2  

def setup_world():
    world = bpy.data.worlds.new("Space_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    wn = world.node_tree.nodes
    wl = world.node_tree.links
    wn.clear()

    w_out  = wn.new("ShaderNodeOutputWorld")
    w_bg   = wn.new("ShaderNodeBackground")
    w_env  = wn.new("ShaderNodeTexEnvironment")
    w_tex_coord = wn.new("ShaderNodeTexCoord")

    star_img = load_tex("stars.jpg", colorspace="Linear")
    if star_img:
        w_env.image = star_img
        wl.new(w_tex_coord.outputs["Generated"], w_env.inputs["Vector"])
        wl.new(w_env.outputs["Color"], w_bg.inputs["Color"])
        w_bg.inputs["Strength"].default_value = 0.15  
    else:
        w_bg.inputs["Color"].default_value    = (0.005, 0.005, 0.012, 1)
        w_bg.inputs["Strength"].default_value = 1.0

    wl.new(w_bg.outputs["Background"], w_out.inputs["Surface"])

# ==============================================================================
# MATERIALS
# ==============================================================================

def create_celestial_body(name, radius, location, segments=128, ring_count=64):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius, segments=segments, ring_count=ring_count, location=location, calc_uvs=True)
    bpy.ops.object.shade_smooth()
    obj = bpy.context.object
    obj.name = name
    return obj

def apply_material_pluto(pluto_obj):
    sm = bpy.data.materials.new("Pluto_Mat")
    sm.use_nodes = True
    sn = sm.node_tree.nodes
    sl = sm.node_tree.links
    sn.clear()

    s_out   = sn.new("ShaderNodeOutputMaterial")
    s_bsdf  = sn.new("ShaderNodeBsdfPrincipled")
    s_tex   = sn.new("ShaderNodeTexImage")
    s_bump  = sn.new("ShaderNodeBump")

    # Pluto is a rocky/icy body, so it's matte
    s_bsdf.inputs["Roughness"].default_value   = 0.85
    s_bsdf.inputs["Specular"].default_value    = 0.1
    s_bsdf.inputs["Metallic"].default_value    = 0.0

    img = load_tex(PLANET_TEXTURES["Pluto"]["map"])
    if img:
        s_tex.image = img
        sl.new(s_tex.outputs["Color"], s_bsdf.inputs["Base Color"])
        
        # Use color map as bump if no bump map exists
        sl.new(s_tex.outputs["Color"], s_bump.inputs["Height"])
        s_bump.inputs["Strength"].default_value = 0.1
        sl.new(s_bump.outputs["Normal"], s_bsdf.inputs["Normal"])
    else:
        s_bsdf.inputs["Base Color"].default_value = (0.7, 0.6, 0.5, 1) # Pale tan/brown

    # Add the tenuous blue haze natively into the planet's material via Fresnel 
    # to avoid any mesh clipping or weird solid white borders!
    s_fres = sn.new("ShaderNodeFresnel")
    s_emit = sn.new("ShaderNodeEmission")
    s_mix  = sn.new("ShaderNodeMixShader")
    s_add  = sn.new("ShaderNodeAddShader")

    s_fres.inputs["IOR"].default_value         = 1.15
    s_emit.inputs["Color"].default_value       = (0.5, 0.7, 1.0, 1) # Thin blue haze
    s_emit.inputs["Strength"].default_value    = 0.4

    sl.new(s_fres.outputs["Fac"], s_mix.inputs["Fac"])
    sl.new(s_bsdf.outputs["BSDF"], s_mix.inputs[1])
    sl.new(s_emit.outputs["Emission"], s_mix.inputs[2])

    sl.new(s_bsdf.outputs["BSDF"], s_add.inputs[0])
    sl.new(s_emit.outputs["Emission"], s_add.inputs[1])

    s_mix2 = sn.new("ShaderNodeMixShader")
    s_mix2.inputs["Fac"].default_value = 0.25
    sl.new(s_bsdf.outputs["BSDF"],  s_mix2.inputs[1])
    sl.new(s_emit.outputs["Emission"], s_mix2.inputs[2])
    sl.new(s_fres.outputs["Fac"],   s_mix2.inputs["Fac"])

    sl.new(s_mix2.outputs["Shader"], s_out.inputs["Surface"])
    pluto_obj.data.materials.append(sm)

def apply_material_moon(moon_obj, tex_key):
    mat = bpy.data.materials.new(name=f"{moon_obj.name}_Mat")
    mat.use_nodes = True
    mn = mat.node_tree.nodes
    ml = mat.node_tree.links
    mn.clear()
    
    m_out  = mn.new("ShaderNodeOutputMaterial")
    m_bsdf = mn.new("ShaderNodeBsdfPrincipled")
    m_tex  = mn.new("ShaderNodeTexImage")
    
    img = load_tex(PLANET_TEXTURES[tex_key]["surface"])
    if img:
        m_tex.image = img
        ml.new(m_tex.outputs["Color"], m_bsdf.inputs["Base Color"])
    else:
        m_bsdf.inputs["Base Color"].default_value = (0.65, 0.60, 0.52, 1)
        
    m_bsdf.inputs["Roughness"].default_value = 0.95
    m_bsdf.inputs["Specular"].default_value  = 0.02
    ml.new(m_bsdf.outputs["BSDF"], m_out.inputs["Surface"])
    
    moon_obj.data.materials.append(mat)

# ==============================================================================
# SYSTEM GENERATION & ANIMATION
# ==============================================================================

def create_and_animate_system():
    # PLUTO TILT PIVOT
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    tilt_empty = bpy.context.object
    tilt_empty.name = "Pluto_TiltPivot"
    # Pluto spins on its side and retrograde (122.5 degrees)
    tilt_empty.rotation_euler[1] = math.radians(PLUTO_TILT)
    # Slight angle to camera
    tilt_empty.rotation_euler[2] = math.radians(15)

    # PLUTO
    pluto = create_celestial_body("Pluto", PLUTO_RADIUS, (0, 0, 0))
    pluto.parent = tilt_empty
    apply_material_pluto(pluto)
    
    # Animate Pluto
    add_keyframe_rotation_z(pluto, 1, 0)
    add_keyframe_rotation_z(pluto, TOTAL_FRAMES + 1, 360 * ROTATION_RATIO)
    set_linear_cycles(pluto)

    # MOONS
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    moons_master = bpy.context.object
    moons_master.name = "Moons_Tilt_Master"
    moons_master.rotation_euler[1] = math.radians(PLUTO_TILT)
    moons_master.rotation_euler[2] = math.radians(15)

    # 1. Major Moons
    for md in MAJOR_MOONS:
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
        pivot = bpy.context.object
        pivot.name = f"{md['name']}_Orbit"
        pivot.parent = moons_master
        
        moon_obj = create_celestial_body(md["name"], md["radius"], (md["distance"], 0, 0), segments=64, ring_count=32)
        apply_material_moon(moon_obj, md["tex"])
        moon_obj.parent = pivot
        
        start_angle = random.uniform(0, 360)
        # Charon is tidally locked to Pluto!
        speed = ROTATION_RATIO if md["name"] == "Charon" else md["rotations"]
        
        add_keyframe_rotation_z(pivot, 1, start_angle)
        add_keyframe_rotation_z(pivot, TOTAL_FRAMES + 1, start_angle + (360 * speed))
        set_linear_cycles(pivot)

    return pluto

# ==============================================================================
# LIGHTING & CAMERA
# ==============================================================================

def setup_lighting(pluto):
    # The Sun is extremely distant from Pluto, so lighting is very dim and sharp!
    bpy.ops.object.light_add(type="SUN", location=(100, -100, 50))
    sun = bpy.context.object
    sun.name = "Sun"
    sun.data.energy          = 1.5       # Very dim sun!
    sun.data.angle           = 0.005     # Sharp shadows
    sun.data.color           = (1.0, 1.0, 1.0)   

    sun_track = sun.constraints.new(type='TRACK_TO')
    sun_track.target = pluto
    sun_track.track_axis = 'TRACK_NEGATIVE_Z'
    sun_track.up_axis = 'UP_Y'

    # Soft dark blue fill to emulate deep space
    bpy.ops.object.light_add(type="AREA", location=(-20, 20, -20))
    fill = bpy.context.object
    fill.name = "Deep_Space_Fill"
    fill.data.energy = 0.05           
    fill.data.size   = 100
    fill.data.color  = (0.05, 0.1, 0.25)  

def setup_camera(pluto):
    CAM_DIST = PLUTO_RADIUS * 14   

    bpy.ops.object.camera_add(location=(CAM_DIST * 0.2, -CAM_DIST * 0.9, CAM_DIST * 0.2))
    cam = bpy.context.object
    cam.name = "Main_Camera"
    cam.data.lens        = 65     
    cam.data.clip_start  = 0.1
    cam.data.clip_end    = 10000

    track = cam.constraints.new(type='TRACK_TO')
    track.target = pluto
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    bpy.context.scene.camera = cam

def main():
    clear_scene()
    setup_rendering()
    setup_world()
    
    pluto = create_and_animate_system()
    setup_lighting(pluto)
    setup_camera(pluto)
    
    print(f"✅ Majestic Pluto sequence generated over {TOTAL_FRAMES} frames!")

if __name__ == "__main__":
    main()
