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
# Mercury radius is approx 2,439.7 km -> we use 2.44 units
MERCURY_RADIUS = 2.44

# Animation timeline configuration
TOTAL_FRAMES = 1080

# For a majestic, cinematic showcase, we discard scientific relative speeds.
# We force a slow fractional rotation to perfectly loop over 1080 frames.
ROTATION_RATIO = 1.0



PLANET_TEXTURES = {
    "Mercury": {"color": "mercury_color.jpg", "surface": "mercury_surface.jpg", "bump": "mercury_bump.jpg"},
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
    
    # Purge orphaned data
    for block in [bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.lights, bpy.data.cameras]:
        for item in block:
            block.remove(item)

def setup_collections():
    """Sets up the required collections for organization."""
    collections = ["Mercury", "Lighting", "Environment"]
    
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
    
    # Enable high-quality shadows for the craters
    scene.eevee.use_soft_shadows = True
    
    # High contrast look (NASA VTAD style)
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
    
    # Ambient Fill Light (Soft galactic glow to kill pure black shadows)
    fill_data = bpy.data.lights.new(name="Ambient_Fill", type='SUN')
    fill_data.energy = 0.5  # Very weak so it doesn't overpower the main sun
    fill_data.color = (0.6, 0.7, 1.0) # Slight bluish tint
    
    fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
    bpy.context.scene.collection.objects.link(fill_obj)
    link_to_collection(fill_obj, "Lighting")
    
    fill_obj.location = (-10, 10, -5) # Exact opposite angle
    fill_dir = Vector((0, 0, 0)) - fill_obj.location
    fill_obj.rotation_euler = fill_dir.to_track_quat('-Z', 'Y').to_euler()

def setup_camera():
    """Sets up a cinematic camera perfectly framing Mercury."""
    cam_data = bpy.data.cameras.new("MainCamera")
    cam_data.lens = 50.0  
    cam_data.clip_start = 0.1
    cam_data.clip_end = 10000.0
    
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    link_to_collection(cam_obj, "Environment")
    
    distance = MERCURY_RADIUS * 6.5  # Wider framing to keep it comfortably inside the camera view
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

def apply_material_mercury(mercury_obj):
    """Builds a physically plausible rocky shader for Mercury."""
    mat = bpy.data.materials.new(name="Mercury_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Nodes
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    # Surface Color Texture
    tex_color = nodes.new("ShaderNodeTexImage")
    color_path = get_texture_path(PLANET_TEXTURES["Mercury"]["surface"])
    try:
        img_c = bpy.data.images.load(color_path)
        tex_color.image = img_c
    except Exception as e:
        print(f"Error loading {color_path}: {e}")
        
    # Bump Texture
    tex_bump = nodes.new("ShaderNodeTexImage")
    bump_path = get_texture_path(PLANET_TEXTURES["Mercury"]["bump"])
    try:
        img_b = bpy.data.images.load(bump_path)
        try:
            img_b.colorspace_settings.name = 'Non-Color'
        except:
            pass
        tex_bump.image = img_b
    except Exception as e:
        print(f"Error loading {bump_path}: {e}")
        
    # Bump Node
    bump_node = nodes.new("ShaderNodeBump")
    bump_node.inputs['Strength'].default_value = 0.8
    bump_node.inputs['Distance'].default_value = 0.01 # Massively reduced to prevent weird sliding/shadow artifacts
    
    # Principled BSDF (Rocky Surface)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.9  # Very rough, dusty surface
    bsdf.inputs['Specular'].default_value = 0.1   # Low reflectivity
    
    output = nodes.new("ShaderNodeOutputMaterial")
    
    # Links
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_color.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_bump.inputs['Vector'])
    
    links.new(tex_color.outputs['Color'], bsdf.inputs['Base Color'])
    
    links.new(tex_bump.outputs['Color'], bump_node.inputs['Height'])
    links.new(bump_node.outputs['Normal'], bsdf.inputs['Normal'])
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    if len(mercury_obj.data.materials) == 0:
        mercury_obj.data.materials.append(mat)
    else:
        mercury_obj.data.materials[0] = mat

def create_mercury():
    """Creates Mercury and applies its rocky material."""
    mercury_obj = create_celestial_body("Mercury", MERCURY_RADIUS, (0, 0, 0), segments=256, ring_count=128)
    link_to_collection(mercury_obj, "Mercury")
    apply_material_mercury(mercury_obj)
    return mercury_obj

# ==============================================================================
# ANIMATION
# ==============================================================================

def setup_animation(mercury_obj):
    """Sets up accurate rotational speed based on NASA facts."""
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    
    # We use EXACTLY 360 degrees, but over a much longer timeline
    target_rotation_degrees = 360.0 * ROTATION_RATIO
    
    mercury_obj.rotation_euler[2] = 0.0
    mercury_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    
    mercury_obj.rotation_euler[2] = math.radians(target_rotation_degrees)
    # We keyframe exactly at TOTAL_FRAMES + 1 to keep linear progression steady
    mercury_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=TOTAL_FRAMES + 1)
    
    if mercury_obj.animation_data and mercury_obj.animation_data.action:
        for fcurve in mercury_obj.animation_data.action.fcurves:
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
    
    mercury_obj = create_mercury()
    setup_animation(mercury_obj)
    
    print("✅ Mercury sequence successfully generated.")

if __name__ == "__main__":
    main()
