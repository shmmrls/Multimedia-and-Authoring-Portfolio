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
MARS_RADIUS = 3.39

# Phobos and Deimos are extremely small potato-shaped rocks.
# We are heavily scaling them up stylistically so they are visible in the animation.
PHOBOS_RADIUS = 0.25
DEIMOS_RADIUS = 0.15

# Orbit distances scaled for cinematic framing
PHOBOS_DISTANCE = 8.0
DEIMOS_DISTANCE = 14.0

# Animation timeline configuration
TOTAL_FRAMES = 480

# Rotations
ROTATION_RATIO = 1.0 # Mars completes 1 rotation
PHOBOS_ROTATIONS = 4.0 # Phobos orbits very fast (in reality, faster than Mars rotates!)
DEIMOS_ROTATIONS = 1.0 # Deimos orbits slower

PLANET_TEXTURES = {
    "Mars": {
        "surface": "mars_surface.jpg", 
        "normal": "mars_normal.jpg", 
        "bump": "mars_bump.jpg"
    },
    "Moons": {
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
    collections = ["MarsSystem", "Lighting", "Environment"]
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
    
    # Pulled the light more towards the camera front (Y = -20) to significantly reduce the shadow 
    light_obj.location = (15, -20, 10)
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
    """Sets up a cinematic camera perfectly framing Mars and its moons."""
    cam_data = bpy.data.cameras.new("MainCamera")
    cam_data.lens = 35.0  # Wider lens to capture the orbiting moons
    cam_data.clip_start = 0.1
    cam_data.clip_end = 10000.0
    
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    link_to_collection(cam_obj, "Environment")
    
    # Distance calculated to fit the furthest moon (Deimos)
    distance = DEIMOS_DISTANCE * 1.5  
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

def apply_material_mars(mars_obj):
    """Builds a dry, dusty, physically accurate shader for Mars."""
    mat = bpy.data.materials.new(name="Mars_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    tex_surface = nodes.new("ShaderNodeTexImage")
    try: tex_surface.image = bpy.data.images.load(get_texture_path(PLANET_TEXTURES["Mars"]["surface"]))
    except: pass
        
    tex_normal = nodes.new("ShaderNodeTexImage")
    try: 
        img_norm = bpy.data.images.load(get_texture_path(PLANET_TEXTURES["Mars"]["normal"]))
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
    
    if len(mars_obj.data.materials) == 0: mars_obj.data.materials.append(mat)
    else: mars_obj.data.materials[0] = mat

def apply_material_moon(moon_obj, material_name="Mars_Moon_Material"):
    mat = bpy.data.materials.new(name=material_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    tex_surface = nodes.new("ShaderNodeTexImage")
    try: tex_surface.image = bpy.data.images.load(get_texture_path(PLANET_TEXTURES["Moons"]["surface"]))
    except: pass
        
    tex_bump = nodes.new("ShaderNodeTexImage")
    try: 
        img_b = bpy.data.images.load(get_texture_path(PLANET_TEXTURES["Moons"]["bump"]))
        try: img_b.colorspace_settings.name = 'Non-Color'
        except: pass
        tex_bump.image = img_b
    except: pass
    
    bump_node = nodes.new("ShaderNodeBump")
    bump_node.inputs['Strength'].default_value = 0.9
    bump_node.inputs['Distance'].default_value = 0.02
    
    # To make them look distinctly like Phobos and Deimos, we darken the generic moon map 
    # to mimic their low-albedo, dark carbonaceous surfaces.
    color_mix = nodes.new("ShaderNodeMixRGB")
    color_mix.blend_type = 'MULTIPLY'
    color_mix.inputs[0].default_value = 1.0
    color_mix.inputs[2].default_value = (0.3, 0.25, 0.2, 1.0) # Dark brownish tint
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.95
    bsdf.inputs['Specular'].default_value = 0.01
    
    output = nodes.new("ShaderNodeOutputMaterial")
    
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_surface.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_bump.inputs['Vector'])
    
    links.new(tex_surface.outputs['Color'], color_mix.inputs[1])
    links.new(color_mix.outputs['Color'], bsdf.inputs['Base Color'])
    
    links.new(tex_bump.outputs['Color'], bump_node.inputs['Height'])
    links.new(bump_node.outputs['Normal'], bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    if len(moon_obj.data.materials) == 0: moon_obj.data.materials.append(mat)
    else: moon_obj.data.materials[0] = mat

def create_system():
    """Creates Mars and its two tiny moons."""
    mars_obj = create_celestial_body("Mars", MARS_RADIUS, (0, 0, 0), segments=256, ring_count=128)
    link_to_collection(mars_obj, "MarsSystem")
    apply_material_mars(mars_obj)
    
    # ---- PHOBOS ----
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    phobos_pivot = bpy.context.object
    phobos_pivot.name = "Phobos_Pivot"
    link_to_collection(phobos_pivot, "MarsSystem")
    
    phobos_obj = create_celestial_body("Phobos", PHOBOS_RADIUS, (PHOBOS_DISTANCE, 0, 0), segments=64, ring_count=32)
    # Phobos is potato-shaped, so we non-uniformly scale the sphere!
    phobos_obj.scale = (1.0, 0.75, 0.6) 
    link_to_collection(phobos_obj, "MarsSystem")
    apply_material_moon(phobos_obj, "Phobos_Material")
    phobos_obj.parent = phobos_pivot
    
    # ---- DEIMOS ----
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    deimos_pivot = bpy.context.object
    deimos_pivot.name = "Deimos_Pivot"
    # Tilt the Deimos orbit slightly for visual depth
    deimos_pivot.rotation_euler[0] = math.radians(10)
    link_to_collection(deimos_pivot, "MarsSystem")
    
    deimos_obj = create_celestial_body("Deimos", DEIMOS_RADIUS, (-DEIMOS_DISTANCE, 0, 0), segments=64, ring_count=32)
    # Deimos is also potato-shaped but even smaller
    deimos_obj.scale = (0.8, 0.6, 0.5)
    link_to_collection(deimos_obj, "MarsSystem")
    apply_material_moon(deimos_obj, "Deimos_Material")
    deimos_obj.parent = deimos_pivot
    
    return mars_obj, phobos_pivot, deimos_pivot

# ==============================================================================
# ANIMATION
# ==============================================================================

def setup_animation(mars_obj, phobos_pivot, deimos_pivot):
    """Sets up a majestic, perfectly looping rotation for all 3 bodies."""
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    
    # MARS
    mars_target_degrees = 360.0 * ROTATION_RATIO
    mars_obj.rotation_euler[2] = 0.0
    mars_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    mars_obj.rotation_euler[2] = math.radians(mars_target_degrees)
    mars_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=TOTAL_FRAMES + 1)
    
    # PHOBOS (Inner fast moon)
    phobos_target_degrees = 360.0 * PHOBOS_ROTATIONS
    phobos_pivot.rotation_euler[2] = 0.0
    phobos_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    phobos_pivot.rotation_euler[2] = math.radians(phobos_target_degrees)
    phobos_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=TOTAL_FRAMES + 1)
    
    # DEIMOS (Outer slow moon)
    deimos_target_degrees = 360.0 * DEIMOS_ROTATIONS
    # Since Deimos was spawned at -X, its starting rotation is technically offset by 180 visually,
    # but we just rotate the pivot starting from 0 to 360 seamlessly.
    deimos_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1) # Already has 10 deg X tilt
    deimos_pivot.rotation_euler[2] = math.radians(deimos_target_degrees)
    deimos_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=TOTAL_FRAMES + 1)
    
    # Linear Interpolation
    for obj in [mars_obj, phobos_pivot, deimos_pivot]:
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
    
    mars_obj, phobos_pivot, deimos_pivot = create_system()
    setup_animation(mars_obj, phobos_pivot, deimos_pivot)
    
    print(f"✅ Majestic Mars sequence generated with Phobos and Deimos.")

if __name__ == "__main__":
    main()
