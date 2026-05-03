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
URANUS_RADIUS = 25.3
RING_INNER    = URANUS_RADIUS * 1.5   
RING_OUTER    = URANUS_RADIUS * 2.2   
# Uranus famously spins on its side! 
URANUS_TILT   = 97.77                   

# Animation timeline configuration
# Uranus rotates in ~17 hours. Earth (24h) = 360 frames. 360 * (17/24) = 255.
TOTAL_FRAMES = 255 
# Because the planet is tilted past 90 degrees, it naturally spins retrograde!
ROTATION_RATIO = 1.0 

PLANET_TEXTURES = {
    "Uranus": {"map": "uranus_map.jpg", "rings": "uranus_rings.png"},
    "GenericMoon": {"surface": "moon_surface.jpg", "bump": "moon_bump.jpg"}
}

# Major Moons (Radius, Distance, Rotations per 255 frames, Texture)
# Massively scaled up radii so they are clearly visible!
MAJOR_MOONS = [
    {"name": "Titania", "radius": 4.0, "distance": URANUS_RADIUS * 5.0, "rotations": 2, "tex": "GenericMoon"},
    {"name": "Oberon", "radius": 3.8, "distance": URANUS_RADIUS * 6.5, "rotations": 1, "tex": "GenericMoon"},
    {"name": "Umbriel", "radius": 3.0, "distance": URANUS_RADIUS * 3.5, "rotations": 3, "tex": "GenericMoon"},
    {"name": "Ariel", "radius": 2.8, "distance": URANUS_RADIUS * 2.5, "rotations": 4, "tex": "GenericMoon"},
    {"name": "Miranda", "radius": 1.5, "distance": URANUS_RADIUS * 1.5, "rotations": 5, "tex": "GenericMoon"},
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
    eevee.bloom_intensity             = 0.02   
    eevee.bloom_radius                = 4.0
    eevee.bloom_color                 = (0.7, 0.9, 1.0)  # Pale icy blue bloom

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

def apply_material_uranus(uranus_obj):
    sm = bpy.data.materials.new("Uranus_Mat")
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

    # Detail: Generate banded noise for visual cloud layers (NO bumps, just color)
    u_coord = sn.new("ShaderNodeTexCoord")
    u_mapping = sn.new("ShaderNodeMapping")
    # Stretch noise along the Z-axis (poles) to create horizontal gas bands
    u_mapping.inputs["Scale"].default_value = (2.0, 2.0, 15.0) 

    u_noise = sn.new("ShaderNodeTexNoise")
    u_noise.inputs["Scale"].default_value = 4.0
    u_noise.inputs["Detail"].default_value = 15.0
    sl.new(u_coord.outputs["Object"], u_mapping.inputs["Vector"])
    sl.new(u_mapping.outputs["Vector"], u_noise.inputs["Vector"])

    sat_img = load_tex(PLANET_TEXTURES["Uranus"]["map"])
    if sat_img:
        s_tex.image = sat_img
        sl.new(s_tex.outputs["Color"], s_gamma.inputs["Color"])
        s_gamma.inputs["Gamma"].default_value = 1.15
        
        # Mix noise with texture to add visible banding/clouds
        u_mix_color = sn.new("ShaderNodeMixRGB")
        u_mix_color.blend_type = "OVERLAY"
        u_mix_color.inputs["Fac"].default_value = 0.35
        sl.new(s_gamma.outputs["Color"], u_mix_color.inputs[1])
        sl.new(u_noise.outputs["Color"], u_mix_color.inputs[2])
        
        sl.new(u_mix_color.outputs["Color"], s_bsdf.inputs["Base Color"])
    else:
        s_bsdf.inputs["Base Color"].default_value = (0.6, 0.8, 0.9, 1) # Pale icy blue

    # Uranus is a very smooth, featureless icy gas giant
    s_bsdf.inputs["Roughness"].default_value   = 0.4
    s_bsdf.inputs["Specular"].default_value    = 0.2
    s_bsdf.inputs["Metallic"].default_value    = 0.0

    s_fres.inputs["IOR"].default_value         = 1.25
    s_emit.inputs["Color"].default_value       = (0.5, 0.8, 0.9, 1) # Cold blue glow
    # Reduced emission strength slightly so the cloud bands don't get washed out
    s_emit.inputs["Strength"].default_value    = 0.25  

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

    uranus_obj.data.materials.append(sm)

def apply_material_rings(ring_obj):
    rm = bpy.data.materials.new("Rings_Mat")
    rm.use_nodes = True
    rm.blend_method   = "BLEND"     
    rm.shadow_method  = "HASHED"    
    rm.use_backface_culling = False

    rn = rm.node_tree.nodes
    rl = rm.node_tree.links
    rn.clear()

    r_out   = rn.new("ShaderNodeOutputMaterial")
    r_bsdf  = rn.new("ShaderNodeBsdfPrincipled")
    r_tex   = rn.new("ShaderNodeTexImage")
    r_coord = rn.new("ShaderNodeTexCoord")
    r_sep   = rn.new("ShaderNodeSeparateXYZ")
    r_comb  = rn.new("ShaderNodeCombineXYZ")
    r_dist  = rn.new("ShaderNodeVectorMath")   
    r_math_a = rn.new("ShaderNodeMath")        
    r_div   = rn.new("ShaderNodeMath")
    r_pi_div = rn.new("ShaderNodeMath")
    r_remap = rn.new("ShaderNodeMapRange")
    r_uv_out = rn.new("ShaderNodeCombineXYZ")

    r_dist.operation  = "LENGTH"   
    r_math_a.operation = "ARCTAN2"
    r_div.operation = "DIVIDE"
    r_pi_div.operation = "DIVIDE"

    rl.new(r_coord.outputs["Object"], r_sep.inputs["Vector"])

    # Radius
    rl.new(r_sep.outputs["X"], r_comb.inputs["X"])
    rl.new(r_sep.outputs["Y"], r_comb.inputs["Y"])
    r_comb.inputs["Z"].default_value = 0.0
    rl.new(r_comb.outputs["Vector"], r_dist.inputs[0])

    r_div.inputs[1].default_value = RING_OUTER
    rl.new(r_dist.outputs["Value"], r_div.inputs[0])

    # Angle
    rl.new(r_sep.outputs["Y"], r_math_a.inputs[0])
    rl.new(r_sep.outputs["X"], r_math_a.inputs[1])

    r_pi_div.inputs[1].default_value = math.pi
    rl.new(r_math_a.outputs["Value"], r_pi_div.inputs[0])

    r_remap.inputs["From Min"].default_value = -1.0
    r_remap.inputs["From Max"].default_value =  1.0
    r_remap.inputs["To Min"].default_value   =  0.0
    r_remap.inputs["To Max"].default_value   =  1.0
    rl.new(r_pi_div.outputs["Value"], r_remap.inputs["Value"])

    # UV Combine
    rl.new(r_div.outputs["Value"],   r_uv_out.inputs["X"])
    rl.new(r_remap.outputs["Result"], r_uv_out.inputs["Y"])
    r_uv_out.inputs["Z"].default_value = 0.0

    r_tex.image = load_tex(PLANET_TEXTURES["Uranus"]["rings"])
    if r_tex.image:
        r_tex.extension = "EXTEND"   
        r_tex.interpolation = "Cubic"
        rl.new(r_uv_out.outputs["Vector"], r_tex.inputs["Vector"])
        
        # Noise to make rotation visible!
        r_noise = rn.new("ShaderNodeTexNoise")
        r_noise.inputs["Scale"].default_value = 25.0
        r_noise.inputs["Detail"].default_value = 10.0
        
        r_mix = rn.new("ShaderNodeMixRGB")
        r_mix.blend_type = "MULTIPLY"
        r_mix.inputs["Fac"].default_value = 0.6 # Stronger noise since Uranus rings are very thin
        rl.new(r_tex.outputs["Color"], r_mix.inputs[1])
        rl.new(r_noise.outputs["Color"], r_mix.inputs[2])
        
        rl.new(r_mix.outputs["Color"], r_bsdf.inputs["Base Color"])
        
        # Multiply alpha to make the rings extremely faint and dusty
        alpha_mult = rn.new("ShaderNodeMath")
        alpha_mult.operation = "MULTIPLY"
        alpha_mult.inputs[1].default_value = 0.15
        rl.new(r_tex.outputs["Alpha"], alpha_mult.inputs[0])
        rl.new(alpha_mult.outputs["Value"], r_bsdf.inputs["Alpha"])
    
    r_bsdf.inputs["Roughness"].default_value  = 0.85
    r_bsdf.inputs["Specular"].default_value   = 0.08
    r_bsdf.inputs["Metallic"].default_value   = 0.0
    rl.new(r_bsdf.outputs["BSDF"], r_out.inputs["Surface"])

    ring_obj.data.materials.append(rm)

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
    # URANUS TILT PIVOT
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    tilt_empty = bpy.context.object
    tilt_empty.name = "Uranus_TiltPivot"
    # Tilting around the Y-axis so the pole points sideways relative to the camera.
    # This gives the iconic "vertical rings / rolling barrel" view from the front!
    tilt_empty.rotation_euler[1] = math.radians(URANUS_TILT)
    # Angle it slightly towards camera so we can see the rings clearly
    tilt_empty.rotation_euler[2] = math.radians(15) 

    # URANUS
    uranus = create_celestial_body("Uranus", URANUS_RADIUS, (0, 0, 0), segments=128, ring_count=64)
    uranus.parent = tilt_empty
    apply_material_uranus(uranus)
    
    # RINGS 
    bpy.ops.mesh.primitive_circle_add(vertices=128, radius=RING_OUTER, fill_type="NGON", location=(0, 0, 0))
    rings = bpy.context.object
    rings.name = "Uranus_Rings"
    rings.parent = uranus 
    bpy.ops.object.shade_smooth()
    apply_material_rings(rings)

    # Animate Uranus and Rings
    add_keyframe_rotation_z(uranus, 1, 0)
    add_keyframe_rotation_z(uranus, TOTAL_FRAMES + 1, 360 * ROTATION_RATIO)
    set_linear_cycles(uranus)
    
    # MOONS
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    moons_master = bpy.context.object
    moons_master.name = "Moons_Tilt_Master"
    moons_master.rotation_euler[1] = math.radians(URANUS_TILT)
    moons_master.rotation_euler[2] = math.radians(15)

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
        m_distance = URANUS_RADIUS * random.uniform(2.5, 6.0)
        
        moon_obj = create_celestial_body(f"MinorMoon_{i}", m_radius, (m_distance, 0, 0), is_low_poly=True)
        moon_obj.scale = (1.0, random.uniform(0.5, 0.9), random.uniform(0.5, 0.9))
        apply_material_moon(moon_obj, "GenericMoon")
        moon_obj.parent = pivot
        
        start_angle = random.uniform(0, 360)
        speed = random.choice([-2, -1, 1, 2, 3])
        add_keyframe_rotation_z(pivot, 1, start_angle)
        add_keyframe_rotation_z(pivot, TOTAL_FRAMES + 1, start_angle + (360 * speed))
        set_linear_cycles(pivot)

    return uranus

# ==============================================================================
# LIGHTING & CAMERA
# ==============================================================================

def setup_lighting(uranus):
    # Primary Sun
    bpy.ops.object.light_add(type="SUN", location=(200, -200, 100))
    sun = bpy.context.object
    sun.name = "Sun"
    sun.data.energy          = 5.5       
    sun.data.angle           = 0.009     
    sun.data.color           = (1.0, 0.98, 0.95)   

    sun_track = sun.constraints.new(type='TRACK_TO')
    sun_track.target = uranus
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

def setup_camera(uranus):
    # Backing the camera up so the full vertical rings and planet fit in the frame
    CAM_DIST = RING_OUTER * 6.5   

    bpy.ops.object.camera_add(location=(CAM_DIST * 0.3, -CAM_DIST * 0.8, CAM_DIST * 0.25))
    cam = bpy.context.object
    cam.name = "Main_Camera"
    cam.data.lens        = 60     
    cam.data.clip_start  = 0.1
    cam.data.clip_end    = 10000

    track = cam.constraints.new(type='TRACK_TO')
    track.target = uranus
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    bpy.context.scene.camera = cam
    cam.data.dof.use_dof = False

def main():
    clear_scene()
    setup_rendering()
    setup_world()
    
    uranus = create_and_animate_system()
    setup_lighting(uranus)
    setup_camera(uranus)
    
    print(f"✅ Majestic Uranus sequence generated with sideways axial tilt over {TOTAL_FRAMES} frames!")

if __name__ == "__main__":
    main()
