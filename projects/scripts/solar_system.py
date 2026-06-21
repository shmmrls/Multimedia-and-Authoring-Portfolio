import bpy
import bmesh
import math
import os
import random
from mathutils import Vector, Matrix

# ============================================================
# CONFIGURATION
# ============================================================
TEXTURE_DIR = r"C:\COLLEGE\THIRD TERM\MAA\Planets\textures"

PLANET_TEXTURES = {
    "Sun": {"surface": "sun_surface.jpg", "map": "sunmap.jpg"},
    "Mercury": {"color": "mercury_color.jpg", "surface": "mercury_surface.jpg", "bump": "mercury_bump.jpg"},
    "Venus": {"surface": "venus_surface.jpg", "clouds": "venus_clouds.jpg"},
    "Earth": {
        "day": "earth_daymap.jpg", 
        "night": "earth_nightmap.jpg", 
        "normal": "earth_normal_map.tif", 
        "specular": "earth_specular.jpg",
        "clouds": "earth_clouds.jpg"
    },
    "Mars": {"surface": "mars_surface.jpg", "normal": "mars_normal.jpg", "bump": "mars_bump.jpg"},
    "Jupiter": {"map": "jupiter_map.jpg"},
    "Saturn": {"map": "saturn_map.jpg", "rings": "saturn_rings.png"},
    "Uranus": {"map": "uranus_map.jpg", "rings": "uranus_rings.png"},
    "Neptune": {"map": "neptune_map.jpg", "rings": "neptune_rings.png"},
    "Pluto": {"map": "pluto_map.jpg", "bump": "pluto_bump.jpg"},
    "Moon": {"surface": "moon_surface.jpg", "bump": "moon_bump.jpg"},
    "Io": {"surface": "moon_io.png"},
    "Europa": {"surface": "moon_europa.jpg"},
    "Ganymede": {"surface": "moon_ganymede.png"},
    "Callisto": {"surface": "moon_callisto.png"}
}
RENDER_ENGINE = "BLENDER_EEVEE"   # or "CYCLES"
RESOLUTION_X = 1920
RESOLUTION_Y = 1080
FRAME_START = 1
FRAME_END = 2941
USE_BLOOM = True
USE_MOTION_BLUR = False


def tex(filename):
    """Return full path to a texture file."""
    return os.path.join(TEXTURE_DIR, filename)


# ============================================================
# SECTION 1 – SCENE SETUP
# ============================================================
def setup_scene():
    # Clear everything robustly
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat, do_unlink=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)

    scene = bpy.context.scene
    scene.frame_start = FRAME_START
    scene.frame_end   = FRAME_END
    # Use cinema standard 24 FPS for smoother, longer planetary rotation
    try:
        scene.render.fps = 24
    except Exception:
        pass

    # Render engine
    scene.render.engine = RENDER_ENGINE
    scene.render.resolution_x = RESOLUTION_X
    scene.render.resolution_y = RESOLUTION_Y
    scene.render.film_transparent = False

    if RENDER_ENGINE == "BLENDER_EEVEE":
        eevee = scene.eevee
        eevee.use_bloom = USE_BLOOM
        eevee.bloom_intensity = 0.05    # Matches celestialbodies
        eevee.bloom_threshold = 1.0     # Matches celestialbodies
        eevee.use_ssr = True
        eevee.use_soft_shadows = True
        eevee.shadow_cube_size = '1024'
        eevee.taa_render_samples = 64
        if USE_MOTION_BLUR:
            eevee.use_motion_blur = True
    else:
        cycles = scene.cycles
        cycles.samples = 128
        if USE_MOTION_BLUR:
            scene.render.use_motion_blur = True
        
        # In Cycles, Bloom must be done via the Compositor using a Glare node
        if USE_BLOOM:
            scene.use_nodes = True
            tree = scene.node_tree
            tree.nodes.clear()
            
            rlayers = tree.nodes.new(type='CompositorNodeRLayers')
            rlayers.location = (0, 0)
            
            glare = tree.nodes.new(type='CompositorNodeGlare')
            glare.location = (300, 0)
            glare.glare_type = 'FOG_GLOW'
            glare.quality = 'HIGH'
            glare.threshold = 0.8
            glare.size = 9  # Max size for glow spread
            
            comp = tree.nodes.new(type='CompositorNodeComposite')
            comp.location = (600, 0)
            
            tree.links.new(rlayers.outputs['Image'], glare.inputs['Image'])
            tree.links.new(glare.outputs['Image'], comp.inputs['Image'])

    # World – starfield
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    wnt = world.node_tree
    wnt.nodes.clear()

    bg_node  = wnt.nodes.new("ShaderNodeBackground")
    out_node = wnt.nodes.new("ShaderNodeOutputWorld")
    out_node.location = (300, 0)

    # 1. Procedural Cosmic Nebula
    noise = wnt.nodes.new("ShaderNodeTexNoise")
    noise.location = (-600, 200)
    noise.inputs["Scale"].default_value = 1.2
    noise.inputs["Detail"].default_value = 15.0
    noise.inputs["Roughness"].default_value = 0.55
    
    ramp = wnt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-400, 200)
    ramp.color_ramp.elements[0].position = 0.4
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp.color_ramp.elements[1].position = 0.6
    # Make the nebula/background tones strongly bluish
    ramp.color_ramp.elements[1].color = (0.02, 0.10, 0.32, 1.0) # Deeper navy-blue
    ramp.color_ramp.elements.new(0.85)
    ramp.color_ramp.elements[2].color = (0.06, 0.18, 0.44, 1.0) # Brighter cyan-blue highlights
    # Add a very subtle warm/yellow edge to the far ramp for atmosphere hint
    ramp.color_ramp.elements.new(0.95)
    ramp.color_ramp.elements[3].color = (0.12, 0.10, 0.04, 1.0)  # Soft light-yellow wash
    
    wnt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    
    # 2. Base Stars
    stars_path = tex("stars.jpg")
    mix_node = wnt.nodes.new("ShaderNodeMixRGB")
    mix_node.blend_type = 'ADD'
    mix_node.inputs[0].default_value = 1.0
    mix_node.location = (-150, 0)

    if os.path.exists(stars_path):
        tex_coord = wnt.nodes.new("ShaderNodeTexCoord")
        mapping    = wnt.nodes.new("ShaderNodeMapping")
        img_node   = wnt.nodes.new("ShaderNodeTexEnvironment")
        tex_coord.location  = (-800, -200)
        mapping.location    = (-600, -200)
        img_node.location   = (-400, -200)
        try:
            img_node.image = bpy.data.images.load(stars_path)
        except Exception:
            pass
        wnt.links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
        wnt.links.new(mapping.outputs["Vector"],      img_node.inputs["Vector"])
        wnt.links.new(img_node.outputs["Color"], mix_node.inputs[1])
    else:
        mix_node.inputs[1].default_value = (0.0, 0.0, 0.0, 1.0)

    wnt.links.new(ramp.outputs["Color"], mix_node.inputs[2])
    wnt.links.new(mix_node.outputs["Color"], bg_node.inputs["Color"])
    bg_node.inputs["Strength"].default_value = 0.5

    wnt.links.new(bg_node.outputs["Background"], out_node.inputs["Surface"])
    return scene


# ============================================================
# SECTION 2 - MATERIAL HELPERS
# ============================================================
def create_material_earth():
    mat = bpy.data.materials.new(name="Earth_Surface_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    tex_day = nodes.new("ShaderNodeTexImage")
    try: tex_day.image = bpy.data.images.load(tex(PLANET_TEXTURES["Earth"]["day"]))
    except: pass
        
    tex_spec = nodes.new("ShaderNodeTexImage")
    try:
        img_spec = bpy.data.images.load(tex(PLANET_TEXTURES["Earth"]["specular"]))
        try: img_spec.colorspace_settings.name = 'Non-Color'
        except: pass
        tex_spec.image = img_spec
    except: pass
    
    invert_spec = nodes.new("ShaderNodeInvert")
        
    tex_normal = nodes.new("ShaderNodeTexImage")
    try:
        img_norm = bpy.data.images.load(tex(PLANET_TEXTURES["Earth"]["normal"]))
        try: img_norm.colorspace_settings.name = 'Non-Color'
        except: pass
        tex_normal.image = img_norm
    except: pass
    
    normal_map_node = nodes.new("ShaderNodeNormalMap")
    normal_map_node.inputs['Strength'].default_value = 1.0
    
    tex_night = nodes.new("ShaderNodeTexImage")
    try: tex_night.image = bpy.data.images.load(tex(PLANET_TEXTURES["Earth"]["night"]))
    except: pass

    geometry = nodes.new("ShaderNodeNewGeometry")
    sun_away_vector = nodes.new("ShaderNodeCombineXYZ")
    sun_away_vector.inputs[0].default_value = -0.913
    sun_away_vector.inputs[1].default_value = 0.365
    sun_away_vector.inputs[2].default_value = -0.182
    
    dot_product = nodes.new("ShaderNodeVectorMath")
    dot_product.operation = 'DOT_PRODUCT'
    
    terminator_ramp = nodes.new("ShaderNodeValToRGB")
    terminator_ramp.color_ramp.elements[0].position = 0.0
    terminator_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    terminator_ramp.color_ramp.elements[1].position = 0.2
    terminator_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    
    emission_strength = nodes.new("ShaderNodeMath")
    emission_strength.operation = 'MULTIPLY'
    emission_strength.inputs[1].default_value = 0.6
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    # Make Earth less shiny by default; specular kept low and roughness high (matching Mars)
    bsdf.inputs['Roughness'].default_value = 0.95
    bsdf.inputs['Specular'].default_value = 0.02
    output = nodes.new("ShaderNodeOutputMaterial")
    
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_day.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_spec.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_normal.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_night.inputs['Vector'])
    
    links.new(tex_day.outputs['Color'], bsdf.inputs['Base Color'])
    # Use the specular map only to modulate roughness (land vs ocean),
    # but keep overall specular low so the planet isn't overly shiny.
    links.new(tex_spec.outputs['Color'], invert_spec.inputs['Color'])
    links.new(invert_spec.outputs['Color'], bsdf.inputs['Roughness']) 
    
    links.new(tex_normal.outputs['Color'], normal_map_node.inputs['Color'])
    links.new(normal_map_node.outputs['Normal'], bsdf.inputs['Normal'])
    
    links.new(geometry.outputs['Normal'], dot_product.inputs[0])
    links.new(sun_away_vector.outputs['Vector'], dot_product.inputs[1])
    links.new(dot_product.outputs['Value'], terminator_ramp.inputs['Fac'])
    links.new(terminator_ramp.outputs['Color'], emission_strength.inputs[0])
    
    links.new(tex_night.outputs['Color'], bsdf.inputs['Emission'])
    links.new(emission_strength.outputs['Value'], bsdf.inputs['Emission Strength'])
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_material_clouds():
    mat = bpy.data.materials.new(name="Cloud_Material")
    mat.use_nodes = True
    mat.blend_method = 'HASHED'
    mat.shadow_method = 'HASHED'
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    tex_clouds = nodes.new("ShaderNodeTexImage")
    try: 
        img_clouds = bpy.data.images.load(tex(PLANET_TEXTURES["Earth"]["clouds"]))
        try: img_clouds.colorspace_settings.name = 'Non-Color'
        except: pass
        tex_clouds.image = img_clouds
    except: pass
    
    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.color_ramp.elements[0].position = 0.05
    color_ramp.color_ramp.elements[0].color = (0, 0, 0, 1) 
    color_ramp.color_ramp.elements[1].position = 0.8
    color_ramp.color_ramp.elements[1].color = (1, 1, 1, 1) 
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Base Color'].default_value = (0.9, 0.9, 0.9, 1.0) 
    bsdf.inputs['Roughness'].default_value = 0.9
    bsdf.inputs['Specular'].default_value = 0.0
    
    output = nodes.new("ShaderNodeOutputMaterial")
    
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_clouds.inputs['Vector'])
    
    links.new(tex_clouds.outputs['Color'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], bsdf.inputs['Alpha'])
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_material_moon(name, tex_key):
    mat = bpy.data.materials.new(name=f"{name}_Mat")
    mat.use_nodes = True
    mn = mat.node_tree.nodes
    ml = mat.node_tree.links
    mn.clear()
    
    m_out  = mn.new("ShaderNodeOutputMaterial")
    m_bsdf = mn.new("ShaderNodeBsdfPrincipled")
    m_tex  = mn.new("ShaderNodeTexImage")
    
    try: img = bpy.data.images.load(tex(PLANET_TEXTURES[tex_key]["surface"]))
    except: img = None
    if img:
        m_tex.image = img
        ml.new(m_tex.outputs["Color"], m_bsdf.inputs["Base Color"])
    else:
        m_bsdf.inputs["Base Color"].default_value = (0.65, 0.60, 0.52, 1)
        
    m_bsdf.inputs["Roughness"].default_value = 0.92
    m_bsdf.inputs["Specular"].default_value  = 0.05
    ml.new(m_bsdf.outputs["BSDF"], m_out.inputs["Surface"])
    return mat

def create_material_jupiter():
    mat = bpy.data.materials.new(name="Jupiter_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    tex_surface = nodes.new("ShaderNodeTexImage")
    try: tex_surface.image = bpy.data.images.load(tex(PLANET_TEXTURES["Jupiter"]["map"]))
    except: pass
        
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.8
    bsdf.inputs['Specular'].default_value = 0.05
    
    output = nodes.new("ShaderNodeOutputMaterial")
    
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_surface.inputs['Vector'])
    links.new(tex_surface.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_material_mars():
    mat = bpy.data.materials.new(name="Mars_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    tex_surface = nodes.new("ShaderNodeTexImage")
    try: tex_surface.image = bpy.data.images.load(tex(PLANET_TEXTURES["Mars"]["surface"]))
    except: pass
        
    tex_normal = nodes.new("ShaderNodeTexImage")
    try: 
        img_norm = bpy.data.images.load(tex(PLANET_TEXTURES["Mars"]["normal"]))
        try: img_norm.colorspace_settings.name = 'Non-Color'
        except: pass
        tex_normal.image = img_norm
    except: pass
    
    normal_map_node = nodes.new("ShaderNodeNormalMap")
    normal_map_node.inputs['Strength'].default_value = 1.0
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.95
    bsdf.inputs['Specular'].default_value = 0.02
    
    output = nodes.new("ShaderNodeOutputMaterial")
    
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_surface.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_normal.inputs['Vector'])
    
    links.new(tex_surface.outputs['Color'], bsdf.inputs['Base Color'])
    
    links.new(tex_normal.outputs['Color'], normal_map_node.inputs['Color'])
    links.new(normal_map_node.outputs['Normal'], bsdf.inputs['Normal'])
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_material_mercury():
    mat = bpy.data.materials.new(name="Mercury_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    tex_color = nodes.new("ShaderNodeTexImage")
    try: tex_color.image = bpy.data.images.load(tex(PLANET_TEXTURES["Mercury"]["surface"]))
    except: pass
        
    tex_bump = nodes.new("ShaderNodeTexImage")
    try:
        img_b = bpy.data.images.load(tex(PLANET_TEXTURES["Mercury"]["bump"]))
        try: img_b.colorspace_settings.name = 'Non-Color'
        except: pass
        tex_bump.image = img_b
    except: pass
        
    bump_node = nodes.new("ShaderNodeBump")
    bump_node.inputs['Strength'].default_value = 0.8
    bump_node.inputs['Distance'].default_value = 0.01 
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.95  
    bsdf.inputs['Specular'].default_value = 0.02   
    
    output = nodes.new("ShaderNodeOutputMaterial")
    
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_color.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_bump.inputs['Vector'])
    
    links.new(tex_color.outputs['Color'], bsdf.inputs['Base Color'])
    
    links.new(tex_bump.outputs['Color'], bump_node.inputs['Height'])
    links.new(bump_node.outputs['Normal'], bsdf.inputs['Normal'])
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_material_neptune():
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

    try: sat_img = bpy.data.images.load(tex(PLANET_TEXTURES["Neptune"]["map"]))
    except: sat_img = None
    if sat_img:
        s_tex.image = sat_img
        sl.new(s_tex.outputs["Color"], s_gamma.inputs["Color"])
        s_gamma.inputs["Gamma"].default_value = 1.15
        sl.new(s_gamma.outputs["Color"], s_bsdf.inputs["Base Color"])
    else:
        s_bsdf.inputs["Base Color"].default_value = (0.1, 0.3, 0.8, 1) 

    s_bsdf.inputs["Roughness"].default_value   = 0.5
    s_bsdf.inputs["Specular"].default_value    = 0.2
    s_bsdf.inputs["Metallic"].default_value    = 0.0

    s_fres.inputs["IOR"].default_value         = 1.25
    s_emit.inputs["Color"].default_value       = (0.2, 0.5, 1.0, 1) 
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
    return sm

def create_material_pluto():
    sm = bpy.data.materials.new("Pluto_Mat")
    sm.use_nodes = True
    sn = sm.node_tree.nodes
    sl = sm.node_tree.links
    sn.clear()

    s_out   = sn.new("ShaderNodeOutputMaterial")
    s_bsdf  = sn.new("ShaderNodeBsdfPrincipled")
    s_tex   = sn.new("ShaderNodeTexImage")
    s_bump  = sn.new("ShaderNodeBump")

    s_bsdf.inputs["Roughness"].default_value   = 0.95
    s_bsdf.inputs["Specular"].default_value    = 0.02
    s_bsdf.inputs["Metallic"].default_value    = 0.0

    try: img = bpy.data.images.load(tex(PLANET_TEXTURES["Pluto"]["map"]))
    except: img = None
    if img:
        s_tex.image = img
        sl.new(s_tex.outputs["Color"], s_bsdf.inputs["Base Color"])
        
        sl.new(s_tex.outputs["Color"], s_bump.inputs["Height"])
        s_bump.inputs["Strength"].default_value = 0.1
        sl.new(s_bump.outputs["Normal"], s_bsdf.inputs["Normal"])
    else:
        s_bsdf.inputs["Base Color"].default_value = (0.7, 0.6, 0.5, 1) 

    sl.new(s_bsdf.outputs["BSDF"], s_out.inputs["Surface"])
    return sm

def create_material_saturn():
    sm = bpy.data.materials.new("Saturn_Mat")
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

    try: sat_img = bpy.data.images.load(tex(PLANET_TEXTURES["Saturn"]["map"]))
    except: sat_img = None
    if sat_img:
        s_tex.image = sat_img
        sl.new(s_tex.outputs["Color"], s_gamma.inputs["Color"])
        s_gamma.inputs["Gamma"].default_value = 1.15
        sl.new(s_gamma.outputs["Color"], s_bsdf.inputs["Base Color"])
    else:
        s_bsdf.inputs["Base Color"].default_value = (0.8, 0.7, 0.5, 1)

    s_bsdf.inputs["Roughness"].default_value   = 0.6
    s_bsdf.inputs["Specular"].default_value    = 0.1
    s_bsdf.inputs["Metallic"].default_value    = 0.0

    s_fres.inputs["IOR"].default_value         = 1.10
    s_emit.inputs["Color"].default_value       = (0.9, 0.8, 0.5, 1) 
    s_emit.inputs["Strength"].default_value    = 0.2  

    sl.new(s_fres.outputs["Fac"], s_mix.inputs["Fac"])
    sl.new(s_bsdf.outputs["BSDF"], s_mix.inputs[1])
    sl.new(s_emit.outputs["Emission"], s_mix.inputs[2])

    sl.new(s_bsdf.outputs["BSDF"], s_add.inputs[0])
    sl.new(s_emit.outputs["Emission"], s_add.inputs[1])

    s_mix2 = sn.new("ShaderNodeMixShader")
    s_mix2.inputs["Fac"].default_value = 0.15
    sl.new(s_bsdf.outputs["BSDF"],  s_mix2.inputs[1])
    sl.new(s_emit.outputs["Emission"], s_mix2.inputs[2])
    sl.new(s_fres.outputs["Fac"],   s_mix2.inputs["Fac"])
    sl.new(s_mix2.outputs["Shader"], s_out.inputs["Surface"])
    return sm

def create_material_saturn_rings():
    rm = bpy.data.materials.new("Saturn_Rings_Mat")
    rm.use_nodes = True
    rm.blend_method = "HASHED"
    rm.shadow_method = "HASHED"
    rn = rm.node_tree.nodes
    rl = rm.node_tree.links
    rn.clear()

    r_out  = rn.new("ShaderNodeOutputMaterial")
    r_bsdf = rn.new("ShaderNodeBsdfPrincipled")
    r_tex  = rn.new("ShaderNodeTexImage")

    try: ring_img = bpy.data.images.load(tex(PLANET_TEXTURES["Saturn"]["rings"]))
    except: ring_img = None
    if ring_img:
        r_tex.image = ring_img
        rl.new(r_tex.outputs["Color"], r_bsdf.inputs["Base Color"])
        rl.new(r_tex.outputs["Alpha"], r_bsdf.inputs["Alpha"])
    else:
        r_bsdf.inputs["Base Color"].default_value = (0.7, 0.6, 0.4, 1)
        r_bsdf.inputs["Alpha"].default_value = 0.5

    r_bsdf.inputs["Roughness"].default_value = 0.9
    r_bsdf.inputs["Specular"].default_value  = 0.0

    rl.new(r_bsdf.outputs["BSDF"], r_out.inputs["Surface"])
    return rm

def create_material_sun():
    mat = bpy.data.materials.new(name="Sun_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    tex_image1 = nodes.new("ShaderNodeTexImage")
    try: tex_image1.image = bpy.data.images.load(tex(PLANET_TEXTURES["Sun"]["surface"]))
    except: pass
        
    tex_image2 = nodes.new("ShaderNodeTexImage")
    try:
        img2 = bpy.data.images.load(tex(PLANET_TEXTURES["Sun"]["map"]))
        try: img2.colorspace_settings.name = 'Non-Color'
        except: pass
        tex_image2.image = img2
    except: pass
        
    emission = nodes.new("ShaderNodeEmission")
    
    math_strength = nodes.new("ShaderNodeMath")
    math_strength.operation = 'MULTIPLY'
    math_strength.inputs[1].default_value = 5.0 
    
    output = nodes.new("ShaderNodeOutputMaterial")
    
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_image1.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_image2.inputs['Vector'])
    
    links.new(tex_image1.outputs['Color'], emission.inputs['Color'])
    
    links.new(tex_image2.outputs['Color'], math_strength.inputs[0])
    links.new(math_strength.outputs['Value'], emission.inputs['Strength'])
    
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    return mat

def create_material_uranus():
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

    try: sat_img = bpy.data.images.load(tex(PLANET_TEXTURES["Uranus"]["map"]))
    except: sat_img = None
    if sat_img:
        s_tex.image = sat_img
        sl.new(s_tex.outputs["Color"], s_gamma.inputs["Color"])
        s_gamma.inputs["Gamma"].default_value = 1.15
        sl.new(s_gamma.outputs["Color"], s_bsdf.inputs["Base Color"])
    else:
        s_bsdf.inputs["Base Color"].default_value = (0.5, 0.8, 0.9, 1)

    s_bsdf.inputs["Roughness"].default_value   = 0.5
    s_bsdf.inputs["Specular"].default_value    = 0.2
    s_bsdf.inputs["Metallic"].default_value    = 0.0

    s_fres.inputs["IOR"].default_value         = 1.15
    s_emit.inputs["Color"].default_value       = (0.7, 0.9, 1.0, 1) 
    s_emit.inputs["Strength"].default_value    = 0.2  

    sl.new(s_fres.outputs["Fac"], s_mix.inputs["Fac"])
    sl.new(s_bsdf.outputs["BSDF"], s_mix.inputs[1])
    sl.new(s_emit.outputs["Emission"], s_mix.inputs[2])

    sl.new(s_bsdf.outputs["BSDF"], s_add.inputs[0])
    sl.new(s_emit.outputs["Emission"], s_add.inputs[1])

    s_mix2 = sn.new("ShaderNodeMixShader")
    s_mix2.inputs["Fac"].default_value = 0.15
    sl.new(s_bsdf.outputs["BSDF"],  s_mix2.inputs[1])
    sl.new(s_emit.outputs["Emission"], s_mix2.inputs[2])
    sl.new(s_fres.outputs["Fac"],   s_mix2.inputs["Fac"])
    sl.new(s_mix2.outputs["Shader"], s_out.inputs["Surface"])
    return sm

def create_material_uranus_rings():
    rm = bpy.data.materials.new("Uranus_Rings_Mat")
    rm.use_nodes = True
    rm.blend_method = "BLEND"
    rm.shadow_method = "HASHED"
    rm.use_backface_culling = False
    rn = rm.node_tree.nodes
    rl = rm.node_tree.links
    rn.clear()

    r_out  = rn.new("ShaderNodeOutputMaterial")
    r_bsdf = rn.new("ShaderNodeBsdfPrincipled")
    r_tex  = rn.new("ShaderNodeTexImage")
    alpha_mult = rn.new("ShaderNodeMath")
    alpha_mult.operation = 'MULTIPLY'
    alpha_mult.inputs[1].default_value = 0.35

    try: ring_img = bpy.data.images.load(tex(PLANET_TEXTURES["Uranus"]["rings"]))
    except: ring_img = None
    if ring_img:
        r_tex.image = ring_img
        r_tex.extension = 'EXTEND'
        r_tex.interpolation = 'Cubic'
        rl.new(r_tex.outputs["Color"], r_bsdf.inputs["Base Color"])
        rl.new(r_tex.outputs["Alpha"], alpha_mult.inputs[0])
        rl.new(alpha_mult.outputs["Value"], r_bsdf.inputs["Alpha"])
    else:
        r_bsdf.inputs["Base Color"].default_value = (0.62, 0.72, 0.82, 1)
        r_bsdf.inputs["Alpha"].default_value = 0.35

    r_bsdf.inputs["Roughness"].default_value = 0.75
    r_bsdf.inputs["Specular"].default_value  = 0.12

    rl.new(r_bsdf.outputs["BSDF"], r_out.inputs["Surface"])
    return rm

def create_material_venus():
    mat = bpy.data.materials.new(name="Venus_Surface_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    tex_surface = nodes.new("ShaderNodeTexImage")
    try: tex_surface.image = bpy.data.images.load(tex(PLANET_TEXTURES["Venus"]["surface"]))
    except: pass
    
    # Cloud texture (will be mixed with surface to preserve surface detail)
    tex_clouds = nodes.new("ShaderNodeTexImage")
    try:
        img_c = bpy.data.images.load(tex(PLANET_TEXTURES["Venus"]["clouds"]))
        tex_clouds.image = img_c
    except: pass
    
    tex_bump = nodes.new("ShaderNodeTexImage")
    try:
        img_b = bpy.data.images.load(tex(PLANET_TEXTURES["Venus"]["surface"]))
        try: img_b.colorspace_settings.name = 'Non-Color'
        except: pass
        tex_bump.image = img_b
    except: pass
    
    bump_node = nodes.new("ShaderNodeBump")
    bump_node.inputs['Strength'].default_value = 0.6
    bump_node.inputs['Distance'].default_value = 0.05
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.95
    bsdf.inputs['Specular'].default_value = 0.02
    
    output = nodes.new("ShaderNodeOutputMaterial")
    
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_surface.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_clouds.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_bump.inputs['Vector'])
    
    # Mix surface and clouds so the cloud cover doesn't completely obscure the radar surface
    mix_node = nodes.new("ShaderNodeMixRGB")
    mix_node.inputs['Fac'].default_value = 0.32
    links.new(tex_surface.outputs['Color'], mix_node.inputs[1])
    links.new(tex_clouds.outputs['Color'], mix_node.inputs[2])
    links.new(mix_node.outputs['Color'], bsdf.inputs['Base Color'])
    
    links.new(tex_bump.outputs['Color'], bump_node.inputs['Height'])
    links.new(bump_node.outputs['Normal'], bsdf.inputs['Normal'])
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_material_venus_clouds():
    mat = bpy.data.materials.new(name="Venus_Clouds_Material")
    mat.use_nodes = True
    mat.blend_method = 'HASHED'
    mat.shadow_method = 'HASHED'
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    tex_clouds = nodes.new("ShaderNodeTexImage")
    try: 
        img_clouds = bpy.data.images.load(tex(PLANET_TEXTURES["Venus"]["clouds"]))
        try: img_clouds.colorspace_settings.name = 'Non-Color'
        except: pass
        tex_clouds.image = img_clouds
    except: pass
    
    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.color_ramp.elements[0].position = 0.05
    color_ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    color_ramp.color_ramp.elements[1].position = 0.7
    color_ramp.color_ramp.elements[1].color = (1, 0.9, 0.7, 1)
    
    alpha_mult = nodes.new("ShaderNodeMath")
    alpha_mult.operation = 'MULTIPLY'
    alpha_mult.inputs[1].default_value = 0.55

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Base Color'].default_value = (0.9, 0.8, 0.6, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.9
    bsdf.inputs['Specular'].default_value = 0.0
    
    output = nodes.new("ShaderNodeOutputMaterial")
    
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_clouds.inputs['Vector'])
    
    links.new(tex_clouds.outputs['Color'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], alpha_mult.inputs[0])
    links.new(alpha_mult.outputs['Value'], bsdf.inputs['Alpha'])
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_material_generic(name, color):
    mat = bpy.data.materials.new(name=f"{name}_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
    return mat


def create_material_spacecraft_metal():
    mat = bpy.data.materials.new(name="Spacecraft_Metal_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    
    # Metal base properties
    bsdf.inputs["Base Color"].default_value = (0.75, 0.78, 0.82, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.95
    bsdf.inputs["Roughness"].default_value = 0.2
    bsdf.inputs["Specular"].default_value = 0.5
    
    # Procedural panel lines
    tex_coord = nodes.new("ShaderNodeTexCoord")
    voronoi_panels = nodes.new("ShaderNodeTexVoronoi")
    voronoi_panels.feature = 'DISTANCE_TO_EDGE'
    voronoi_panels.inputs["Scale"].default_value = 35.0  # size of panels
    
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.3
    bump.inputs["Distance"].default_value = 0.015
    
    links.new(tex_coord.outputs["Object"], voronoi_panels.inputs["Vector"])
    links.new(voronoi_panels.outputs["Distance"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    
    # Procedural Windows (glowing cells)
    voronoi_windows = nodes.new("ShaderNodeTexVoronoi")
    voronoi_windows.inputs["Scale"].default_value = 55.0  # window density
    
    rgb_to_bw = nodes.new("ShaderNodeVectorMath")
    rgb_to_bw.operation = 'LENGTH'
    
    math_filter = nodes.new("ShaderNodeMath")
    math_filter.operation = 'GREATER_THAN'
    math_filter.inputs[1].default_value = 0.90  # Only 10% of cells will be glowing windows
    
    links.new(tex_coord.outputs["Object"], voronoi_windows.inputs["Vector"])
    links.new(voronoi_windows.outputs["Color"], rgb_to_bw.inputs[0])
    links.new(rgb_to_bw.outputs["Value"], math_filter.inputs[0])
    
    # Connect to emission
    bsdf.inputs["Emission"].default_value = (1.0, 0.8, 0.4, 1.0) # warm yellow windows
    links.new(math_filter.outputs["Value"], bsdf.inputs["Emission Strength"])
    
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def create_material_solar_panel():
    mat = bpy.data.materials.new(name="Solar_Panel_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    
    bsdf.inputs["Base Color"].default_value = (0.02, 0.06, 0.18, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.05
    bsdf.inputs["Specular"].default_value = 1.0
    
    # Solar cell grid
    tex_coord = nodes.new("ShaderNodeTexCoord")
    voronoi = nodes.new("ShaderNodeTexVoronoi")
    voronoi.feature = 'DISTANCE_TO_EDGE'
    voronoi.inputs["Scale"].default_value = 40.0
    
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    bump.inputs["Distance"].default_value = 0.01
    
    links.new(tex_coord.outputs["Object"], voronoi.inputs["Vector"])
    links.new(voronoi.outputs["Distance"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def create_material_nav_light(color, name):
    mat = bpy.data.materials.new(name=f"Nav_Light_{name}_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = color
    emit.inputs["Strength"].default_value = 15.0
    
    links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat

def create_material_comet_tail(name, color, emission_strength, depth, base_radius, end_radius, curve_x, warp_strength, noise_scale, radial_power=2.0, longitudinal_power=1.0, opacity_scale=1.0):
    mat = bpy.data.materials.new(name=f"{name}_Mat")
    mat.use_nodes = True
    mat.blend_method = 'HASHED'
    mat.shadow_method = 'NONE'
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Emission"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Emission Strength"].default_value = emission_strength
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Specular"].default_value = 0.0
    
    # Coordinates and Warping
    tex_coord = nodes.new("ShaderNodeTexCoord")
    
    # Noise for coordinate warping
    warp_noise = nodes.new("ShaderNodeTexNoise")
    warp_noise.inputs["Scale"].default_value = noise_scale
    warp_noise.inputs["Detail"].default_value = 3.0
    warp_noise.inputs["Roughness"].default_value = 0.5
    
    # Subtract 0.5 to center the noise
    sub_half = nodes.new("ShaderNodeVectorMath")
    sub_half.operation = 'SUBTRACT'
    sub_half.inputs[1].default_value = (0.5, 0.5, 0.5)
    
    # Scale by warp_strength
    scale_warp = nodes.new("ShaderNodeVectorMath")
    scale_warp.operation = 'SCALE'
    scale_warp.inputs["Scale"].default_value = warp_strength
    
    # Add warp to original coordinate
    add_warp = nodes.new("ShaderNodeVectorMath")
    add_warp.operation = 'ADD'
    
    # Separate XYZ of warped coordinate
    sep_obj = nodes.new("ShaderNodeSeparateXYZ")
    
    links.new(tex_coord.outputs["Object"], warp_noise.inputs["Vector"])
    links.new(warp_noise.outputs["Color"], sub_half.inputs[0])
    links.new(sub_half.outputs["Vector"], scale_warp.inputs[0])
    links.new(tex_coord.outputs["Object"], add_warp.inputs[0])
    links.new(scale_warp.outputs["Vector"], add_warp.inputs[1])
    links.new(add_warp.outputs["Vector"], sep_obj.inputs["Vector"])
    
    # Calculate d_norm = -Z / depth
    # Since Z runs from 0.0 (head) to -depth (tail end), d_norm ranges from 0.0 to 1.0
    neg_z = nodes.new("ShaderNodeMath")
    neg_z.operation = 'MULTIPLY'
    neg_z.inputs[1].default_value = -1.0
    links.new(sep_obj.outputs["Z"], neg_z.inputs[0])
    
    div_depth = nodes.new("ShaderNodeMath")
    div_depth.operation = 'DIVIDE'
    div_depth.inputs[1].default_value = depth
    links.new(neg_z.outputs["Value"], div_depth.inputs[0])
    
    # Clamp d_norm to [0, 1]
    clamp_d = nodes.new("ShaderNodeMath")
    clamp_d.operation = 'MINIMUM'
    clamp_d.inputs[1].default_value = 1.0
    links.new(div_depth.outputs["Value"], clamp_d.inputs[0])
    
    clamp_d_min = nodes.new("ShaderNodeMath")
    clamp_d_min.operation = 'MAXIMUM'
    clamp_d_min.inputs[1].default_value = 0.0
    links.new(clamp_d.outputs["Value"], clamp_d_min.inputs[0])
    
    # Calculate x_offset = curve_x * d_norm^2
    d_sq = nodes.new("ShaderNodeMath")
    d_sq.operation = 'MULTIPLY'
    links.new(clamp_d_min.outputs["Value"], d_sq.inputs[0])
    links.new(clamp_d_min.outputs["Value"], d_sq.inputs[1])
    
    x_off = nodes.new("ShaderNodeMath")
    x_off.operation = 'MULTIPLY'
    x_off.inputs[1].default_value = curve_x
    links.new(d_sq.outputs["Value"], x_off.inputs[0])
    
    # Calculate X_centered = X - x_offset
    x_cen = nodes.new("ShaderNodeMath")
    x_cen.operation = 'SUBTRACT'
    links.new(sep_obj.outputs["X"], x_cen.inputs[0])
    links.new(x_off.outputs["Value"], x_cen.inputs[1])
    
    # Calculate r = sqrt(X_centered^2 + Y^2)
    x_cen_sq = nodes.new("ShaderNodeMath")
    x_cen_sq.operation = 'MULTIPLY'
    links.new(x_cen.outputs["Value"], x_cen_sq.inputs[0])
    links.new(x_cen.outputs["Value"], x_cen_sq.inputs[1])
    
    y_sq = nodes.new("ShaderNodeMath")
    y_sq.operation = 'MULTIPLY'
    links.new(sep_obj.outputs["Y"], y_sq.inputs[0])
    links.new(sep_obj.outputs["Y"], y_sq.inputs[1])
    
    r_sq = nodes.new("ShaderNodeMath")
    r_sq.operation = 'ADD'
    links.new(x_cen_sq.outputs["Value"], r_sq.inputs[0])
    links.new(y_sq.outputs["Value"], r_sq.inputs[1])
    
    r_dist = nodes.new("ShaderNodeMath")
    r_dist.operation = 'SQRT'
    links.new(r_sq.outputs["Value"], r_dist.inputs[0])
    
    # Calculate R(Z) = base_radius + (end_radius - base_radius) * d_norm
    r_range = end_radius - base_radius
    r_growth = nodes.new("ShaderNodeMath")
    r_growth.operation = 'MULTIPLY'
    r_growth.inputs[1].default_value = r_range
    links.new(clamp_d_min.outputs["Value"], r_growth.inputs[0])
    
    rad_z = nodes.new("ShaderNodeMath")
    rad_z.operation = 'ADD'
    rad_z.inputs[1].default_value = base_radius
    links.new(r_growth.outputs["Value"], rad_z.inputs[0])
    
    # Calculate u = r / R(Z)
    u_val = nodes.new("ShaderNodeMath")
    u_val.operation = 'DIVIDE'
    links.new(r_dist.outputs["Value"], u_val.inputs[0])
    links.new(rad_z.outputs["Value"], u_val.inputs[1])
    
    # Radial Fade: (1.0 - u)^radial_power, clamped
    one_minus_u = nodes.new("ShaderNodeMath")
    one_minus_u.operation = 'SUBTRACT'
    one_minus_u.inputs[0].default_value = 1.0
    links.new(u_val.outputs["Value"], one_minus_u.inputs[1])
    
    clamp_u = nodes.new("ShaderNodeMath")
    clamp_u.operation = 'MAXIMUM'
    clamp_u.inputs[1].default_value = 0.0
    links.new(one_minus_u.outputs["Value"], clamp_u.inputs[0])
    
    radial_fade = nodes.new("ShaderNodeMath")
    radial_fade.operation = 'POWER'
    radial_fade.inputs[1].default_value = radial_power
    links.new(clamp_u.outputs["Value"], radial_fade.inputs[0])
    
    # Longitudinal Fade: (1.0 - d_norm)^longitudinal_power, clamped
    one_minus_d = nodes.new("ShaderNodeMath")
    one_minus_d.operation = 'SUBTRACT'
    one_minus_d.inputs[0].default_value = 1.0
    links.new(clamp_d_min.outputs["Value"], one_minus_d.inputs[1])
    
    long_fade = nodes.new("ShaderNodeMath")
    long_fade.operation = 'POWER'
    long_fade.inputs[1].default_value = longitudinal_power
    links.new(one_minus_d.outputs["Value"], long_fade.inputs[0])
    
    # Secondary Noise pattern to add wispy details inside the tail
    details_noise = nodes.new("ShaderNodeTexNoise")
    details_noise.inputs["Scale"].default_value = noise_scale * 2.0
    details_noise.inputs["Detail"].default_value = 2.0
    details_noise.inputs["Roughness"].default_value = 0.6
    links.new(tex_coord.outputs["Object"], details_noise.inputs["Vector"])
    
    # Remap noise details from [0, 1] to [0.3, 1.0] so it doesn't punch holes but makes it wispy
    noise_remap = nodes.new("ShaderNodeMapRange")
    noise_remap.inputs["From Min"].default_value = 0.0
    noise_remap.inputs["From Max"].default_value = 1.0
    noise_remap.inputs["To Min"].default_value = 0.3
    noise_remap.inputs["To Max"].default_value = 1.0
    links.new(details_noise.outputs["Fac"], noise_remap.inputs["Value"])
    
    # Multiply radial_fade * long_fade
    fade_mult = nodes.new("ShaderNodeMath")
    fade_mult.operation = 'MULTIPLY'
    links.new(radial_fade.outputs["Value"], fade_mult.inputs[0])
    links.new(long_fade.outputs["Value"], fade_mult.inputs[1])
    
    # Multiply by noise details
    opacity_with_noise = nodes.new("ShaderNodeMath")
    opacity_with_noise.operation = 'MULTIPLY'
    links.new(fade_mult.outputs["Value"], opacity_with_noise.inputs[0])
    links.new(noise_remap.outputs["Result"], opacity_with_noise.inputs[1])
    
    # Multiply by overall opacity scale
    final_opacity = nodes.new("ShaderNodeMath")
    final_opacity.operation = 'MULTIPLY'
    final_opacity.inputs[1].default_value = opacity_scale
    links.new(opacity_with_noise.outputs["Value"], final_opacity.inputs[0])
    
    # Connect output
    links.new(final_opacity.outputs["Value"], bsdf.inputs["Alpha"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    
    return mat

def create_material_asteroid():
    mat = bpy.data.materials.new(name="Asteroid_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.28, 0.24, 0.22, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.95
        bsdf.inputs["Specular"].default_value = 0.02
        bsdf.inputs["Metallic"].default_value = 0.0
    return mat

def add_cylinder(name, radius, depth, location=(0,0,0), rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return obj

def add_cone(name, radius, depth, location=(0,0,0), rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(radius1=radius, radius2=0.0, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return obj

def add_cube(name, scale_size, location=(0,0,0), rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale_size
    return obj

def extrude_face(bm, face, distance=0.0):
    res = bmesh.ops.extrude_discrete_faces(bm, faces=[face])
    new_face = res['faces'][0]
    bmesh.ops.translate(bm, vec=new_face.normal * distance, verts=new_face.verts)
    return new_face

def scale_face(bm, face, scale_factor):
    center = face.calc_center_bounds()
    for v in face.verts:
        v.co = center + (v.co - center) * scale_factor

def build_satellite(name):
    metal_mat = create_material_spacecraft_metal()
    panel_mat = create_material_solar_panel()
    red_light = create_material_nav_light((1, 0, 0, 1), f"{name}_Red")

    me = bpy.data.meshes.new(name)
    bm = bmesh.new()

    bmesh.ops.create_cube(bm, size=0.08)
    
    for face in bm.faces[:]:
        if not face.is_valid:
            continue
        n = face.normal
        if n.y > 0.5: # Front face
            f = extrude_face(bm, face, 0.03)
            scale_face(bm, f, 0.7)
            f = extrude_face(bm, f, 0.015)
            scale_face(bm, f, 2.2)
            f = extrude_face(bm, f, 0.005)
            f.material_index = 0
        elif n.y < -0.5: # Rear face
            f = extrude_face(bm, face, 0.02)
            scale_face(bm, f, 0.6)
            f.material_index = 1
        elif abs(n.x) > 0.5: # Side faces
            f = extrude_face(bm, face, 0.04)
            scale_face(bm, f, 0.4)
            f = extrude_face(bm, f, 0.01)
            center = f.calc_center_bounds()
            for v in f.verts:
                v.co.z = center.z + (v.co.z - center.z) * 0.2
            
            f = extrude_face(bm, f, 0.12)
            f.material_index = 1
            for edge in f.edges:
                for lf in edge.link_faces:
                    if lf != f:
                        lf.material_index = 1
                        
            light_face = extrude_face(bm, f, 0.008)
            scale_face(bm, light_face, 0.5)
            light_face.material_index = 2

    for face in bm.faces:
        if face.material_index != 1 and face.material_index != 2:
            face.material_index = 0

    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)

    obj.data.materials.append(metal_mat)
    obj.data.materials.append(panel_mat)
    obj.data.materials.append(red_light)

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    
    # Scale down to be believable relative to Earth
    obj.scale = (0.12, 0.12, 0.12)
    return obj

def build_space_station(name):
    metal_mat = create_material_spacecraft_metal()
    panel_mat = create_material_solar_panel()
    red_light = create_material_nav_light((1, 0, 0, 1), f"{name}_Red")

    me = bpy.data.meshes.new(name)
    bm = bmesh.new()

    bmesh.ops.create_cube(bm, size=0.04)
    for v in bm.verts:
        v.co.y *= 8.0
        v.co.x *= 0.5
        v.co.z *= 0.5

    for face in bm.faces[:]:
        if not face.is_valid:
            continue
        center = face.calc_center_bounds()
        if abs(center.y) < 0.05 and abs(face.normal.x) > 0.5:
            h = extrude_face(bm, face, 0.05)
            scale_face(bm, h, 1.2)
            h = extrude_face(bm, h, 0.06)
            
            node_face = h
            if node_face and node_face.is_valid:
                n_f = extrude_face(bm, node_face, 0.03)
                scale_face(bm, n_f, 1.3)
                n_f = extrude_face(bm, n_f, 0.04)
                scale_face(bm, n_f, 0.7)

    for face in bm.faces[:]:
        if not face.is_valid:
            continue
        center = face.calc_center_bounds()
        if abs(face.normal.y) > 0.8:
            m = extrude_face(bm, face, 0.03)
            scale_face(bm, m, 0.6)
            
            wing = extrude_face(bm, m, 0.01)
            for v in wing.verts:
                v.co.y = wing.calc_center_bounds().y
                
            for v in wing.verts:
                v.co.x *= 6.0
                v.co.z *= 0.15
                
            top_face = None
            bottom_face = None
            for wf in bm.faces:
                if wf.normal.z > 0.8 and (wf.calc_center_bounds() - wing.calc_center_bounds()).length < 0.05:
                    top_face = wf
                elif wf.normal.z < -0.8 and (wf.calc_center_bounds() - wing.calc_center_bounds()).length < 0.05:
                    bottom_face = wf
            
            if top_face:
                p1 = extrude_face(bm, top_face, 0.25)
                p1.material_index = 1
                for edge in p1.edges:
                    for lf in edge.link_faces:
                        lf.material_index = 1
            if bottom_face:
                p2 = extrude_face(bm, bottom_face, 0.25)
                p2.material_index = 1
                for edge in p2.edges:
                    for lf in edge.link_faces:
                        lf.material_index = 1

    for face in bm.faces:
        if face.material_index != 1:
            face.material_index = 0

    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)

    obj.data.materials.append(metal_mat)
    obj.data.materials.append(panel_mat)
    obj.data.materials.append(red_light)

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()

    # Scale down to be believable relative to Earth
    obj.scale = (0.2, 0.2, 0.2)
    return obj

def build_space_shuttle(name):
    metal_mat = create_material_spacecraft_metal()
    dark_mat = create_material_solar_panel()
    white_light = create_material_nav_light((1, 1, 1, 1), f"{name}_White")

    me = bpy.data.meshes.new(name)
    bm = bmesh.new()

    bmesh.ops.create_cube(bm, size=0.06)
    
    for v in bm.verts:
        v.co.y *= 2.0

    front_face = None
    rear_face = None
    side_faces = []
    top_faces = []
    
    for face in bm.faces[:]:
        n = face.normal
        if n.y > 0.5:
            front_face = face
        elif n.y < -0.5:
            rear_face = face
        elif abs(n.x) > 0.5:
            side_faces.append(face)
        elif n.z > 0.5:
            top_faces.append(face)

    if front_face:
        f = extrude_face(bm, front_face, 0.05)
        scale_face(bm, f, 0.7)
        f = extrude_face(bm, f, 0.04)
        scale_face(bm, f, 0.4)
        f = extrude_face(bm, f, 0.02)
        scale_face(bm, f, 0.1)
        
    for sf in side_faces:
        if not sf.is_valid:
            continue
        w = extrude_face(bm, sf, 0.02)
        center = w.calc_center_bounds()
        for v in w.verts:
            v.co.z = center.z + (v.co.z - center.z) * 0.15
        
        w = extrude_face(bm, w, 0.12)
        scale_face(bm, w, 0.5)
        bmesh.ops.translate(bm, vec=Vector((0, -0.06, 0)), verts=w.verts)

    for tf in top_faces:
        if not tf.is_valid:
            continue
        t = extrude_face(bm, tf, 0.015)
        scale_face(bm, t, 0.5)
        t = extrude_face(bm, t, 0.06)
        scale_face(bm, t, 0.3)
        bmesh.ops.translate(bm, vec=Vector((0, -0.04, 0.02)), verts=t.verts)

    if rear_face and rear_face.is_valid:
        r = extrude_face(bm, rear_face, 0.01)
        scale_face(bm, r, 0.8)
        n1 = extrude_face(bm, r, 0.02)
        scale_face(bm, n1, 0.6)
        n1.material_index = 1

    for face in bm.faces:
        if face.material_index == 0:
            if face.normal.z > 0.3 and face.normal.y > 0.3:
                face.material_index = 1
            else:
                face.material_index = 0

    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)

    obj.data.materials.append(metal_mat)
    obj.data.materials.append(dark_mat)
    obj.data.materials.append(white_light)

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()

    bevel_modifier = obj.modifiers.new('Bevel', 'BEVEL')
    bevel_modifier.width = 15.0
    bevel_modifier.offset_type = 'PERCENT'
    bevel_modifier.segments = 2
    bevel_modifier.profile = 0.25

    # Scale down to be believable relative to Earth
    obj.scale = (0.1, 0.1, 0.1)
    return obj

def build_interplanetary_spacecraft(name):
    metal_mat = create_material_spacecraft_metal()
    panel_mat = create_material_solar_panel()
    red_light = create_material_nav_light((1, 0, 0, 1), f"{name}_Red")
    green_light = create_material_nav_light((0, 1, 0, 1), f"{name}_Green")

    me = bpy.data.meshes.new(name)
    bm = bmesh.new()

    bmesh.ops.create_cube(bm, size=0.06)
    for v in bm.verts:
        v.co.y *= 3.0
        v.co.x *= 0.8
        v.co.z *= 0.8

    front_face = None
    rear_face = None
    side_faces = []
    
    for face in bm.faces[:]:
        n = face.normal
        if n.y > 0.5:
            front_face = face
        elif n.y < -0.5:
            rear_face = face
        elif abs(n.x) > 0.5 or abs(n.z) > 0.5:
            side_faces.append(face)

    if front_face:
        f = extrude_face(bm, front_face, 0.03)
        scale_face(bm, f, 0.7)
        f = extrude_face(bm, f, 0.02)
        f = extrude_face(bm, f, 0.01)
        scale_face(bm, f, 2.5)
        f = extrude_face(bm, f, 0.005)
        f.material_index = 0

    if rear_face:
        r = extrude_face(bm, rear_face, 0.02)
        scale_face(bm, r, 0.7)
        r = extrude_face(bm, r, 0.02)
        scale_face(bm, r, 0.5)
        r.material_index = 1

    for face in side_faces:
        if not face.is_valid:
            continue
        center = face.calc_center_bounds()
        if abs(center.y) < 0.04:
            is_x_aligned = abs(face.normal.x) > 0.5
            
            f = extrude_face(bm, face, 0.03)
            scale_face(bm, f, 0.5)
            f = extrude_face(bm, f, 0.006)
            
            if is_x_aligned:
                for v in f.verts:
                    v.co.z = f.calc_center_bounds().z + (v.co.z - f.calc_center_bounds().z) * 0.15
            else:
                for v in f.verts:
                    v.co.x = f.calc_center_bounds().x + (v.co.x - f.calc_center_bounds().x) * 0.15
            
            f = extrude_face(bm, f, 0.14)
            f.material_index = 1
            for edge in f.edges:
                for lf in edge.link_faces:
                    lf.material_index = 1

            l = extrude_face(bm, f, 0.008)
            scale_face(bm, l, 0.5)
            l.material_index = 2

    for face in bm.faces:
        if face.material_index != 1 and face.material_index != 2:
            face.material_index = 0

    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)

    obj.data.materials.append(metal_mat)
    obj.data.materials.append(panel_mat)
    obj.data.materials.append(red_light)

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()

    # Scale down to be believable in the solar system
    obj.scale = (0.15, 0.15, 0.15)
    return obj

def build_space_probe(name):
    metal_mat = create_material_spacecraft_metal()
    dark_mat = create_material_solar_panel()
    red_light = create_material_nav_light((1, 0.2, 0.2, 1), f"{name}_Red")

    me = bpy.data.meshes.new(name)
    bm = bmesh.new()

    bmesh.ops.create_cube(bm, size=0.05)
    
    front_face = None
    rear_face = None
    side_faces = []
    
    for face in bm.faces[:]:
        n = face.normal
        if n.y > 0.5:
            front_face = face
        elif n.y < -0.5:
            rear_face = face
        else:
            side_faces.append(face)

    if front_face:
        f = extrude_face(bm, front_face, 0.02)
        scale_face(bm, f, 0.6)
        f = extrude_face(bm, f, 0.015)
        scale_face(bm, f, 3.5)
        f = extrude_face(bm, f, 0.008)
        
        center_face = extrude_face(bm, f, -0.004)
        scale_face(bm, center_face, 0.15)
        boom = extrude_face(bm, center_face, 0.06)
        scale_face(bm, boom, 0.4)
        sub_dish = extrude_face(bm, boom, 0.008)
        scale_face(bm, sub_dish, 2.5)

    for idx, face in enumerate(side_faces):
        if not face.is_valid:
            continue
        if idx == 0:
            b = extrude_face(bm, face, 0.02)
            scale_face(bm, b, 0.2)
            b = extrude_face(bm, b, 0.22)
            scale_face(bm, b, 0.5)
            b.material_index = 0
        elif idx == 1:
            b = extrude_face(bm, face, 0.02)
            scale_face(bm, b, 0.3)
            b = extrude_face(bm, b, 0.12)
            scale_face(bm, b, 1.2)
            b.material_index = 1
        elif idx == 2:
            b = extrude_face(bm, face, 0.02)
            scale_face(bm, b, 0.4)
            b = extrude_face(bm, b, 0.04)
            scale_face(bm, b, 1.4)
            b.material_index = 0
            lens = extrude_face(bm, b, 0.01)
            scale_face(bm, lens, 0.3)
            lens.material_index = 2

    for face in bm.faces:
        if face.material_index != 1 and face.material_index != 2:
            face.material_index = 0

    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)

    obj.data.materials.append(metal_mat)
    obj.data.materials.append(dark_mat)
    obj.data.materials.append(red_light)

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()

    # Scale down to be believable in the solar system
    obj.scale = (0.12, 0.12, 0.12)
    return obj

def build_asteroid(name, radius):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=12, ring_count=12)
    ast = bpy.context.active_object
    ast.name = name
    
    for v in ast.data.vertices:
        v.co.x += (v.co.x * random.uniform(-0.16, 0.16))
        v.co.y += (v.co.y * random.uniform(-0.16, 0.16))
        v.co.z += (v.co.z * random.uniform(-0.16, 0.16))
        
    bpy.ops.object.shade_smooth()
    ast_mat = create_material_asteroid()
    assign_material(ast, ast_mat)
    return ast

def create_material_comet_coma(name="Comet_Coma", radius=0.075):
    mat = bpy.data.materials.new(name=f"{name}_Mat")
    mat.use_nodes = True
    mat.blend_method = 'HASHED'
    mat.shadow_method = 'NONE'
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.8, 0.94, 1.0, 1.0)
    bsdf.inputs["Emission"].default_value = (0.8, 0.94, 1.0, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 25.0
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Specular"].default_value = 0.0
    
    # 3D spherical radial distance with noise warping
    tex_coord = nodes.new("ShaderNodeTexCoord")
    
    # Noise for warping coordinates
    warp_noise = nodes.new("ShaderNodeTexNoise")
    warp_noise.inputs["Scale"].default_value = 15.0
    warp_noise.inputs["Detail"].default_value = 2.0
    warp_noise.inputs["Roughness"].default_value = 0.5
    
    sub_half = nodes.new("ShaderNodeVectorMath")
    sub_half.operation = 'SUBTRACT'
    sub_half.inputs[1].default_value = (0.5, 0.5, 0.5)
    
    scale_warp = nodes.new("ShaderNodeVectorMath")
    scale_warp.operation = 'SCALE'
    scale_warp.inputs["Scale"].default_value = 0.02 # Subtle warping to make it look organic
    
    add_warp = nodes.new("ShaderNodeVectorMath")
    add_warp.operation = 'ADD'
    
    # Distance from center in warped object coordinates
    vec_len = nodes.new("ShaderNodeVectorMath")
    vec_len.operation = 'LENGTH'
    
    # Divide by radius to get u in [0, 1]
    div_radius = nodes.new("ShaderNodeMath")
    div_radius.operation = 'DIVIDE'
    div_radius.inputs[1].default_value = radius
    
    # 1 - u
    one_minus_u = nodes.new("ShaderNodeMath")
    one_minus_u.operation = 'SUBTRACT'
    one_minus_u.inputs[0].default_value = 1.0
    
    # Clamp to positive
    clamp_u = nodes.new("ShaderNodeMath")
    clamp_u.operation = 'MAXIMUM'
    clamp_u.inputs[1].default_value = 0.0
    
    # Power for smoother falloff
    soft_fade = nodes.new("ShaderNodeMath")
    soft_fade.operation = 'POWER'
    soft_fade.inputs[1].default_value = 1.5  # Soft, dense center
    
    # Connect coordinates and warp
    links.new(tex_coord.outputs["Object"], warp_noise.inputs["Vector"])
    links.new(warp_noise.outputs["Color"], sub_half.inputs[0])
    links.new(sub_half.outputs["Vector"], scale_warp.inputs[0])
    links.new(tex_coord.outputs["Object"], add_warp.inputs[0])
    links.new(scale_warp.outputs["Vector"], add_warp.inputs[1])
    links.new(add_warp.outputs["Vector"], vec_len.inputs[0])
    
    # Calculate normalized distance and fade
    links.new(vec_len.outputs["Value"], div_radius.inputs[0])
    links.new(div_radius.outputs["Value"], one_minus_u.inputs[1])
    links.new(one_minus_u.outputs["Value"], clamp_u.inputs[0])
    links.new(clamp_u.outputs["Value"], soft_fade.inputs[0])
    
    # Connect output
    links.new(soft_fade.outputs["Value"], bsdf.inputs["Alpha"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    
    return mat

def build_curved_cone_mesh(name, base_radius, end_radius, depth, segments, curve_x):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    
    num_verts = 16
    z_start = 0.0
    z_step = -depth / segments
    
    # Create vertices for all rings
    rings = []
    for s in range(segments + 1):
        t = s / segments
        current_radius = base_radius + (end_radius - base_radius) * t
        x_offset = curve_x * (t ** 2)  # Quadratic sweep
        z_pos = z_start + z_step * t
        
        ring_verts = []
        for i in range(num_verts):
            angle = 2 * math.pi * i / num_verts
            x = x_offset + current_radius * math.cos(angle)
            y = current_radius * math.sin(angle)
            v = bm.verts.new((x, y, z_pos))
            ring_verts.append(v)
        rings.append(ring_verts)
        
    # Create quad faces between rings
    for s in range(segments):
        ring_current = rings[s]
        ring_next = rings[s + 1]
        for i in range(num_verts):
            i_next = (i + 1) % num_verts
            bm.faces.new((
                ring_current[i],
                ring_current[i_next],
                ring_next[i_next],
                ring_next[i]
            ))
            
    bm.to_mesh(me)
    bm.free()
    
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    return obj

def build_comet(name):
    # Nucleus: sphere with radius=0.06
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, segments=12, ring_count=12)
    nuc = bpy.context.active_object
    nuc.name = f"{name}_Nucleus"
    for v in nuc.data.vertices:
        v.co.x += (v.co.x * random.uniform(-0.18, 0.18))
        v.co.y += (v.co.y * random.uniform(-0.18, 0.18))
        v.co.z += (v.co.z * random.uniform(-0.18, 0.18))
    bpy.ops.object.shade_smooth()
    
    ast_mat = create_material_asteroid()
    assign_material(nuc, ast_mat)
    
    parent = create_empty(name)
    nuc.parent = parent
    
    # Glowing Coma (gas envelope around head)
    # radius 0.15, emission strength 25.0
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, segments=16, ring_count=16)
    coma = bpy.context.active_object
    coma.name = f"{name}_Coma"
    coma.parent = parent
    bpy.ops.object.shade_smooth()
    
    coma_mat = create_material_comet_coma(f"{name}_Coma", radius=0.15)
    assign_material(coma, coma_mat)
    
    # 1. Straight Gas/Ion Tail (Type I): blue-cyan
    # depth=9.0, base_radius=0.10, end_radius=0.6, curve_x=0.0
    gas_tail = build_curved_cone_mesh(f"{name}_Tail_Gas", base_radius=0.10, end_radius=0.6, depth=9.0, segments=16, curve_x=0.0)
    gas_tail.parent = parent
    gas_tail.location = (0, 0, 0)
    
    gas_tail_mat = create_material_comet_tail(
        name=f"{name}_Tail_Gas",
        color=(0.35, 0.75, 1.0), # vibrant icy cyan-blue
        emission_strength=12.0,
        depth=9.0,
        base_radius=0.10,
        end_radius=0.6,
        curve_x=0.0,
        warp_strength=0.03,
        noise_scale=3.0,
        radial_power=1.5,
        longitudinal_power=0.8,
        opacity_scale=1.5
    )
    assign_material(gas_tail, gas_tail_mat)
    
    # 2. Curved Dust Tail (Type II): warm yellowish-orange dust
    # depth=8.0, base_radius=0.12, end_radius=1.5, curve_x=-1.5
    dust_tail = build_curved_cone_mesh(f"{name}_Tail_Dust", base_radius=0.12, end_radius=1.5, depth=8.0, segments=16, curve_x=-1.5)
    dust_tail.parent = parent
    dust_tail.location = (0, 0, 0)
    
    dust_tail_mat = create_material_comet_tail(
        name=f"{name}_Tail_Dust",
        color=(0.98, 0.88, 0.72), # warm yellowish-orange dust
        emission_strength=6.0,
        depth=8.0,
        base_radius=0.12,
        end_radius=1.5,
        curve_x=-1.5,
        warp_strength=0.025,
        noise_scale=2.0,
        radial_power=1.3,
        longitudinal_power=0.7,
        opacity_scale=1.3
    )
    assign_material(dust_tail, dust_tail_mat)
    
    return parent


# ============================================================
# SECTION 3 – OBJECT HELPERS
# ============================================================
def add_uv_sphere(name, radius, location=(0, 0, 0), segments=64, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius, location=location,
        segments=segments, ring_count=rings)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return obj


def create_empty(name, location=(0, 0, 0)):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def create_torus_ring(name, radius, thickness, parent_obj, mat=None, alpha=None):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=radius,
        minor_radius=thickness,
        location=(0, 0, 0),
        major_segments=128,
        minor_segments=16
    )
    ring = bpy.context.active_object
    ring.name = name
    ring.parent = parent_obj
    bpy.ops.object.shade_smooth()
    # If alpha provided, create a thin translucent material similar to celestialbodies/neptune.py
    if alpha is not None:
        mat = bpy.data.materials.new(f"{name}_Mat")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        out = nodes.new("ShaderNodeOutputMaterial")
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")

        bsdf.inputs["Base Color"].default_value = (0.7, 0.8, 1.0, 1)
        bsdf.inputs["Roughness"].default_value = 1.0
        try:
            bsdf.inputs["Alpha"].default_value = alpha
        except Exception:
            pass

        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

        mat.blend_method = 'BLEND'
        mat.shadow_method = 'NONE'
        ring.data.materials.append(mat)
    else:
        if mat is not None:
            assign_material(ring, mat)
    return ring


def add_point_light(name, location, energy, radius=0.5, color=(1, 0.9, 0.7)):
    bpy.ops.object.light_add(type='POINT', location=location)
    light = bpy.context.active_object
    light.name = name
    light.data.energy       = energy
    light.data.color        = color
    light.data.shadow_soft_size = radius
    return light


def assign_material(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


# ============================================================
# SECTION 4 – PLANET DEFINITIONS
# ============================================================
# (name, radius, orbit_radius, orbital_period_frames,
#  self_rot_period_frames, axial_tilt_deg,
#  base_color_rgba, texture_filename)
PLANET_DATA = [
    # True relative size (Earth = 0.3)
    # Name, radius, orbit_r, orb_period_days, rot_period, axial_tilt, base_color, tex_filename
    ("Mercury", 0.11,  12,     88,   58,  0.03,  (0.6, 0.5, 0.45, 1), "mercury_color.jpg"),
    ("Venus",   0.28,  18,    225,  243,  177.4, (0.9, 0.8, 0.5,  1), "venus_surface.jpg"),
    ("Earth",   0.30,  25,    365,    1,   23.4, (0.2, 0.5, 0.9,  1), "earth_daymap.jpg"),
    ("Mars",    0.16,  34,    687,   1.03, 25.2, (0.8, 0.4, 0.2,  1), "mars_surface.jpg"),
    ("Jupiter", 3.36,  55,   4333,   0.41, 3.1,  (0.8, 0.7, 0.55, 1), "jupiter_map.jpg"),
    ("Saturn",  2.83,  80,  10759,   0.45, 26.7, (0.9, 0.85, 0.6, 1), "saturn_color.jpg"),
    ("Uranus",  1.20, 105,  30688,   0.72, 97.8, (0.5, 0.85, 0.9, 1), "uranus.jpg"),
    ("Neptune", 1.16, 125,  60182,   0.67, 28.3, (0.2, 0.4, 0.9,  1), "neptune_surface.jpg"),
    ("Pluto",   0.05, 150,  90560,   6.39, 122.5, (0.6, 0.5, 0.4,  1), "pluto_map.jpg"),
]

SUN_RADIUS = 8.0

# Global orbital speed multiplier (keeps relative speeds mathematically perfectly accurate)
SPEED_SCALE = 1.5

# Moons Configuration (proportional to host radius)
MOONS_DATA = {
    "Earth": [("Moon", 0.27, 3.0, 1.0, "Moon")],
    "Mars": [
        ("Phobos", 0.2, 1.5, 3.0, "Moon"), 
        ("Deimos", 0.15, 2.5, 1.5, "Moon")
    ],
    "Jupiter": [
        ("Io", 0.025, 1.5, 4.0, "Io"),
        ("Europa", 0.02, 2.0, 2.0, "Europa"),
        ("Ganymede", 0.035, 2.6, 1.0, "Ganymede"),
        ("Callisto", 0.032, 3.3, 0.5, "Callisto")
    ],
    "Saturn": [
        ("Titan", 0.25, 4.0, 2.0, "Moon"),
        ("Rhea", 0.15, 2.8, 3.0, "Moon"),
        ("Enceladus", 0.1, 1.8, 4.0, "Moon")
    ],
    "Uranus": [
        ("Titania", 0.2, 5.0, 2.0, "Moon"),
        ("Oberon", 0.18, 6.5, 1.0, "Moon"),
        ("Umbriel", 0.15, 3.5, 3.0, "Moon"),
        ("Ariel", 0.12, 2.5, 4.0, "Moon"),
        ("Miranda", 0.08, 1.5, 5.0, "Moon")
    ],
    "Neptune": [
        ("Triton", 0.2, 4.0, -2.0, "Moon"),
        ("Proteus", 0.1, 2.0, 4.0, "Moon"),
        ("Nereid", 0.08, 6.5, 1.0, "Moon"),
        ("Larissa", 0.05, 1.5, 5.0, "Moon")
    ],
    "Pluto": [
        ("Charon", 0.35, 3.5, 1.0, "Moon"),
        ("Styx", 0.1, 5.0, 2.0, "Moon"),
        ("Nix", 0.12, 6.5, 1.5, "Moon"),
        ("Kerberos", 0.11, 8.0, 2.5, "Moon"),
        ("Hydra", 0.15, 9.5, 3.0, "Moon")
    ]
}




# ============================================================
# SECTION 5 – BUILD SOLAR SYSTEM
# ============================================================
def build_solar_system():
    planets = {}

    # ----- SUN -----
    sun_obj = add_uv_sphere("Sun", SUN_RADIUS)
    sun_mat = create_material_sun()
    assign_material(sun_obj, sun_mat)

    # FIX 1: Sun mesh must NOT cast shadows.
    sun_obj.visible_shadow = False

    # Sun point light - extremely high intensity for high contrast realism
    # Restore a strong but reasonable point light so distant planets remain visible.
    # Energy tuned down from the original extreme value but high enough for Eevee.
    sun_light = add_point_light("SunLight", (0, 0, 0), energy=2000.0,
                                radius=SUN_RADIUS, color=(1.0, 0.95, 0.9))

    # FIX 2: Disable shadows on the point light.
    sun_light.data.use_shadow = False

    # Directional key light to highlight surface textures (soft, filmic)
    bpy.ops.object.light_add(type='SUN', rotation=(math.radians(-10), math.radians(0), math.radians(20)))
    key_sun = bpy.context.active_object
    key_sun.name = "KeySun"
    key_sun.data.energy = 3.0
    try:
        key_sun.data.angle = math.radians(0.5)
    except Exception:
        pass
    key_sun.data.color = (1.0, 0.95, 0.9)
    key_sun.data.use_shadow = True

    # FIX 3: Extend light cutoff so outer planets (Pluto r=150) stay lit.
    # Keep light effective to reach outer planets while avoiding overexposure
    sun_light.data.use_custom_distance = True
    sun_light.data.cutoff_distance     = 600.0

    # Ambient fill light (very weak, to maintain dark space but not pure black)
    bpy.ops.object.light_add(type='SUN', rotation=(math.radians(45), math.radians(45), 0))
    fill = bpy.context.active_object
    fill.name = "AmbientFill"
    fill.data.energy = 0.01
    fill.data.color = (0.3, 0.35, 0.5)
    fill.data.use_shadow = False
    
    # Subtle rim light style fill
    bpy.ops.object.light_add(type='SUN', rotation=(math.radians(-45), math.radians(-135), 0))
    fill2 = bpy.context.active_object
    fill2.name = "AmbientFill2"
    fill2.data.energy = 0.03
    fill2.data.color = (0.7, 0.8, 1.0)
    fill2.data.use_shadow = False

    # ----- PLANETS -----
    for (pname, prad, orbit_r, orb_period, rot_period,
         axial_tilt, base_color, tex_file) in PLANET_DATA:

        # Pivot empty at origin
        pivot = create_empty(f"{pname}_Pivot")

        if pname == "Pluto":
            # Tilt pivot Empty for Pluto to isolate rotation and prevent viewport wobble
            tilt_pivot = create_empty("Pluto_TiltPivot", location=(orbit_r, 0, 0))
            tilt_pivot.parent = pivot
            tilt_pivot.rotation_euler.y = math.radians(axial_tilt)
            tilt_pivot.rotation_euler.z = math.radians(15)
            
            planet = add_uv_sphere(pname, prad, location=(0, 0, 0))
            planet.parent = tilt_pivot
        else:
            # Planet sphere
            planet = add_uv_sphere(pname, prad, location=(orbit_r, 0, 0))
            planet.parent = pivot

            # Axial tilt
            planet.rotation_euler.x = math.radians(axial_tilt)

        # Material
        func_name = f"create_material_{pname.lower()}"
        if func_name in globals():
            mat = globals()[func_name]()
        else:
            mat = create_material_generic(pname, base_color)
            
        assign_material(planet, mat)

        # Per-planet subtle rim/fill light (low energy) to reveal texture edges.
        # Skip Mercury, Venus, Earth, Mars, and Pluto to prevent excessive shininess and glowing borders.
        if pname not in {"Mercury", "Venus", "Earth", "Mars", "Pluto"}:
            try:
                bpy.ops.object.light_add(type='POINT', location=(orbit_r + prad * 0.5, 0, prad * 0.3))
                rim = bpy.context.active_object
                rim.name = f"{pname}_Rim"
                rim.data.energy = 50.0
                rim.data.color = (1.0, 0.95, 0.9)
                rim.data.use_shadow = False
                rim.data.use_custom_distance = True
                rim.data.cutoff_distance = max(prad * 4.0, 5.0)
                rim.parent = planet
                rim.location = (prad * 0.5, 0, prad * 0.3)
            except Exception:
                pass

        planets[pname] = {"pivot": pivot, "planet": planet,
                          "orbit_r": orbit_r, "radius": prad, "axial_tilt": axial_tilt}

        # ----- EARTH CLOUDS -----
        if pname == "Earth":
            clouds = add_uv_sphere("Earth_Clouds", prad * 1.015, location=(orbit_r, 0, 0))
            clouds.parent = pivot
            clouds.rotation_euler.x = math.radians(axial_tilt)
            cloud_mat = create_material_clouds()
            assign_material(clouds, cloud_mat)
            planets["Earth_Clouds"] = {"pivot": pivot, "planet": clouds, "orbit_r": orbit_r, "radius": prad * 1.015, "axial_tilt": axial_tilt}

        # ----- VENUS CLOUDS -----
        if pname == "Venus":
            clouds = add_uv_sphere("Venus_Clouds", prad * 1.015, location=(orbit_r, 0, 0))
            clouds.parent = pivot
            clouds.rotation_euler.x = math.radians(axial_tilt)
            cloud_mat = create_material_venus_clouds()
            assign_material(clouds, cloud_mat)
            planets["Venus_Clouds"] = {"pivot": pivot, "planet": clouds, "orbit_r": orbit_r, "radius": prad * 1.015, "axial_tilt": axial_tilt}

    # ----- RINGS -----
    # Saturn Rings (NGON Circle)
    if "Saturn" in planets:
        sat_obj = planets["Saturn"]["planet"]
        sat_r = planets["Saturn"]["radius"]
        bpy.ops.mesh.primitive_circle_add(vertices=128, radius=sat_r * 2.2, fill_type="NGON", location=(0, 0, 0))
        ring = bpy.context.active_object
        ring.name = "Saturn_Ring"
        ring.parent = sat_obj
        bpy.ops.object.shade_smooth()
        ring_mat = create_material_saturn_rings()
        assign_material(ring, ring_mat)
        
    # Uranus Rings (NGON Circle)
    if "Uranus" in planets:
        ur_obj = planets["Uranus"]["planet"]
        ur_r = planets["Uranus"]["radius"]
        bpy.ops.mesh.primitive_circle_add(vertices=128, radius=ur_r * 2.2, fill_type="NGON", location=(0, 0, 0))
        ring = bpy.context.active_object
        ring.name = "Uranus_Ring"
        ring.parent = ur_obj
        bpy.ops.object.shade_smooth()
        ring_mat = create_material_uranus_rings()
        assign_material(ring, ring_mat)

    # Neptune Rings (5 delicate Torus rings)
    if "Neptune" in planets:
        nep_obj = planets["Neptune"]["planet"]
        nep_r = planets["Neptune"]["radius"]
        # Use delicate translucent rings (very low alpha) to match the neptune module
        create_torus_ring("Ring_1", nep_r * 1.5, 0.01, nep_obj, alpha=0.05)
        create_torus_ring("Ring_2", nep_r * 1.7, 0.01, nep_obj, alpha=0.06)
        create_torus_ring("Ring_3", nep_r * 1.9, 0.02, nep_obj, alpha=0.04)
        create_torus_ring("Ring_4", nep_r * 2.1, 0.01, nep_obj, alpha=0.05)
        create_torus_ring("Ring_Adams", nep_r * 2.3, 0.02, nep_obj, alpha=0.08)

    # ----- MOONS -----
    for host_name, moons_list in MOONS_DATA.items():
        if host_name in planets:
            host_info = planets[host_name]
            host_pivot = host_info["pivot"]
            host_r = host_info["radius"]
            host_orbit_r = host_info["orbit_r"]
            host_tilt = host_info["axial_tilt"]
            
            # Master pivot for moons to inherit the host's axial tilt but not its diurnal rotation
            moons_master = create_empty(f"{host_name}_Moons_Master", location=(host_orbit_r, 0, 0))
            moons_master.parent = host_pivot
            if host_name == "Pluto":
                moons_master.rotation_euler.y = math.radians(host_tilt)
                moons_master.rotation_euler.z = math.radians(15)
            else:
                moons_master.rotation_euler.x = math.radians(host_tilt)
            
            moon_count = len(moons_list)
            for moon_index, (m_name, rad_mult, dist_mult, rot_speed, tex_key) in enumerate(moons_list):
                m_rad = host_r * rad_mult
                m_dist = host_r * dist_mult
                # Keep Jupiter moons distributed (fixes clumping), but keep others centered.
                if host_name == "Jupiter":
                    start_phase_deg = (360.0 * moon_index) / moon_count if moon_count > 0 else 0.0
                else:
                    start_phase_deg = 0.0

                # Pluto is tiny in this scene scale; tighten moon distances for better framing.
                if host_name == "Pluto":
                    m_dist *= 0.6
                
                m_orbit_pivot = create_empty(f"{m_name}_Orbit_Pivot", location=(0, 0, 0))
                m_orbit_pivot.parent = moons_master
                m_orbit_pivot.rotation_euler.z = math.radians(start_phase_deg)
                
                # Create Moon
                m_obj = add_uv_sphere(m_name, m_rad, location=(m_dist, 0, 0))
                m_obj.parent = m_orbit_pivot
                
                m_mat = create_material_moon(m_name, tex_key)
                assign_material(m_obj, m_mat)
                
                # Register moon in planets dict for animating
                planets[m_name] = {
                    "pivot": m_orbit_pivot,
                    "planet": m_obj,
                    "rot_speed": rot_speed,
                    "start_phase_deg": start_phase_deg,
                    "is_moon": True
                }

    # ----- SATELLITE, SPACE SHUTTLE, SPACE STATION, DEBRIS (EARTH ORBIT) -----
    if "Earth" in planets:
        earth_info = planets["Earth"]
        earth_obj = earth_info["planet"]
        earth_pivot = earth_info["pivot"]
        
        # Satellite
        sat = build_satellite("Earth_Satellite")
        sat_orbit = create_empty("Earth_Satellite_Orbit", location=(25, 0, 0))
        sat_orbit.parent = earth_pivot
        sat.parent = sat_orbit
        sat.location = (0.7, 0, 0.2)
        planets["Earth_Satellite"] = {"pivot": sat_orbit, "planet": sat, "is_spacecraft": True}
        
        # Space Station
        iss = build_space_station("Earth_Space_Station")
        iss_orbit = create_empty("Earth_Space_Station_Orbit", location=(25, 0, 0))
        iss_orbit.parent = earth_pivot
        iss.parent = iss_orbit
        iss.location = (-0.45, 0.0, -0.2)
        planets["Earth_Space_Station"] = {"pivot": iss_orbit, "planet": iss, "is_spacecraft": True}
        
        # Space Shuttle (starts near Earth, departs)
        shuttle = build_space_shuttle("Earth_Space_Shuttle")
        shuttle_pivot = create_empty("Earth_Space_Shuttle_Pivot", location=(0, 0, 0))
        
        # Use Copy Location constraint to stay centered at Earth but world-aligned (non-rotating)
        c_loc = shuttle_pivot.constraints.new(type='COPY_LOCATION')
        c_loc.target = earth_obj
        
        shuttle.parent = shuttle_pivot
        shuttle.location = (0.4, -0.5, 0.15)
        planets["Earth_Space_Shuttle"] = {"pivot": shuttle_pivot, "planet": shuttle, "is_spacecraft": True, "radius": 0.05}
        
        # Space Debris (6 random metal chunks with individual pivots)
        debris_mat = create_material_solar_panel()
        for i in range(6):
            deb_pivot = create_empty(f"Earth_Debris_Pivot_{i}", location=(25, 0, 0))
            deb_pivot.parent = earth_pivot
            
            bpy.ops.mesh.primitive_cube_add(size=0.003)
            deb = bpy.context.active_object
            deb.name = f"Earth_Debris_{i}"
            deb.parent = deb_pivot
            
            rad_angle = math.radians(60 * i + random.uniform(-10, 10))
            dist = 0.5 + random.uniform(0.1, 0.4)
            deb.location = (dist * math.cos(rad_angle), dist * math.sin(rad_angle), random.uniform(-0.3, 0.3))
            assign_material(deb, debris_mat)
            
            planets[deb.name] = {
                "pivot": deb_pivot,
                "planet": deb,
                "orbit_speed": random.uniform(8.0, 20.0),
                "start_angle": rad_angle,
                "is_debris": True
            }

    # ----- INTERPLANETARY SPACECRAFT (Earth to Mars traveler) -----
    spacecraft = build_interplanetary_spacecraft("Interplanetary_Spacecraft")
    sc_pivot = create_empty("Interplanetary_Spacecraft_Pivot", location=(0, 0, 0))
    spacecraft.parent = sc_pivot
    planets["Interplanetary_Spacecraft"] = {"pivot": sc_pivot, "planet": spacecraft, "is_spacecraft": True}

    # ----- DEEP-SPACE PROBE (Voyager style to Saturn) -----
    probe = build_space_probe("Saturn_Probe")
    probe_pivot = create_empty("Saturn_Probe_Pivot", location=(0, 0, 0))
    probe.parent = probe_pivot
    planets["Saturn_Probe"] = {"pivot": probe_pivot, "planet": probe, "is_spacecraft": True}

    # ----- ASTEROID BELT (80 irregular asteroids Mars-Jupiter) -----
    for i in range(80):
        ast_r = random.uniform(42.0, 48.0)
        ast_size = random.uniform(0.02, 0.065)
        ast_pivot = create_empty(f"Asteroid_Pivot_{i}")
        ast_mesh = build_asteroid(f"Asteroid_{i}", ast_size)
        ast_mesh.parent = ast_pivot
        ast_mesh.location = (ast_r, 0, 0)
        
        start_phase = random.uniform(0, 360)
        ast_pivot.rotation_euler.z = math.radians(start_phase)
        
        planets[f"Asteroid_{i}"] = {
            "pivot": ast_pivot,
            "planet": ast_mesh,
            "orbit_r": ast_r,
            "start_phase": start_phase,
            "is_asteroid": True,
            "radius": ast_size
        }

    # ----- COMETS (Eccentric elliptical orbit comets) -----
    comet1 = build_comet("Comet_Halley")
    comet1_pivot = create_empty("Comet_Halley_Pivot")
    comet1.parent = comet1_pivot
    # Track Sun with both Gas and Dust tails
    for suffix in ["Tail_Gas", "Tail_Dust"]:
        t_obj = bpy.data.objects.get(f"Comet_Halley_{suffix}")
        if t_obj and sun_obj:
            c_track = t_obj.constraints.new(type='TRACK_TO')
            c_track.target = sun_obj
            c_track.track_axis = 'TRACK_Z'
            c_track.up_axis = 'UP_Y'
    tail1 = bpy.data.objects.get("Comet_Halley_Tail_Gas")
    planets["Comet_Halley"] = {"pivot": comet1_pivot, "planet": comet1, "is_comet": True, "tail": tail1}
    
    comet2 = build_comet("Comet_Neowise")
    comet2_pivot = create_empty("Comet_Neowise_Pivot")
    comet2.parent = comet2_pivot
    # Track Sun with both Gas and Dust tails
    for suffix in ["Tail_Gas", "Tail_Dust"]:
        t_obj = bpy.data.objects.get(f"Comet_Neowise_{suffix}")
        if t_obj and sun_obj:
            c_track = t_obj.constraints.new(type='TRACK_TO')
            c_track.target = sun_obj
            c_track.track_axis = 'TRACK_Z'
            c_track.up_axis = 'UP_Y'
    tail2 = bpy.data.objects.get("Comet_Neowise_Tail_Gas")
    planets["Comet_Neowise"] = {"pivot": comet2_pivot, "planet": comet2, "is_comet": True, "tail": tail2}

    # ----- DWARF PLANETS (Beyond Neptune) -----
    for name, r, period, color in [("Eris", 170.0, 100000, (0.5, 0.55, 0.65, 1)), 
                                   ("Makemake", 185.0, 110000, (0.7, 0.5, 0.45, 1))]:
        ast_pivot = create_empty(f"{name}_Pivot")
        ast_mesh = add_uv_sphere(name, 0.055, location=(r, 0, 0))
        ast_mesh.parent = ast_pivot
        
        mat = create_material_generic(name, color)
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Roughness"].default_value = 0.95
            bsdf.inputs["Specular"].default_value = 0.02
        assign_material(ast_mesh, mat)
        
        planets[name] = {
            "pivot": ast_pivot,
            "planet": ast_mesh,
            "orbit_r": r,
            "is_dwarf": True,
            "orb_period": period
        }

    return planets


# ============================================================
# SECTION 5b – ORBIT LINES
# ============================================================
def add_orbit_lines():
    """Draw a faint emissive circle at each planet's orbital radius."""

    mat = bpy.data.materials.new("Orbit_Line_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out  = nodes.new("ShaderNodeOutputMaterial"); out.location  = (400, 0)
    emit = nodes.new("ShaderNodeEmission");        emit.location = (100, 0)
    emit.inputs["Color"].default_value    = (0.4, 0.6, 1.0, 1.0)
    emit.inputs["Strength"].default_value = 0.7  # Below bloom threshold to prevent bright glowing
    
    # We add a Mix Shader to animate opacity
    trans = nodes.new("ShaderNodeBsdfTransparent"); trans.location = (100, 100)
    mix = nodes.new("ShaderNodeMixShader"); mix.location = (250, 50)
    mix.name = "OrbitFadeMix"
    mix.inputs[0].default_value = 1.0 # 0 = transparent, 1 = emission
    
    links.new(trans.outputs["BSDF"], mix.inputs[1])
    links.new(emit.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])

    mat.blend_method  = "BLEND"
    mat.shadow_method = "NONE"

    ORBIT_SEGMENTS = 256

    for (pname, prad, orbit_r, *_rest) in PLANET_DATA:
        curve_data = bpy.data.curves.new(name=f"Orbit_{pname}", type='CURVE')
        curve_data.dimensions          = '3D'
        curve_data.resolution_u        = 12
        curve_data.render_resolution_u = 24
        curve_data.bevel_depth         = 0.014  # Physically thicker so they don't vanish from afar without bloom
        curve_data.use_fill_caps       = True

        spline = curve_data.splines.new('POLY')
        spline.use_cyclic_u = True
        spline.points.add(ORBIT_SEGMENTS - 1)

        for i, pt in enumerate(spline.points):
            angle = (2 * math.pi * i) / ORBIT_SEGMENTS
            pt.co = (
                orbit_r * math.cos(angle),
                orbit_r * math.sin(angle),
                0.0,
                1.0
            )

        orbit_obj = bpy.data.objects.new(f"Orbit_{pname}", curve_data)
        bpy.context.collection.objects.link(orbit_obj)
        orbit_obj.data.materials.append(mat)


# ============================================================
# SECTION 6 – ANIMATION
# ============================================================
def animate_solar_system(planets, blocks=None):
    scene = bpy.context.scene
    scene.frame_set(1)

    # Degrees per frame for self rotation (based on celestialbodies/*.py)
    ROT_SPEEDS = {
        "Sun": (360 * 2) / 300.0,
        "Mercury": 360.0 / 300.0,
        "Venus": (-360 * 4.0) / 300.0,
        "Earth": (360 * 5) / 300.0,
        "Mars": (360 * 5) / 300.0,
        "Jupiter": (360 * 15) / 300.0,
        "Saturn": (360 * 15) / 300.0,
        "Uranus": (360 * 15) / 300.0,
        "Neptune": (360 * 15) / 300.0,
        "Pluto": (360 * 2) / 300.0,
    }

    for pname, info in planets.items():
        if info.get("is_moon"):
            # It's a moon - animate its pivot (orbiting the host)
            pivot = info["pivot"]
            rot_speed = info["rot_speed"]
            start_phase_deg = info.get("start_phase_deg", 0.0)
            deg_per_frame = (360.0 * rot_speed) / 300.0
            
            pivot.rotation_euler.z = math.radians(start_phase_deg)
            pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
            pivot.rotation_euler.z = math.radians(start_phase_deg + (deg_per_frame * FRAME_END))
            pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=FRAME_END)
            
            for fcurve in pivot.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'LINEAR'
            continue
            
        if "Clouds" in pname:
            continue  # Handled inside host planet block
            
        pivot = info.get("pivot")
        planet = info.get("planet")
        
        if not pivot or not planet:
            continue

        # Orbit data
        found_data = next((d for d in PLANET_DATA if d[0] == pname), None)
        if not found_data:
            continue
            
        orb_period = found_data[3]
        axial_tilt = found_data[5]

        # ---- Orbital rotation (pivot Z-axis) ----
        deg_per_frame = 360.0 / (orb_period / SPEED_SCALE)

        pivot.rotation_euler = (0, 0, 0)
        pivot.keyframe_insert(data_path="rotation_euler", frame=1)
        total_degrees = deg_per_frame * FRAME_END
        pivot.rotation_euler.z = math.radians(total_degrees)
        pivot.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)

        for fcurve in pivot.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'LINEAR'

        # ---- Self-rotation (planet Z-axis, respecting X-axis tilt) ----
        planet.rotation_mode = 'XYZ'
        base_deg_per_frame = ROT_SPEEDS.get(pname, 1.0)

        # Ensure rotation direction respects axial tilt (retrograde if tilt > 90°)
        try:
            if axial_tilt > 90 and base_deg_per_frame > 0:
                base_deg_per_frame = -base_deg_per_frame
            elif axial_tilt <= 90 and base_deg_per_frame < 0:
                base_deg_per_frame = abs(base_deg_per_frame)
        except Exception:
            pass

        # If camera showcase blocks provided, slow rotation during that planet's showcase
        # Keep Venus rotating dynamically (85% speed) so clockwise motion is not cancelled by camera orbit
        current_slowdown = 0.85 if pname == "Venus" else 0.15
        showcase_start = None
        showcase_end = None
        if blocks:
            for (bname, bstart, bend) in blocks:
                if bname == pname:
                    showcase_start = bstart
                    showcase_end = bend
                    break

        # Base keyframe at frame 1
        x_rot = 0.0 if pname == "Pluto" else math.radians(axial_tilt)
        planet.rotation_euler = (x_rot, 0, 0)
        planet.keyframe_insert(data_path="rotation_euler", frame=1)

        if showcase_start and showcase_end:
            # Rotation before focus
            deg_before = base_deg_per_frame * (showcase_start - 1)
            planet.rotation_euler = (x_rot, 0, math.radians(deg_before))
            planet.keyframe_insert(data_path="rotation_euler", frame=showcase_start)

            # Rotation during focus
            deg_during = base_deg_per_frame * current_slowdown * (showcase_end - showcase_start)
            planet.rotation_euler = (x_rot, 0, math.radians(deg_before + deg_during))
            planet.keyframe_insert(data_path="rotation_euler", frame=showcase_end)

            # Rotation after focus (resume base speed)
            deg_after = base_deg_per_frame * (FRAME_END - showcase_end)
            total_deg = deg_before + deg_during + deg_after
            planet.rotation_euler = (x_rot, 0, math.radians(total_deg))
            planet.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)
        else:
            # No showcase block — keep uniform rotation across whole timeline
            planet.rotation_euler = (x_rot, 0, math.radians(base_deg_per_frame * FRAME_END))
            planet.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)

        if planet.animation_data and planet.animation_data.action:
            for fcurve in planet.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'LINEAR'
                
        # ---- Clouds Rotation ----
        if pname == "Earth" and "Earth_Clouds" in planets:
            clouds = planets["Earth_Clouds"]["planet"]
            clouds.rotation_mode = 'XYZ'

            # Keep cloud layer visually coupled to Earth by using the same timing curve,
            # with only a tiny speed offset so clouds still feel alive.
            cloud_speed_factor = 1.03

            clouds.rotation_euler = (math.radians(axial_tilt), 0, 0)
            clouds.keyframe_insert(data_path="rotation_euler", frame=1)

            if showcase_start and showcase_end:
                cloud_deg_before = base_deg_per_frame * cloud_speed_factor * (showcase_start - 1)
                clouds.rotation_euler = (math.radians(axial_tilt), 0, math.radians(cloud_deg_before))
                clouds.keyframe_insert(data_path="rotation_euler", frame=showcase_start)

                cloud_deg_during = base_deg_per_frame * cloud_speed_factor * current_slowdown * (showcase_end - showcase_start)
                clouds.rotation_euler = (math.radians(axial_tilt), 0, math.radians(cloud_deg_before + cloud_deg_during))
                clouds.keyframe_insert(data_path="rotation_euler", frame=showcase_end)

                cloud_deg_after = base_deg_per_frame * cloud_speed_factor * (FRAME_END - showcase_end)
                cloud_total_deg = cloud_deg_before + cloud_deg_during + cloud_deg_after
                clouds.rotation_euler = (math.radians(axial_tilt), 0, math.radians(cloud_total_deg))
                clouds.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)
            else:
                cloud_total_deg = base_deg_per_frame * cloud_speed_factor * FRAME_END
                clouds.rotation_euler = (math.radians(axial_tilt), 0, math.radians(cloud_total_deg))
                clouds.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)

            for fcurve in clouds.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'LINEAR'
                    
        if pname == "Venus" and "Venus_Clouds" in planets:
            clouds = planets["Venus_Clouds"]["planet"]
            clouds.rotation_mode = 'XYZ'

            # Use same speed ratio as base rotation: clouds are 1.125x faster than surface
            cloud_speed_factor = 1.125

            clouds.rotation_euler = (math.radians(axial_tilt), 0, 0)
            clouds.keyframe_insert(data_path="rotation_euler", frame=1)

            if showcase_start and showcase_end:
                cloud_deg_before = base_deg_per_frame * cloud_speed_factor * (showcase_start - 1)
                clouds.rotation_euler = (math.radians(axial_tilt), 0, math.radians(cloud_deg_before))
                clouds.keyframe_insert(data_path="rotation_euler", frame=showcase_start)

                cloud_deg_during = base_deg_per_frame * cloud_speed_factor * current_slowdown * (showcase_end - showcase_start)
                clouds.rotation_euler = (math.radians(axial_tilt), 0, math.radians(cloud_deg_before + cloud_deg_during))
                clouds.keyframe_insert(data_path="rotation_euler", frame=showcase_end)

                cloud_deg_after = base_deg_per_frame * cloud_speed_factor * (FRAME_END - showcase_end)
                cloud_total_deg = cloud_deg_before + cloud_deg_during + cloud_deg_after
                clouds.rotation_euler = (math.radians(axial_tilt), 0, math.radians(cloud_total_deg))
                clouds.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)
            else:
                cloud_total_deg = base_deg_per_frame * cloud_speed_factor * FRAME_END
                clouds.rotation_euler = (math.radians(axial_tilt), 0, math.radians(cloud_total_deg))
                clouds.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)

            for fcurve in clouds.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'LINEAR'

    # Sun slow self-rotation
    sun = bpy.data.objects.get("Sun")
    if sun:
        sun.rotation_mode = 'XYZ'
        sun.rotation_euler = (0, 0, 0)
        sun.keyframe_insert(data_path="rotation_euler", frame=1)
        sun.rotation_euler = (0, 0, math.radians(ROT_SPEEDS.get("Sun", 2.0) * FRAME_END))
        sun.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)
        for fcurve in sun.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'LINEAR'

    # Closing shot: ramp orbital speeds so Pluto completes one full revolution
    if globals().get('CLOSING_TRANS_END') and globals().get('CLOSING_END'):
        c_start = int(CLOSING_TRANS_END)
        c_end = int(CLOSING_END)
        closing_span = max(1, c_end - c_start)

        for pname, info in list(planets.items()):
            if info.get('is_moon'):
                continue
            pivot = info.get('pivot')
            if not pivot:
                continue

            found_data = next((d for d in PLANET_DATA if d[0] == pname), None)
            if not found_data:
                continue

            orb_period = found_data[3]
            try:
                deg_per_frame = 360.0 / (orb_period / SPEED_SCALE)
            except Exception:
                deg_per_frame = 0.0

            base_deg_at_cstart = deg_per_frame * c_start

            # Make the inner planets visibly orbit in the final wide pullback.
            # Outer planets get a smaller boost so the motion still feels balanced.
            orbit_boost = 1.0
            if pname == "Mercury":
                orbit_boost = 3.5
            elif pname == "Venus":
                orbit_boost = 3.0
            elif pname == "Earth":
                orbit_boost = 2.5
            elif pname == "Mars":
                orbit_boost = 2.0
            elif pname == "Jupiter":
                orbit_boost = 3.0
            elif pname == "Saturn":
                orbit_boost = 5.0
            elif pname == "Uranus":
                orbit_boost = 12.0
            elif pname == "Neptune":
                orbit_boost = 20.0
            elif pname == "Pluto":
                orbit_boost = 38.7

            # Insert keyframe at ramp start with current rotation
            pivot.rotation_euler.z = math.radians(base_deg_at_cstart)
            pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=c_start)

            # Insert keyframe at ramp end with extra rotation added.
            # The extra rotation scales with orbital speed so the motion stays readable.
            extra_deg = deg_per_frame * closing_span * orbit_boost
            pivot.rotation_euler.z = math.radians(base_deg_at_cstart + extra_deg)
            pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=c_end)

            # Smooth interpolation for the ramp segment
            if pivot.animation_data and pivot.animation_data.action:
                for fcurve in pivot.animation_data.action.fcurves:
                    if 'rotation_euler' in fcurve.data_path:
                        for kf in fcurve.keyframe_points:
                            kf.interpolation = 'BEZIER'

    # ----- ANIMATE ENHANCED SPACE OBJECTS -----
    # 1. Earth Satellite
    sat_info = planets.get("Earth_Satellite")
    if sat_info:
        sat_pivot = sat_info["pivot"]
        sat_pivot.rotation_euler.z = 0
        sat_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
        sat_pivot.rotation_euler.z = math.radians(360.0 * 20.0)
        sat_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=FRAME_END)
        for fcurve in sat_pivot.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'LINEAR'
                
    # 2. Earth Space Station
    iss_info = planets.get("Earth_Space_Station")
    if iss_info:
        iss_pivot = iss_info["pivot"]
        iss_pivot.rotation_euler.z = math.radians(180)
        iss_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
        iss_pivot.rotation_euler.z = math.radians(180.0 - 360.0 * 15.0)
        iss_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=FRAME_END)
        for fcurve in iss_pivot.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'LINEAR'

    # 3. Earth Space Shuttle (departs outward from Earth)
    shuttle_info = planets.get("Earth_Space_Shuttle")
    if shuttle_info:
        sh_pivot = shuttle_info["pivot"]
        sh_planet = shuttle_info["planet"]
        
        # Keep pivot non-rotating so its coordinates align with Earth's local space
        sh_pivot.rotation_euler = (0, 0, 0)
        
        # Flight path aligned with the camera view during showcase
        sh_planet.rotation_mode = 'XYZ'
        sh_planet.rotation_euler = (math.radians(15), 0, math.radians(-167))
        sh_planet.keyframe_insert(data_path="rotation_euler", frame=1)
        sh_planet.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)
        
        # Location offset (passing across the foreground of Earth showcase)
        sh_planet.location = (0.4, -0.5, 0.15)
        sh_planet.keyframe_insert(data_path="location", frame=1)
        sh_planet.location = (0.4, -0.5, 0.15)
        sh_planet.keyframe_insert(data_path="location", frame=540) # start of showcase
        
        sh_planet.location = (-0.5, -0.7, 0.4)
        sh_planet.keyframe_insert(data_path="location", frame=660) # end of showcase/start of departure
        
        # flies far away by frame 1200
        sh_planet.location = (-3.0, -2.0, 2.0)
        sh_planet.keyframe_insert(data_path="location", frame=1200)
        
        # deep space by FRAME_END
        sh_planet.location = (-10.0, -5.0, 5.0)
        sh_planet.keyframe_insert(data_path="location", frame=FRAME_END)
        for fcurve in sh_planet.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'BEZIER'

    # 4. Interplanetary Spacecraft (travels Earth to Mars)
    sc_info = planets.get("Interplanetary_Spacecraft")
    if sc_info:
        sc_pivot = sc_info["pivot"]
        sc_planet = sc_info["planet"]
        
        sc_planet.rotation_mode = 'XYZ'
        sc_planet.rotation_euler.y = 0
        sc_planet.keyframe_insert(data_path="rotation_euler", index=1, frame=1)
        sc_planet.rotation_euler.y = math.radians(360.0 * 5.0)
        sc_planet.keyframe_insert(data_path="rotation_euler", index=1, frame=FRAME_END)
        
        sc_pivot.location = (25.0, 4.0, 1.0) # near Earth
        sc_pivot.keyframe_insert(data_path="location", frame=1)
        
        sc_pivot.location = (29.0, 2.0, 0.5)
        sc_pivot.keyframe_insert(data_path="location", frame=620)
        
        # close approach Mars (Mars orbit = 34) at frame 720
        sc_pivot.location = (34.0, 0.8, 0.4)
        sc_pivot.keyframe_insert(data_path="location", frame=720)
        
        sc_pivot.location = (46.0, -4.0, -1.0)
        sc_pivot.keyframe_insert(data_path="location", frame=1200)
        
        sc_pivot.location = (65.0, -10.0, -2.5)
        sc_pivot.keyframe_insert(data_path="location", frame=FRAME_END)
        
        for fcurve in sc_pivot.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'BEZIER'

    # 5. Deep Space Probe (Voyager style to Saturn)
    probe_info = planets.get("Saturn_Probe")
    if probe_info:
        pr_pivot = probe_info["pivot"]
        pr_planet = probe_info["planet"]
        
        pr_planet.rotation_mode = 'XYZ'
        pr_planet.rotation_euler.y = 0
        pr_planet.keyframe_insert(data_path="rotation_euler", index=1, frame=1)
        pr_planet.rotation_euler.y = math.radians(360.0 * 2.0)
        pr_planet.keyframe_insert(data_path="rotation_euler", index=1, frame=FRAME_END)
        
        pr_pivot.location = (55.0, 15.0, 5.0) # starting beyond Jupiter
        pr_pivot.keyframe_insert(data_path="location", frame=1)
        pr_pivot.keyframe_insert(data_path="location", frame=600)
        
        # Sat encounter (Saturn orbit_r = 80)
        pr_pivot.location = (80.0, 1.4, 0.6)
        pr_pivot.keyframe_insert(data_path="location", frame=960)
        
        # flies past
        pr_pivot.location = (92.0, -6.0, -2.0)
        pr_pivot.keyframe_insert(data_path="location", frame=1500)
        
        pr_pivot.location = (120.0, -15.0, -5.0)
        pr_pivot.keyframe_insert(data_path="location", frame=FRAME_END)
        
        for fcurve in pr_pivot.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'BEZIER'

    # 6. Asteroid Belt Orbits
    for pname, info in planets.items():
        if info.get("is_asteroid"):
            ast_pivot = info["pivot"]
            ast_r = info["orbit_r"]
            start_phase = info["start_phase"]
            
            period = 2200.0 * (ast_r / 45.0)**1.5
            deg_per_frame = 360.0 / (period / SPEED_SCALE)
            
            ast_pivot.rotation_euler.z = math.radians(start_phase)
            ast_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
            
            total_deg = start_phase + deg_per_frame * FRAME_END
            ast_pivot.rotation_euler.z = math.radians(total_deg)
            ast_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=FRAME_END)
            
            for fcurve in ast_pivot.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'LINEAR'

    # 7. Comets Elliptical Animation
    c1_info = planets.get("Comet_Halley")
    if c1_info:
        c1_pivot = c1_info["pivot"]
        for f in range(1, FRAME_END + 1, 40):
            theta_deg = -120.0 + (f / FRAME_END) * 240.0
            theta = math.radians(theta_deg)
            r = 18.0 / (1.0 + 0.85 * math.cos(theta))
            c1_pivot.location = (r * math.cos(theta), r * math.sin(theta), 0.4 * math.sin(theta))
            c1_pivot.keyframe_insert(data_path="location", frame=f)
        
        if c1_pivot.animation_data and c1_pivot.animation_data.action:
            for fcurve in c1_pivot.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'BEZIER'
                    
    c2_info = planets.get("Comet_Neowise")
    if c2_info:
        c2_pivot = c2_info["pivot"]
        for f in range(1, FRAME_END + 1, 40):
            theta_deg = -150.0 + (f / FRAME_END) * 300.0
            theta = math.radians(theta_deg)
            r = 9.0 / (1.0 + 0.9 * math.cos(theta))
            loc_x = r * math.cos(theta + math.radians(45.0))
            loc_y = r * math.sin(theta + math.radians(45.0))
            loc_z = r * 0.35 * math.sin(theta)
            c2_pivot.location = (loc_x, loc_y, loc_z)
            c2_pivot.keyframe_insert(data_path="location", frame=f)
            
        if c2_pivot.animation_data and c2_pivot.animation_data.action:
            for fcurve in c2_pivot.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'BEZIER'

    # 8. Dwarf Planets
    for pname, info in planets.items():
        if info.get("is_dwarf"):
            ast_pivot = info["pivot"]
            period = info["orb_period"]
            deg_per_frame = 360.0 / (period / SPEED_SCALE)
            
            ast_pivot.rotation_euler.z = 0
            ast_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
            ast_pivot.rotation_euler.z = math.radians(deg_per_frame * FRAME_END)
            ast_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=FRAME_END)
            
            for fcurve in ast_pivot.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'LINEAR'

    # 9. Space Debris Orbits
    for pname, info in planets.items():
        if info.get("is_debris"):
            deb_pivot = info["pivot"]
            speed = info["orbit_speed"]
            
            deb_pivot.rotation_euler.z = 0
            deb_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
            deb_pivot.rotation_euler.z = math.radians(speed * FRAME_END)
            deb_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=FRAME_END)
            
            for fcurve in deb_pivot.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'LINEAR'

# ============================================================
# SECTION 7 – PLANET LABELS
# ============================================================
def add_planet_labels(planets, cam_obj, blocks):
    label_objects = {}

    for (pname, prad, orbit_r, orb_period, rot_period,
         axial_tilt, base_color, tex_file) in PLANET_DATA:

        planet = planets[pname]["planet"]
        pivot = planets[pname]["pivot"]
        
        # Adjust radius consideration for Saturn to account for its rings
        label_prad = prad * 2.5 if pname == "Saturn" else prad
        
        # 1. Create an Empty Rig to act as a billboard center
        billboard_rig = create_empty(f"LabelRig_{pname}", location=(orbit_r, 0, 0))
        
        # Parent to the pivot. It will follow the planet's orbit perfectly, 
        # but won't inherit the planet's spinning rotation!
        billboard_rig.parent = pivot
        
        # Rig always faces the camera (Z points to camera, Y points Up, X points Right)
        c_track = billboard_rig.constraints.new(type='TRACK_TO')
        c_track.target = cam_obj
        c_track.track_axis = 'TRACK_Z'
        c_track.up_axis = 'UP_Y'

        # 2. Create the Text Object
        bpy.ops.object.text_add(location=(0, 0, 0))
        txt_obj = bpy.context.active_object
        txt_obj.name = f"Label_{pname}"
        txt_obj.parent = billboard_rig

        # 3. Typography & Styling
        txt_obj.data.body = pname.upper()  # All caps
        txt_obj.data.size = label_prad * 0.35  # Strict proportional scale so all planets match visually
        txt_obj.data.align_x = 'LEFT'
        txt_obj.data.space_character = 1.4  # Cinematic letter spacing
        
        # Offset text strictly proportional to the planet's radius
        txt_obj.location = (label_prad * 1.3, label_prad * 0.2, 0)
        
        # Try to load a clean modern font (Windows standard)
        font_path = "C:\\Windows\\Fonts\\segoeuil.ttf"  # Segoe UI Light
        if not os.path.exists(font_path):
            font_path = "C:\\Windows\\Fonts\\arial.ttf"
            
        if os.path.exists(font_path):
            try:
                fnt = bpy.data.fonts.load(font_path)
                txt_obj.data.font = fnt
            except Exception:
                pass

        # 4. Material with clean, crisp text and animated transparency
        lmat = bpy.data.materials.new(f"Label_{pname}_Mat")
        lmat.use_nodes = True
        lmat.blend_method = 'BLEND'
        ln = lmat.node_tree.nodes
        ll = lmat.node_tree.links
        ln.clear()

        lout = ln.new("ShaderNodeOutputMaterial")
        lout.location = (400, 0)

        lbsdf = ln.new("ShaderNodeBsdfPrincipled")
        lbsdf.location = (0, 0)
        lbsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        lbsdf.inputs["Roughness"].default_value = 0.4
        lbsdf.inputs["Specular"].default_value = 0.0

        ltrans = ln.new("ShaderNodeBsdfTransparent")
        ltrans.location = (0, 100)

        lmix = ln.new("ShaderNodeMixShader")
        lmix.location = (200, 50)
        lmix.inputs[0].default_value = 0.0  # 0 = Transparent, 1 = Visible label

        ll.new(ltrans.outputs["BSDF"], lmix.inputs[1])
        ll.new(lbsdf.outputs["BSDF"], lmix.inputs[2])
        ll.new(lmix.outputs["Shader"], lout.inputs["Surface"])

        txt_obj.data.materials.append(lmat)

        # Store mix node to animate it later
        label_objects[pname] = {"obj": txt_obj, "mix_node": lmix}

    # 5. Animate visibility based on camera segments
    for idx, (pname, b_start, b_end) in enumerate(blocks):
        if pname not in label_objects:
            continue
        trans_end = b_start if idx == 0 else b_start + 40
        showcase_start = trans_end
        showcase_end = b_end

        fade_in_start = showcase_start
        fade_in_end = showcase_start + 20
        fade_out_start = showcase_end - 20
        fade_out_end = showcase_end

        mix_node = label_objects[pname]["mix_node"]

        # Keep transparent before fade in
        mix_node.inputs[0].default_value = 0.0
        mix_node.inputs[0].keyframe_insert(data_path="default_value", frame=1)
        mix_node.inputs[0].keyframe_insert(data_path="default_value", frame=fade_in_start)

        # Fade in
        mix_node.inputs[0].default_value = 1.0
        mix_node.inputs[0].keyframe_insert(data_path="default_value", frame=fade_in_end)

        # Hold
        mix_node.inputs[0].keyframe_insert(data_path="default_value", frame=fade_out_start)

        # Fade out
        mix_node.inputs[0].default_value = 0.0
        mix_node.inputs[0].keyframe_insert(data_path="default_value", frame=fade_out_end)

        # Apply bezier interpolation for smooth cinematic fade
        if mix_node.id_data.animation_data and mix_node.id_data.animation_data.action:
            for fcurve in mix_node.id_data.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'BEZIER'

    return label_objects


# ============================================================
# SECTION 8 – CAMERA SYSTEM
# ============================================================
def build_camera_system(planets):
    # 1. Create Rig Objects
    cam_target = create_empty("CameraTarget")
    cam_pivot = create_empty("CameraPivot")

    # 2. Create Camera
    bpy.ops.object.camera_add(location=(0, -250, 100))
    cam_obj = bpy.context.active_object
    cam_obj.name = "MainCamera"
    bpy.context.scene.camera = cam_obj

    # Parent Camera to Pivot
    cam_obj.parent = cam_pivot

    # Constraint Camera to Target
    track = cam_obj.constraints.new(type='TRACK_TO')
    track.target = cam_target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    # Keep labels sharp during focus shots by disabling depth-of-field blur.
    cam_data = cam_obj.data
    cam_data.lens = 50  # Cinematic 50mm lens
    cam_data.clip_start = 0.01
    cam_data.clip_end = 2000
    cam_data.dof.use_dof = False
    cam_data.dof.focus_object = cam_target
    cam_data.dof.aperture_fstop = 16.0
    
    # Offset camera slightly for rule-of-thirds framing
    cam_data.shift_x = 0.15

    # Slight camera tilt for realism
    cam_obj.rotation_euler.y = math.radians(2)

    # 3. Setup Target Constraints
    sun_obj = bpy.data.objects.get("Sun")

    c_sun_pivot = cam_pivot.constraints.new(type='COPY_LOCATION')
    c_sun_pivot.target = sun_obj
    c_sun_pivot.name = "Copy_Sun"

    c_sun_tgt = cam_target.constraints.new(type='COPY_LOCATION')
    c_sun_tgt.target = sun_obj
    c_sun_tgt.name = "Copy_Sun"

    # Setup constraints for planets
    for pname in PLANET_DATA:
        p_name = pname[0]
        planet_obj = planets[p_name]["planet"]

        cp = cam_pivot.constraints.new(type='COPY_LOCATION')
        cp.target = planet_obj
        cp.name = f"Copy_{p_name}"
        cp.influence = 0.0

        ct = cam_target.constraints.new(type='COPY_LOCATION')
        ct.target = planet_obj
        ct.name = f"Copy_{p_name}"
        ct.influence = 0.0

    # Setup constraints for custom camera targets
    custom_targets = ["Earth_Space_Shuttle", "Asteroid_0", "Interplanetary_Spacecraft", "Saturn_Probe", "Comet_Halley", "Comet_Neowise"]
    for p_name in custom_targets:
        if p_name in planets:
            target_obj = planets[p_name]["planet"]

            cp = cam_pivot.constraints.new(type='COPY_LOCATION')
            cp.target = target_obj
            cp.name = f"Copy_{p_name}"
            cp.influence = 0.0

            ct = cam_target.constraints.new(type='COPY_LOCATION')
            ct.target = target_obj
            ct.name = f"Copy_{p_name}"
            ct.influence = 0.0

    def keyframe_influence(target_name, frame, influence):
        """Helper to animate the target influence of the camera rig."""
        for obj in [cam_pivot, cam_target]:
            c = obj.constraints.get(f"Copy_{target_name}")
            if c:
                c.influence = influence
                c.keyframe_insert(data_path="influence", frame=frame)

    # 4. Animate Scene 1 – Overview
    keyframe_influence("Sun", 1, 1.0)
    for pname in PLANET_DATA:
        keyframe_influence(pname[0], 1, 0.0)
    for p_name in ["Earth_Space_Shuttle", "Asteroid_0", "Interplanetary_Spacecraft", "Saturn_Probe", "Comet_Halley", "Comet_Neowise"]:
        keyframe_influence(p_name, 1, 0.0)

    # Overview Camera Motion (Arc/Orbit, slow easing)
    cam_obj.location = (-60, -140, 100)
    cam_obj.keyframe_insert(data_path="location", frame=1)

    cam_obj.location = (50, -80, 60)
    cam_obj.keyframe_insert(data_path="location", frame=240)

    # Animate orbit lines fading out after the overview
    orbit_mat = bpy.data.materials.get("Orbit_Line_Mat")
    orbit_mix = orbit_mat.node_tree.nodes["OrbitFadeMix"] if orbit_mat else None

    if orbit_mix:
        orbit_mix.inputs[0].default_value = 1.0
        orbit_mix.inputs[0].keyframe_insert(data_path="default_value", frame=1)
        orbit_mix.inputs[0].keyframe_insert(data_path="default_value", frame=240)
        orbit_mix.inputs[0].default_value = 0.0
        orbit_mix.inputs[0].keyframe_insert(data_path="default_value", frame=300)

    # Hold Sun target until transition ends
    keyframe_influence("Sun", 300, 1.0)
    keyframe_influence("Sun", 301, 0.0)

    # 5. Define Timings
    blocks = [
        ("Mercury", 300, 420),
        ("Venus", 420, 540),
        ("Earth", 540, 660),
        ("Mars", 660, 780),
        ("Jupiter", 780, 900),
        ("Saturn", 900, 1020),
        ("Uranus", 1020, 1140),
        ("Neptune", 1140, 1260),
        ("Pluto", 1260, 1380),
    ]

    prev_target = "Sun"
    prev_end_frame = 240

    # 6. Animate Planet Showcases
    for idx, (pname, b_start, b_end) in enumerate(blocks):
        trans_start = prev_end_frame
        trans_end = b_start if idx == 0 else b_start + 40
        showcase_start = trans_end
        showcase_end = b_end

        # Keep previous target at 1.0 until transition ends
        keyframe_influence(prev_target, trans_end, 1.0)
        keyframe_influence(prev_target, trans_end + 1, 0.0)

        # Fade in new target
        keyframe_influence(pname, trans_start, 0.0)
        keyframe_influence(pname, trans_end, 1.0)
        keyframe_influence(pname, showcase_end, 1.0)

        prad = planets[pname]["radius"]
        
        # Pull camera back further for Saturn so the rings fit perfectly
        cam_prad = prad * 2.5 if pname == "Saturn" else prad

        # Local camera position (arc/orbital movement around planet)
        start_loc = (-cam_prad * 5, -cam_prad * 8, cam_prad * 4)
        cam_obj.location = start_loc
        cam_obj.keyframe_insert(data_path="location", frame=showcase_start)

        # Subtle arc and push-in during showcase
        end_loc = (cam_prad * 4, -cam_prad * 6, cam_prad * 2)
        cam_obj.location = end_loc
        cam_obj.keyframe_insert(data_path="location", frame=showcase_end)

        prev_target = pname
        prev_end_frame = showcase_end

    # 6b. Animate Final Scene - Zoom out to entire Solar System
    final_start = 1380
    final_mid = final_start + int((FRAME_END - final_start) * 0.45)
    final_end = FRAME_END

    # Expose closing timing so orbital animation can ramp up later.
    # The close-up starts after Pluto, then eases all the way to the end.
    global CLOSING_TRANS_END, CLOSING_END
    CLOSING_TRANS_END = final_start
    CLOSING_END = final_end

    # Crossfade from Pluto to the Sun over the full closing move.
    keyframe_influence(prev_target, final_start, 1.0)
    keyframe_influence(prev_target, final_end, 0.0)

    keyframe_influence("Sun", final_start, 0.0)
    keyframe_influence("Sun", final_end, 1.0)

    # Bring orbit lines back for the final overview
    if orbit_mix:
        orbit_mix.inputs[0].keyframe_insert(data_path="default_value", frame=final_start)
        orbit_mix.inputs[0].default_value = 1.0
        orbit_mix.inputs[0].keyframe_insert(data_path="default_value", frame=final_mid)
        orbit_mix.inputs[0].keyframe_insert(data_path="default_value", frame=final_end)
        
        # Smooth interpolation for orbit mix
        if orbit_mix.id_data.animation_data and orbit_mix.id_data.animation_data.action:
            for fcurve in orbit_mix.id_data.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'BEZIER'

    # Move camera from the Pluto close-up into a full-system view with the same camera.
    cam_obj.location = cam_obj.location
    cam_obj.keyframe_insert(data_path="location", frame=final_start)

    cam_obj.location = (0, -150, 95)
    cam_obj.keyframe_insert(data_path="location", frame=final_mid)

    cam_obj.location = (0, -240, 150)
    cam_obj.keyframe_insert(data_path="location", frame=final_end)

    # 7. Smoothing & Polish
    for obj in [cam_pivot, cam_target, cam_obj]:
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'BEZIER'

    # Add slight camera noise for realism
    if cam_obj.animation_data and cam_obj.animation_data.action:
        for fcurve in cam_obj.animation_data.action.fcurves:
            if fcurve.data_path == "location":
                mod = fcurve.modifiers.new(type='NOISE')
                mod.scale = 120.0
                mod.strength = 0.1  # Very subtle shake

    # Late closing title card, anchored to the camera so it sits in the bottom-right corner.
    title_obj = None
    bpy.ops.object.text_add(location=(0, 0, 0))
    title_obj = bpy.context.active_object
    title_obj.name = "ClosingTitle"
    title_obj.data.body = "THE SOLAR SYSTEM"
    # Place the title in camera-local space (bottom-right) and scale to match planet labels
    try:
        # Compute average label size from planet radii so title matches label scale
        avg_label_size = 0.0
        count = 0
        major_bodies = {p[0] for p in PLANET_DATA} | {"Earth_Clouds", "Venus_Clouds"}
        for p in planets:
            if p in major_bodies and "radius" in planets[p]:
                avg_label_size += planets[p]["radius"] * 0.35
                count += 1
        if count > 0:
            avg_label_size /= count
        else:
            avg_label_size = 0.12
        title_obj.data.size = avg_label_size * 1.0
    except Exception:
        # Fallback to a small readable size
        title_obj.data.size = 0.12
    title_obj.data.align_x = 'CENTER'
    try:
        title_obj.data.align_y = 'BOTTOM'
    except Exception:
        # Older Blender versions may not expose align_y; ignore if absent
        pass
    title_obj.data.space_character = 1.0
    title_obj.parent = cam_obj
    # Local coordinates relative to camera: centered horizontally, down, and in front
    title_obj.location = (0.0, -1.15, -6.0)
    title_obj.rotation_euler = (0.0, 0.0, 0.0)

    title_mat = bpy.data.materials.new("ClosingTitle_Mat")
    title_mat.use_nodes = True
    title_mat.blend_method = 'BLEND'
    title_nodes = title_mat.node_tree.nodes
    title_links = title_mat.node_tree.links
    title_nodes.clear()

    title_out = title_nodes.new("ShaderNodeOutputMaterial")
    title_bsdf = title_nodes.new("ShaderNodeBsdfPrincipled")
    title_trans = title_nodes.new("ShaderNodeBsdfTransparent")
    title_mix = title_nodes.new("ShaderNodeMixShader")
    title_bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    title_bsdf.inputs["Roughness"].default_value = 0.35
    title_bsdf.inputs["Specular"].default_value = 0.0
    title_mix.inputs[0].default_value = 0.0

    title_links.new(title_trans.outputs["BSDF"], title_mix.inputs[1])
    title_links.new(title_bsdf.outputs["BSDF"], title_mix.inputs[2])
    title_links.new(title_mix.outputs["Shader"], title_out.inputs["Surface"])

    title_obj.data.materials.append(title_mat)
    title_mix.inputs[0].keyframe_insert(data_path="default_value", frame=1)
    title_mix.inputs[0].default_value = 0.0
    title_mix.inputs[0].keyframe_insert(data_path="default_value", frame=2700)
    title_mix.inputs[0].default_value = 1.0
    title_mix.inputs[0].keyframe_insert(data_path="default_value", frame=2750)
    title_mix.inputs[0].keyframe_insert(data_path="default_value", frame=FRAME_END)

    if title_mix.id_data.animation_data and title_mix.id_data.animation_data.action:
        for fcurve in title_mix.id_data.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'BEZIER'

    return cam_obj, blocks


def set_linear_cycles(obj):
    if not (obj.animation_data and obj.animation_data.action):
        return
    for fc in obj.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'


def create_meteor_material():
    mat = bpy.data.materials.new("Meteor_Material")
    mat.use_nodes = True
    mat.blend_method = 'BLEND'
    mat.shadow_method = 'NONE'
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Specular"].default_value = 0.0
    # Clean, non-bright white base and emission
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Emission"].default_value = (1.0, 1.0, 1.0, 1.0)
    
    # Texture Coordinate -> Separate XYZ (Z channel represents length from tail to head)
    tex_coord = nodes.new("ShaderNodeTexCoord")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tex_coord.outputs["Generated"], separate.inputs["Vector"])
    
    # Color Ramp for Alpha transparency (tapered tail at tip, opaque head at base)
    alpha_ramp = nodes.new("ShaderNodeValToRGB")
    alpha_ramp.color_ramp.elements[0].position = 0.15
    alpha_ramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)  # Opaque front (base)
    alpha_ramp.color_ramp.elements[1].position = 1.0
    alpha_ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 0.0)  # Transparent tail (tip)
    links.new(separate.outputs["Z"], alpha_ramp.inputs["Fac"])
    links.new(alpha_ramp.outputs["Color"], bsdf.inputs["Alpha"])
    
    # Object Info node to read custom per-object brightness scale (stored in Object Color Red channel)
    obj_info = nodes.new("ShaderNodeObjectInfo")
    sep_color = nodes.new("ShaderNodeSeparateColor")
    links.new(obj_info.outputs["Color"], sep_color.inputs["Color"])
    
    # Multiply custom scale by base emission strength (kept low but visible against bright daylight)
    mult = nodes.new("ShaderNodeMath")
    mult.operation = 'MULTIPLY'
    mult.inputs[1].default_value = 5.0 # Low base strength
    links.new(sep_color.outputs["Red"], mult.inputs[0])
    links.new(mult.outputs["Value"], bsdf.inputs["Emission Strength"])
    
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def create_meteor_mesh(name):
    # Low-poly tapered cone representing meteor core and trail
    # Align along Z axis: base at bottom (trail end), tip at top (head core)
    bpy.ops.mesh.primitive_cone_add(
        vertices=8, radius1=1.0, radius2=0.0, depth=1.0, location=(0, 0, 0)
    )
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return obj

def add_meteor_system(planets, cam_obj):
    scene = bpy.context.scene
    met_mat = create_meteor_material()
    
    # Major planets to scatter shooting stars across
    planet_names = [d[0] for d in PLANET_DATA]
    
    # Timing windows for each planet close-up showcase
    blocks = {
        "Mercury": (300, 420),
        "Venus": (420, 540),
        "Earth": (540, 660),
        "Mars": (660, 780),
        "Jupiter": (780, 900),
        "Saturn": (900, 1020),
        "Uranus": (1020, 1140),
        "Neptune": (1140, 1260),
        "Pluto": (1260, 1380),
    }
    
    meteor_counter = 0
    
    for pname in planet_names:
        p_info = planets.get(pname)
        if not p_info:
            continue
            
        pivot = p_info["pivot"]
        planet_obj = p_info["planet"]
        prad = p_info["radius"]
        orbit_r = p_info["orbit_r"]
        
        # Create a local meteor system for this planet
        meteor_system = create_empty(f"{pname}_Meteor_System", location=(orbit_r, 0, 0))
        meteor_system.parent = pivot
        
        # Template mesh specifically for this planet
        base_mesh_obj = create_meteor_mesh(f"{pname}_Meteor_Template")
        base_mesh_obj.parent = meteor_system
        base_mesh_obj.hide_viewport = True
        base_mesh_obj.hide_render = True
        assign_material(base_mesh_obj, met_mat)
        
        # Schedule starts for this planet (scattered, not grouped together)
        scheduled_starts = []
        
        # 1. Showcase close-up window: Schedule 1 or 2 meteors
        window = blocks.get(pname)
        if window:
            b_start, b_end = window
            scheduled_starts.append(random.randint(b_start + 10, b_start + 50))
            if random.random() < 0.8:
                scheduled_starts.append(random.randint(b_start + 60, b_end - 15))
                
        # 2. Overview window (frames 1 to 240) - 25% chance per planet to keep it sparse/touring
        if random.random() < 0.25:
            scheduled_starts.append(random.randint(20, 220))
            
        # 3. Final zoom-out window (frames 1400 to 2900) - 50% chance per planet to keep it sparse/touring
        if random.random() < 0.5:
            scheduled_starts.append(random.randint(1400, 2900))
            
        for f_start in scheduled_starts:
            duration = random.randint(8, 16)
            f_end = f_start + duration
            if f_end >= FRAME_END:
                continue
                
            # Get camera direction relative to planet at f_start to bias visibility
            scene.frame_set(f_start)
            bpy.context.view_layer.update()
            p_loc = planet_obj.matrix_world.translation.copy()
            c_loc = cam_obj.matrix_world.translation.copy()
            dir_to_cam_world = (c_loc - p_loc).normalized()
            
            # Transform dir_to_cam_world to meteor_system local coordinates
            dir_to_cam = meteor_system.matrix_world.inverted().to_3x3() @ dir_to_cam_world
            dir_to_cam.normalize()
            
            # Generate two orthonormal vectors u_x and u_y perpendicular to dir_to_cam
            if abs(dir_to_cam.z) < 0.9:
                u_x = dir_to_cam.cross(Vector((0, 0, 1))).normalized()
            else:
                u_x = dir_to_cam.cross(Vector((1, 0, 0))).normalized()
            u_y = dir_to_cam.cross(u_x).normalized()
            
            # Choose a random travel direction angle in the plane perpendicular to the camera vector
            alpha = random.uniform(0, 2 * math.pi)
            dir_motion = math.cos(alpha) * u_x + math.sin(alpha) * u_y
            dir_offset = -math.sin(alpha) * u_x + math.cos(alpha) * u_y
            
            # Distance from planet center
            r = prad * random.uniform(1.3, 1.7)
            
            # Angle of offset relative to camera line of sight (0 = directly in front, 90 = on the limb)
            # We use 0 to 75 degrees so they can pass in front or skim the sides
            beta = random.uniform(0, math.radians(75))
            
            d_cam_offset = r * math.cos(beta)
            d_side_offset = r * math.sin(beta)
            
            p_center = d_cam_offset * dir_to_cam + d_side_offset * dir_offset
            
            # Length of travel path
            L_half = prad * random.uniform(0.7, 1.1)
            
            # Generate straight line path tangent to the planet (passing by/across it, not colliding)
            p_start = p_center - L_half * dir_motion
            p_end = p_center + L_half * dir_motion
            
            # Instantiate meteor by copying template mesh
            met = base_mesh_obj.copy()
            met.name = f"Meteor_{pname}_{meteor_counter}"
            meteor_counter += 1
            met.hide_viewport = False
            met.hide_render = False
            met.parent = meteor_system
            bpy.context.collection.objects.link(met)
            
            # Calculate rotation so it points base-first along path vector (using -Z tracking)
            path_vec = p_end - p_start
            rot_quat = path_vec.to_track_quat('-Z', 'Y')
            met.rotation_mode = 'QUATERNION'
            met.rotation_quaternion = rot_quat
            
            # Size proportional to host planet's radius (small and elegant)
            scale_xy = prad * random.uniform(0.04, 0.08)
            scale_z = prad * random.uniform(0.66, 1.16)
            brightness = 1.0 # Base intensity (multiplied by 2.0 in shader)
            
            met.color = (brightness, 0.0, 0.0, 1.0)
            
            # Animate location (Linear interpolation)
            met.location = p_start
            met.keyframe_insert(data_path="location", frame=f_start)
            met.location = p_end
            met.keyframe_insert(data_path="location", frame=f_end)
            
            # Animate scale (Fade in, shrink/burn up at end)
            met.scale = (0, 0, 0)
            met.keyframe_insert(data_path="scale", frame=f_start - 1)
            
            # Quick fade-in
            fade_in_frame = f_start + int(duration * 0.15)
            met.scale = (scale_xy, scale_xy, scale_z)
            met.keyframe_insert(data_path="scale", frame=fade_in_frame)
            
            # Burn out (taper down to 0)
            met.scale = (0, 0, 0)
            met.keyframe_insert(data_path="scale", frame=f_end)
            met.keyframe_insert(data_path="scale", frame=f_end + 1)
            
            # Set linear interpolation for clean constant speed
            set_linear_cycles(met)
            
            # Ensure scale channels are linear as well
            if met.animation_data and met.animation_data.action:
                for fc in met.animation_data.action.fcurves:
                    if "scale" in fc.data_path:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "LINEAR"


# ============================================================
# MAIN
# ============================================================
def main():
    print("=== Solar System Generator – Blender 3.6 ===")

    # 1. Scene
    print("[1/6] Setting up scene...")
    setup_scene()

    # 2. Build solar system objects + materials
    print("[2/6] Building planets and materials...")
    planets = build_solar_system()

    # 2b. Orbit lines
    print("[2b/6] Drawing orbit lines...")
    add_orbit_lines()

    # 3. Camera
    print("[3/6] Building camera animation...")
    cam_obj, blocks = build_camera_system(planets)

    # 4. Animate orbits / rotations (now that camera blocks exist so we can slow rotations when focused)
    print("[4/6] Animating orbits and rotations...")
    animate_solar_system(planets, blocks)

    # 5. Labels
    print("[5/6] Adding planet labels...")
    add_planet_labels(planets, cam_obj, blocks)

    # 5b. Shooting stars (Meteors) near Earth
    print("[5b/6] Adding shooting stars (meteor events) near Earth...")
    add_meteor_system(planets, cam_obj)

    # 6. Final scene housekeeping
    print("[6/6] Finalising scene...")
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

    print("=== Done! Press SPACE or render to see the animation. ===")


main()
