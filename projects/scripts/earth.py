import bpy
import os
import math
from mathutils import Vector

# ==============================================================================
# GLOBAL CONFIGURATION
# ==============================================================================

# Directory containing all the planet textures
TEXTURE_DIR = r"C:\COLLEGE\THIRD TERM\MAA\Planets\textures"

# Scale factor for physical sizing (1 Blender Unit = 1,000 km for this showcase)
EARTH_RADIUS = 6.37
MOON_RADIUS = 1.73

# We compress the Earth-Moon distance slightly for cinematic framing
MOON_DISTANCE = 25.0 

# Animation timeline configuration
TOTAL_FRAMES = 360

# For a majestic, cinematic showcase, we discard scientific relative speeds.
# We force Earth to 1 full rotation (slowest perfect loop) and the Moon to 1 full orbit
EARTH_ROTATIONS = 1.0
MOON_ROTATIONS = 1.0

PLANET_TEXTURES = {
    "Earth": {
        "day": "earth_daymap.jpg", 
        "night": "earth_nightmap.jpg", 
        "normal": "earth_normal_map.tif", 
        "specular": "earth_specular.jpg",
        "clouds": "earth_clouds.jpg"
    },
    "Moon": {
        "surface": "moon_surface.jpg", 
        "bump": "moon_bump.jpg"
    }
}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_texture_path(filename):
    """Returns the absolute path to a texture file."""
    path = os.path.join(TEXTURE_DIR, filename)
    if not os.path.exists(path):
        print(f"Warning: Texture '{filename}' not found in {TEXTURE_DIR}.")
    return path

def clear_scene():
    """Removes all objects, meshes, materials, and worlds from the current scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    for block in [bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.lights, bpy.data.cameras]:
        for item in block:
            block.remove(item)

def setup_collections():
    """Sets up the required collections for organization."""
    collections = ["EarthSystem", "Lighting", "Environment"]
    scene_collection = bpy.context.scene.collection
    for name in collections:
        if name not in bpy.data.collections:
            new_col = bpy.data.collections.new(name)
            scene_collection.children.link(new_col)

def link_to_collection(obj, collection_name):
    """Links an object to a specific collection and unlinks from the master scene collection."""
    if collection_name in bpy.data.collections:
        bpy.data.collections[collection_name].objects.link(obj)
        if obj.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(obj)

# ==============================================================================
# RENDERING, WORLD & LIGHTING
# ==============================================================================

def setup_rendering():
    """Configures the render engine to Eevee."""
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = 64
    scene.eevee.use_soft_shadows = True
    scene.eevee.use_bloom = True
    scene.eevee.bloom_threshold = 1.0
    scene.eevee.bloom_intensity = 0.05
    scene.view_settings.look = 'High Contrast'
    scene.view_settings.view_transform = 'Filmic'

def setup_world():
    """Sets up the environment background with high-res stars."""
    world = bpy.data.worlds.new("Space_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    mapping = nodes.new('ShaderNodeMapping')
    env_tex = nodes.new('ShaderNodeTexEnvironment')
    bg = nodes.new('ShaderNodeBackground')
    out = nodes.new('ShaderNodeOutputWorld')
    
    stars_path = get_texture_path("stars.jpg")
    try:
        env_img = bpy.data.images.load(stars_path)
        env_tex.image = env_img
    except Exception as e:
        pass
    
    bg.inputs['Strength'].default_value = 1.0
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])
    links.new(env_tex.outputs['Color'], bg.inputs['Color'])
    links.new(bg.outputs['Background'], out.inputs['Surface'])

def setup_lighting():
    """Adds a harsh directional Sun light and a soft ambient fill light."""
    light_data = bpy.data.lights.new(name="Distant_Sun", type='SUN')
    light_data.energy = 5.0  
    light_data.angle = math.radians(0.5)
    
    light_obj = bpy.data.objects.new(name="SunLight", object_data=light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    link_to_collection(light_obj, "Lighting")
    
    light_obj.location = (25, -10, 5) # Adjusted to create a ~1/4 shadow
    direction = Vector((0, 0, 0)) - light_obj.location
    light_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    fill_data = bpy.data.lights.new(name="Ambient_Fill", type='SUN')
    fill_data.energy = 0.2 
    fill_data.color = (0.6, 0.7, 1.0) 
    
    fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
    bpy.context.scene.collection.objects.link(fill_obj)
    link_to_collection(fill_obj, "Lighting")
    
    fill_obj.location = (-20, 20, -10) 
    fill_dir = Vector((0, 0, 0)) - fill_obj.location
    fill_obj.rotation_euler = fill_dir.to_track_quat('-Z', 'Y').to_euler()

def setup_camera():
    """Sets up a cinematic camera perfectly framing the Earth-Moon system."""
    cam_data = bpy.data.cameras.new("MainCamera")
    cam_data.lens = 35.0  # Wider lens to capture the moon
    cam_data.clip_start = 0.1
    cam_data.clip_end = 10000.0
    
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    link_to_collection(cam_obj, "Environment")
    
    # Pull camera back far enough to see the moon's orbit
    distance = MOON_DISTANCE * 1.5  
    cam_obj.location = (0, -distance, distance * 0.1)
    
    direction = Vector((0, 0, 0)) - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam_obj

# ==============================================================================
# CELESTIAL BODIES & MATERIALS
# ==============================================================================

def create_celestial_body(name, radius, location, segments=128, ring_count=64):
    """Reusable function to spawn a high-quality spherical mesh."""
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius,
        segments=segments,
        ring_count=ring_count,
        location=location,
        calc_uvs=True
    )
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return obj

def apply_material_earth(earth_obj):
    mat = bpy.data.materials.new(name="Earth_Surface_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    # 1. Day Map
    tex_day = nodes.new("ShaderNodeTexImage")
    try: tex_day.image = bpy.data.images.load(get_texture_path(PLANET_TEXTURES["Earth"]["day"]))
    except: pass
        
    # 2. Specular Map (Oceans shiny, landmass rough)
    tex_spec = nodes.new("ShaderNodeTexImage")
    try:
        img_spec = bpy.data.images.load(get_texture_path(PLANET_TEXTURES["Earth"]["specular"]))
        try: img_spec.colorspace_settings.name = 'Non-Color'
        except: pass
        tex_spec.image = img_spec
    except: pass
    
    invert_spec = nodes.new("ShaderNodeInvert")
        
    # 3. Normal Map (Realistic mountain/terrain bumps from TIF)
    tex_normal = nodes.new("ShaderNodeTexImage")
    try:
        img_norm = bpy.data.images.load(get_texture_path(PLANET_TEXTURES["Earth"]["normal"]))
        try: img_norm.colorspace_settings.name = 'Non-Color'
        except: pass
        tex_normal.image = img_norm
    except: pass
    
    normal_map_node = nodes.new("ShaderNodeNormalMap")
    normal_map_node.inputs['Strength'].default_value = 1.0
    
    # 4. Night Map
    tex_night = nodes.new("ShaderNodeTexImage")
    try: tex_night.image = bpy.data.images.load(get_texture_path(PLANET_TEXTURES["Earth"]["night"]))
    except: pass

    # Day/Night Terminator Mask
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
    emission_strength.inputs[1].default_value = 3.0
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.6
    output = nodes.new("ShaderNodeOutputMaterial")
    
    # Links
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_day.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_spec.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_normal.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_night.inputs['Vector'])
    
    links.new(tex_day.outputs['Color'], bsdf.inputs['Base Color'])
    
    links.new(tex_spec.outputs['Color'], bsdf.inputs['Specular'])
    links.new(tex_spec.outputs['Color'], invert_spec.inputs['Color'])
    links.new(invert_spec.outputs['Color'], bsdf.inputs['Roughness']) # Land rough, oceans shiny!
    
    links.new(tex_normal.outputs['Color'], normal_map_node.inputs['Color'])
    links.new(normal_map_node.outputs['Normal'], bsdf.inputs['Normal'])
    
    links.new(geometry.outputs['Normal'], dot_product.inputs[0])
    links.new(sun_away_vector.outputs['Vector'], dot_product.inputs[1])
    links.new(dot_product.outputs['Value'], terminator_ramp.inputs['Fac'])
    links.new(terminator_ramp.outputs['Color'], emission_strength.inputs[0])
    
    links.new(tex_night.outputs['Color'], bsdf.inputs['Emission'])
    links.new(emission_strength.outputs['Value'], bsdf.inputs['Emission Strength'])
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    if len(earth_obj.data.materials) == 0: earth_obj.data.materials.append(mat)
    else: earth_obj.data.materials[0] = mat

def apply_material_clouds(cloud_obj):
    """Creates an alpha-hashed semi-transparent cloud layer that wraps around Earth."""
    mat = bpy.data.materials.new(name="Cloud_Material")
    mat.use_nodes = True
    mat.blend_method = 'HASHED' # High-quality Eevee transparency with shadows
    mat.shadow_method = 'HASHED'
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    tex_clouds = nodes.new("ShaderNodeTexImage")
    try: 
        img_clouds = bpy.data.images.load(get_texture_path(PLANET_TEXTURES["Earth"]["clouds"]))
        try: img_clouds.colorspace_settings.name = 'Non-Color'
        except: pass
        tex_clouds.image = img_clouds
    except: pass
    
    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.color_ramp.elements[0].position = 0.05
    color_ramp.color_ramp.elements[0].color = (0, 0, 0, 1) # Transparent
    color_ramp.color_ramp.elements[1].position = 0.8
    color_ramp.color_ramp.elements[1].color = (1, 1, 1, 1) # Opaque white clouds
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Base Color'].default_value = (0.9, 0.9, 0.9, 1.0) # Light-grey clouds
    bsdf.inputs['Roughness'].default_value = 0.9
    bsdf.inputs['Specular'].default_value = 0.0
    
    output = nodes.new("ShaderNodeOutputMaterial")
    
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_clouds.inputs['Vector'])
    
    links.new(tex_clouds.outputs['Color'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], bsdf.inputs['Alpha'])
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    if len(cloud_obj.data.materials) == 0: cloud_obj.data.materials.append(mat)
    else: cloud_obj.data.materials[0] = mat

def apply_material_moon(moon_obj):
    mat = bpy.data.materials.new(name="Moon_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    tex_surface = nodes.new("ShaderNodeTexImage")
    try: tex_surface.image = bpy.data.images.load(get_texture_path(PLANET_TEXTURES["Moon"]["surface"]))
    except: pass
        
    tex_bump = nodes.new("ShaderNodeTexImage")
    try: 
        img_b = bpy.data.images.load(get_texture_path(PLANET_TEXTURES["Moon"]["bump"]))
        try: img_b.colorspace_settings.name = 'Non-Color'
        except: pass
        tex_bump.image = img_b
    except: pass
    
    bump_node = nodes.new("ShaderNodeBump")
    bump_node.inputs['Strength'].default_value = 0.8
    bump_node.inputs['Distance'].default_value = 0.01
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.9
    bsdf.inputs['Specular'].default_value = 0.05
    
    output = nodes.new("ShaderNodeOutputMaterial")
    
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_surface.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_bump.inputs['Vector'])
    
    links.new(tex_surface.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(tex_bump.outputs['Color'], bump_node.inputs['Height'])
    links.new(bump_node.outputs['Normal'], bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    if len(moon_obj.data.materials) == 0: moon_obj.data.materials.append(mat)
    else: moon_obj.data.materials[0] = mat

def create_system():
    """Creates Earth, the Atmospheric Clouds, and the Moon."""
    # Create Earth Surface
    earth_obj = create_celestial_body("Earth", EARTH_RADIUS, (0, 0, 0), segments=256, ring_count=128)
    link_to_collection(earth_obj, "EarthSystem")
    apply_material_earth(earth_obj)
    
    # Create Earth Cloud Shell (slightly larger than Earth)
    clouds_obj = create_celestial_body("Earth_Clouds", EARTH_RADIUS * 1.006, (0, 0, 0), segments=256, ring_count=128)
    link_to_collection(clouds_obj, "EarthSystem")
    apply_material_clouds(clouds_obj)
    
    # Parent clouds to earth so they rotate synchronously
    clouds_obj.parent = earth_obj
    
    # Create Moon Pivot (Empty at the center of Earth)
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    moon_pivot = bpy.context.object
    moon_pivot.name = "Moon_Orbit_Pivot"
    link_to_collection(moon_pivot, "EarthSystem")
    
    # Create Moon
    moon_obj = create_celestial_body("Moon", MOON_RADIUS, (MOON_DISTANCE, 0, 0), segments=128, ring_count=64)
    link_to_collection(moon_obj, "EarthSystem")
    apply_material_moon(moon_obj)
    moon_obj.parent = moon_pivot
    
    return earth_obj, clouds_obj, moon_pivot

# ==============================================================================
# ANIMATION
# ==============================================================================

def setup_animation(earth_obj, clouds_obj, moon_pivot):
    """Sets up a majestic, slow rotation so the planet features can be highlighted."""
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    
    # Earth rotates exactly 1 time over 240 frames for a majestic showcase
    earth_target_degrees = 360.0 * EARTH_ROTATIONS
    
    earth_obj.rotation_euler[2] = 0.0
    earth_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    
    earth_obj.rotation_euler[2] = math.radians(earth_target_degrees)
    earth_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=TOTAL_FRAMES + 1)
    
    # We can optionally animate the clouds slightly faster/slower than Earth for a dynamic wind effect!
    # A full rotation + 5 degrees offset creates realistic cloud movement over the animation loop
    clouds_obj.rotation_euler[2] = 0.0
    clouds_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    clouds_obj.rotation_euler[2] = math.radians(5.0) 
    clouds_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=TOTAL_FRAMES + 1)
    
    # Moon orbits exactly 1 time over 240 frames
    moon_target_degrees = 360.0 * MOON_ROTATIONS
    
    moon_pivot.rotation_euler[2] = 0.0
    moon_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    
    moon_pivot.rotation_euler[2] = math.radians(moon_target_degrees)
    moon_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=TOTAL_FRAMES + 1)
    
    # Linear Interpolation
    for obj in [earth_obj, clouds_obj, moon_pivot]:
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'LINEAR'

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    clear_scene()
    setup_collections()
    setup_rendering()
    setup_world()
    setup_lighting()
    setup_camera()
    
    earth_obj, clouds_obj, moon_pivot = create_system()
    setup_animation(earth_obj, clouds_obj, moon_pivot)
    
    print(f"✅ Majestic Earth sequence generated with advanced multi-layer textures.")

if __name__ == "__main__":
    main()
