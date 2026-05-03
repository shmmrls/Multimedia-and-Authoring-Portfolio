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
NEPTUNE_RADIUS = 24.6
RING_INNER    = NEPTUNE_RADIUS * 1.6   
RING_OUTER    = NEPTUNE_RADIUS * 2.5   
NEPTUNE_TILT  = 28.32                   # Neptune's true tilt, very similar to Saturn's

# Animation timeline configuration
# Neptune rotates in ~16 hours. 
TOTAL_FRAMES = 240 
ROTATION_RATIO = 1.0 

PLANET_TEXTURES = {
    "Neptune": {"map": "neptune_map.jpg", "rings": "neptune_rings.png"},
    "GenericMoon": {"surface": "moon_surface.jpg", "bump": "moon_bump.jpg"}
}

# Major Moons (Radius, Distance, Rotations per 240 frames, Texture)
# Massively scaled up radii so they are clearly visible!
MAJOR_MOONS = [
    # Triton famously has a RETROGRADE orbit (spins backwards!)
    {"name": "Triton", "radius": 8.0, "distance": NEPTUNE_RADIUS * 4.0, "rotations": -2, "tex": "GenericMoon"},
    {"name": "Proteus", "radius": 3.0, "distance": NEPTUNE_RADIUS * 2.0, "rotations": 4, "tex": "GenericMoon"},
    {"name": "Nereid", "radius": 2.5, "distance": NEPTUNE_RADIUS * 6.5, "rotations": 1, "tex": "GenericMoon"},
    {"name": "Larissa", "radius": 1.5, "distance": NEPTUNE_RADIUS * 1.5, "rotations": 5, "tex": "GenericMoon"},
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
    eevee.shadow_cube_size            = "2048"
    eevee.shadow_cascade_size         = "2048"

    eevee.use_bloom                   = True
    eevee.bloom_threshold             = 1.0    
    eevee.bloom_intensity             = 0.03   
    eevee.bloom_radius                = 4.0
    eevee.bloom_color                 = (0.2, 0.4, 1.0)  # Deep blue bloom

    eevee.use_ssr                     = True   
    eevee.use_ssr_halfres             = True
    eevee.use_gtao                    = True   
    eevee.gtao_distance               = 0.5
    eevee.gtao_factor                 = 0.6

    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look            = "High Contrast" 
    scene.view_settings.exposure        = -0.5  
    scene.view_settings.gamma           = 1.0

def setup_world():
    world = bpy.data.worlds.new("Space_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    wn = world.node_tree.nodes
    wl = world.node_tree.links
    wn.clear()

    w_out  = wn.new("ShaderNodeOutputWorld")
    w_bg   = wn.new("ShaderNodeBackground")
    w_mix  = wn.new("ShaderNodeMixShader")
    w_bg2  = wn.new("ShaderNodeBackground")   
    w_env  = wn.new("ShaderNodeTexEnvironment")
    w_tex_coord = wn.new("ShaderNodeTexCoord")
    w_is_cam    = wn.new("ShaderNodeLightPath") 

    star_img = load_tex("stars.jpg", colorspace="Linear")
    if star_img:
        w_env.image = star_img
        wl.new(w_tex_coord.outputs["Generated"], w_env.inputs["Vector"])
        wl.new(w_env.outputs["Color"], w_bg.inputs["Color"])
        w_bg.inputs["Strength"].default_value = 0.15  
    else:
        w_bg.inputs["Color"].default_value    = (0.005, 0.005, 0.012, 1)
        w_bg.inputs["Strength"].default_value = 1.0

    w_bg2.inputs["Color"].default_value    = (0.002, 0.002, 0.005, 1)
    w_bg2.inputs["Strength"].default_value = 1.0

    wl.new(w_is_cam.outputs["Is Camera Ray"], w_mix.inputs["Fac"])
    wl.new(w_bg2.outputs["Background"], w_mix.inputs[1])
    wl.new(w_bg.outputs["Background"],  w_mix.inputs[2])
    wl.new(w_mix.outputs["Shader"],     w_out.inputs["Surface"])

# ==============================================================================
# MATERIALS
# ==============================================================================

def create_celestial_body(name, radius, location, segments=128, ring_count=64, is_low_poly=False):
    if is_low_poly:
        bpy.ops.mesh.primitive_ico_sphere_add(radius=radius, subdivisions=2, location=location)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=radius, segments=segments, ring_count=ring_count, location=location, calc_uvs=True)
        bpy.ops.object.shade_smooth()
    obj = bpy.context.object
    obj.name = name
    return obj

def apply_material_neptune(neptune_obj):
    sm = bpy.data.materials.new("Neptune_Mat")
    sm.use_nodes = True
    sn = sm.node_tree.nodes
    sl = sm.node_tree.links
    sn.clear()

    s_out   = sn.new("ShaderNodeOutputMaterial")
    s_bsdf  = sn.new("ShaderNodeBsdfPrincipled")
    s_tex   = sn.new("ShaderNodeTexImage")
    s_emit  = sn.new("ShaderNodeEmission")    
    s_mix   = sn.new("ShaderNodeMixShader")
    s_add   = sn.new("ShaderNodeAddShader")
    s_fres  = sn.new("ShaderNodeFresnel")
    s_gamma = sn.new("ShaderNodeGamma")      

    sat_img = load_tex(PLANET_TEXTURES["Neptune"]["map"])
    if sat_img:
        s_tex.image = sat_img
        sl.new(s_tex.outputs["Color"], s_gamma.inputs["Color"])
        s_gamma.inputs["Gamma"].default_value = 1.15
        sl.new(s_gamma.outputs["Color"], s_bsdf.inputs["Base Color"])
    else:
        s_bsdf.inputs["Base Color"].default_value = (0.1, 0.3, 0.8, 1) # Deep blue

    s_bsdf.inputs["Roughness"].default_value   = 0.5
    s_bsdf.inputs["Specular"].default_value    = 0.2
    s_bsdf.inputs["Metallic"].default_value    = 0.0

    s_fres.inputs["IOR"].default_value         = 1.25
    s_emit.inputs["Color"].default_value       = (0.2, 0.5, 1.0, 1) # Deep blue glow
    s_emit.inputs["Strength"].default_value    = 0.35  

    sl.new(s_fres.outputs["Fac"], s_mix.inputs["Fac"])
    sl.new(s_bsdf.outputs["BSDF"], s_mix.inputs[1])
    sl.new(s_emit.outputs["Emission"], s_mix.inputs[2])

    sl.new(s_bsdf.outputs["BSDF"], s_add.inputs[0])
    sl.new(s_emit.outputs["Emission"], s_add.inputs[1])

    s_mix2 = sn.new("ShaderNodeMixShader")
    s_mix2.inputs["Fac"].default_value = 0.20
    sl.new(s_bsdf.outputs["BSDF"],  s_mix2.inputs[1])
    sl.new(s_emit.outputs["Emission"], s_mix2.inputs[2])
    sl.new(s_fres.outputs["Fac"],   s_mix2.inputs["Fac"])
    sl.new(s_mix2.outputs["Shader"], s_out.inputs["Surface"])

    neptune_obj.data.materials.append(sm)

def create_torus_ring(name, radius, thickness, alpha, parent_obj):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=radius,
        minor_radius=thickness,
        location=(0, 0, 0),
        major_segments=128,
        minor_segments=16
    )
    ring = bpy.context.object
    ring.name = name
    bpy.ops.object.shade_smooth()
    ring.parent = parent_obj

    mat = bpy.data.materials.new(f"{name}_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")

    bsdf.inputs["Base Color"].default_value = (0.7, 0.8, 1.0, 1) # Pale blue/white rings
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Alpha"].default_value = alpha

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    mat.blend_method = 'BLEND'
    mat.shadow_method = 'NONE'
    ring.data.materials.append(mat)
    return ring

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
        
    m_bsdf.inputs["Roughness"].default_value = 0.92
    m_bsdf.inputs["Specular"].default_value  = 0.05
    ml.new(m_bsdf.outputs["BSDF"], m_out.inputs["Surface"])
    
    if len(moon_obj.data.materials) == 0: moon_obj.data.materials.append(mat)
    else: moon_obj.data.materials[0] = mat

# ==============================================================================
# SYSTEM GENERATION & ANIMATION
# ==============================================================================

def create_and_animate_system():
    # NEPTUNE TILT PIVOT
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    tilt_empty = bpy.context.object
    tilt_empty.name = "Neptune_TiltPivot"
    tilt_empty.rotation_euler[0] = math.radians(NEPTUNE_TILT)

    # NEPTUNE
    neptune = create_celestial_body("Neptune", NEPTUNE_RADIUS, (0, 0, 0), segments=128, ring_count=64)
    neptune.parent = tilt_empty
    apply_material_neptune(neptune)
    
    # RINGS (Distinct 3D Torus Rings)
    create_torus_ring("Ring_1", 30.2, 0.04, 0.05, neptune)
    create_torus_ring("Ring_2", 33.2, 0.04, 0.06, neptune)
    create_torus_ring("Ring_3", 36.4, 0.08, 0.04, neptune)
    create_torus_ring("Ring_4", 38.8, 0.04, 0.05, neptune)
    create_torus_ring("Ring_Adams", 42.0, 0.06, 0.08, neptune)

    # Animate Neptune and Rings
    add_keyframe_rotation_z(neptune, 1, 0)
    add_keyframe_rotation_z(neptune, TOTAL_FRAMES + 1, 360 * ROTATION_RATIO)
    set_linear_cycles(neptune)
    
    # MOONS
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    moons_master = bpy.context.object
    moons_master.name = "Moons_Tilt_Master"
    moons_master.rotation_euler[0] = math.radians(NEPTUNE_TILT)

    # 1. Major Moons
    for md in MAJOR_MOONS:
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
        pivot = bpy.context.object
        pivot.name = f"{md['name']}_Orbit"
        pivot.parent = moons_master
        
        moon_obj = create_celestial_body(md["name"], md["radius"], (md["distance"], 0, 0), segments=48, ring_count=24)
        apply_material_moon(moon_obj, md["tex"])
        moon_obj.parent = pivot
        
        start_angle = random.uniform(0, 360)
        add_keyframe_rotation_z(pivot, 1, start_angle)
        add_keyframe_rotation_z(pivot, TOTAL_FRAMES + 1, start_angle + (360 * md["rotations"]))
        set_linear_cycles(pivot)

    # 2. Cinematic Swarm
    for i in range(1, 10):
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        pivot = bpy.context.object
        pivot.name = f"MinorMoon_Pivot_{i}"
        pivot.parent = moons_master
        
        pivot.rotation_euler[0] = math.radians(random.uniform(-45, 45))
        pivot.rotation_euler[1] = math.radians(random.uniform(-45, 45))
        
        m_radius = random.uniform(0.5, 1.2)
        m_distance = NEPTUNE_RADIUS * random.uniform(2.5, 6.0)
        
        moon_obj = create_celestial_body(f"MinorMoon_{i}", m_radius, (m_distance, 0, 0), is_low_poly=True)
        moon_obj.scale = (1.0, random.uniform(0.5, 0.9), random.uniform(0.5, 0.9))
        apply_material_moon(moon_obj, "GenericMoon")
        moon_obj.parent = pivot
        
        start_angle = random.uniform(0, 360)
        speed = random.choice([-2, -1, 1, 2, 3])
        add_keyframe_rotation_z(pivot, 1, start_angle)
        add_keyframe_rotation_z(pivot, TOTAL_FRAMES + 1, start_angle + (360 * speed))
        set_linear_cycles(pivot)

    return neptune

# ==============================================================================
# LIGHTING & CAMERA
# ==============================================================================

def setup_lighting(neptune):
    # Primary Sun (distant)
    bpy.ops.object.light_add(type="SUN", location=(200, -200, 100))
    sun = bpy.context.object
    sun.name = "Sun"
    sun.data.energy          = 5.5       
    sun.data.angle           = 0.009     
    sun.data.color           = (1.0, 0.98, 0.95)   

    sun_track = sun.constraints.new(type='TRACK_TO')
    sun_track.target = neptune
    sun_track.track_axis = 'TRACK_NEGATIVE_Z'
    sun_track.up_axis = 'UP_Y'

    sun.data.use_contact_shadow = True
    sun.data.contact_shadow_bias     = 0.001
    sun.data.contact_shadow_distance = 0.2

    # Rim light 
    bpy.ops.object.light_add(type="SUN", location=(-100, 100, -20))
    rim = bpy.context.object
    rim.name = "Rim_Light"
    rim.data.energy  = 0.15          
    rim.data.color   = (0.6, 0.85, 1.0)  
    rim.rotation_euler = (math.radians(-40), 0, math.radians(-150))

    # Space Fill
    bpy.ops.object.light_add(type="AREA", location=(0, 0, 80))
    fill = bpy.context.object
    fill.name = "Space_Fill"
    fill.data.energy = 0.1           
    fill.data.size   = 300
    fill.data.color  = (0.1, 0.15, 0.40)  

def setup_camera(neptune):
    # Backing the camera up so the full rings and planet fit comfortably in the frame
    CAM_DIST = RING_OUTER * 6.5   

    bpy.ops.object.camera_add(location=(CAM_DIST * 0.3, -CAM_DIST * 0.8, CAM_DIST * 0.25))
    cam = bpy.context.object
    cam.name = "Main_Camera"
    cam.data.lens        = 60     
    cam.data.clip_start  = 0.1
    cam.data.clip_end    = 10000

    track = cam.constraints.new(type='TRACK_TO')
    track.target = neptune
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    bpy.context.scene.camera = cam
    cam.data.dof.use_dof = False

def main():
    clear_scene()
    setup_rendering()
    setup_world()
    
    neptune = create_and_animate_system()
    setup_lighting(neptune)
    setup_camera(neptune)
    
    print(f"✅ Majestic Neptune sequence generated with retrograde Triton over {TOTAL_FRAMES} frames!")

if __name__ == "__main__":
    main()
