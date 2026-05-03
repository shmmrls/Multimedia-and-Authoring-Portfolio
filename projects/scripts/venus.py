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
# Venus radius is approx 6,051.8 km -> we use 6.05 units
VENUS_RADIUS = 6.05

# Animation timeline configuration
TOTAL_FRAMES = 1440

# For a majestic, cinematic showcase, we discard scientific relative speeds.
# We force a slow backward rotation (-1.0) to perfectly loop over 1440 frames.
ROTATION_RATIO = -1.0



PLANET_TEXTURES = {
    "Venus": {"surface": "venus_surface.jpg", "clouds": "venus_clouds.jpg"},
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
    collections = ["Venus", "Lighting", "Environment"]
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
        print(f"Could not load stars texture: {e}")
    
    bg.inputs['Strength'].default_value = 1.0
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])
    links.new(env_tex.outputs['Color'], bg.inputs['Color'])
    links.new(bg.outputs['Background'], out.inputs['Surface'])

def setup_lighting():
    """Adds a harsh directional Sun light and a soft ambient fill light."""
    # Main Sunlight
    light_data = bpy.data.lights.new(name="Distant_Sun", type='SUN')
    light_data.energy = 5.0  
    light_data.angle = math.radians(0.5)
    
    light_obj = bpy.data.objects.new(name="SunLight", object_data=light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    link_to_collection(light_obj, "Lighting")
    
    light_obj.location = (10, -10, 5)
    direction = Vector((0, 0, 0)) - light_obj.location
    light_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    # Ambient Fill Light (Soft galactic/starlight glow to kill pure black shadows)
    fill_data = bpy.data.lights.new(name="Ambient_Fill", type='SUN')
    fill_data.energy = 0.5  # Very weak so it doesn't overpower the main sun
    fill_data.color = (0.6, 0.7, 1.0) # Slight bluish/cool tint
    
    fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
    bpy.context.scene.collection.objects.link(fill_obj)
    link_to_collection(fill_obj, "Lighting")
    
    fill_obj.location = (-10, 10, -5) # Exact opposite angle
    fill_dir = Vector((0, 0, 0)) - fill_obj.location
    fill_obj.rotation_euler = fill_dir.to_track_quat('-Z', 'Y').to_euler()

def setup_camera():
    """Sets up a cinematic camera perfectly framing Venus."""
    cam_data = bpy.data.cameras.new("MainCamera")
    cam_data.lens = 50.0  
    cam_data.clip_start = 0.1
    cam_data.clip_end = 10000.0
    
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    link_to_collection(cam_obj, "Environment")
    
    distance = VENUS_RADIUS * 6.5  
    cam_obj.location = (0, -distance, distance * 0.05)
    
    direction = Vector((0, 0, 0)) - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam_obj

# ==============================================================================
# CELESTIAL BODIES (MODULAR)
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

def apply_material_venus(venus_obj):
    """Builds a material that blends Venus' radar surface with its thick cloud cover."""
    mat = bpy.data.materials.new(name="Venus_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Nodes
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    # Surface Texture (Radar map of Venus)
    tex_surface = nodes.new("ShaderNodeTexImage")
    surface_path = get_texture_path(PLANET_TEXTURES["Venus"]["surface"])
    try:
        img_s = bpy.data.images.load(surface_path)
        tex_surface.image = img_s
    except Exception as e:
        print(f"Error loading {surface_path}: {e}")
        
    # Cloud Texture
    tex_clouds = nodes.new("ShaderNodeTexImage")
    clouds_path = get_texture_path(PLANET_TEXTURES["Venus"]["clouds"])
    try:
        img_c = bpy.data.images.load(clouds_path)
        tex_clouds.image = img_c
    except Exception as e:
        print(f"Error loading {clouds_path}: {e}")
        
    # Artistic Blend Node: Mixes the rocky surface with the thick yellow clouds
    # We mix them at ~65% clouds so you can still faintly see the surface details below
    mix_node = nodes.new("ShaderNodeMixRGB")
    mix_node.inputs['Fac'].default_value = 0.65 
    
    # Principled BSDF
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.7  # Clouds are relatively diffuse
    bsdf.inputs['Specular'].default_value = 0.2
    
    output = nodes.new("ShaderNodeOutputMaterial")
    
    # Links
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_surface.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_clouds.inputs['Vector'])
    
    links.new(tex_surface.outputs['Color'], mix_node.inputs[1])
    links.new(tex_clouds.outputs['Color'], mix_node.inputs[2])
    
    links.new(mix_node.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    if len(venus_obj.data.materials) == 0:
        venus_obj.data.materials.append(mat)
    else:
        venus_obj.data.materials[0] = mat

def create_venus():
    """Creates Venus and applies its material."""
    venus_obj = create_celestial_body("Venus", VENUS_RADIUS, (0, 0, 0), segments=256, ring_count=128)
    link_to_collection(venus_obj, "Venus")
    apply_material_venus(venus_obj)
    return venus_obj

# ==============================================================================
# ANIMATION
# ==============================================================================

def setup_animation(venus_obj):
    """Sets up perfectly looped rotation based on dynamically calculated frames."""
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    
    # We use EXACTLY 360 degrees, but over a much longer timeline (2160 frames)
    target_rotation_degrees = 360.0 * ROTATION_RATIO
    
    venus_obj.rotation_euler[2] = 0.0
    venus_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    
    venus_obj.rotation_euler[2] = math.radians(target_rotation_degrees)
    venus_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=TOTAL_FRAMES + 1)
    
    if venus_obj.animation_data and venus_obj.animation_data.action:
        for fcurve in venus_obj.animation_data.action.fcurves:
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
    
    venus_obj = create_venus()
    setup_animation(venus_obj)
    
    print("✅ Venus sequence successfully generated.")

if __name__ == "__main__":
    main()
