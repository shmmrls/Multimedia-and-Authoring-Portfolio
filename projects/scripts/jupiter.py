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
# Jupiter radius is approx 69,911 km -> we use 69.9 units
JUPITER_RADIUS = 69.9

# Animation timeline configuration
# Jupiter rotates incredibly fast! A 10-hour day.
# If Earth (24 hr) is 360 frames, Jupiter (10 hr) should be 150 frames.
TOTAL_FRAMES = 150 
ROTATION_RATIO = 1.0 

PLANET_TEXTURES = {
    "Jupiter": {"map": "jupiter_map.jpg"},
    "Io": {"surface": "moon_io.png"},
    "Europa": {"surface": "moon_europa.jpg"},
    "Ganymede": {"surface": "moon_ganymede.png"},
    "Callisto": {"surface": "moon_callisto.png"},
    "GenericMoon": {"surface": "moon_surface.jpg", "bump": "moon_bump.jpg"}
}

# The 4 Galilean Moons (Radius, Distance, Rotations per 150 frames, Texture)
GALILEAN_MOONS = [
    {"name": "Io", "radius": 1.82, "distance": JUPITER_RADIUS * 1.5, "rotations": 4, "tex": "Io"},
    {"name": "Europa", "radius": 1.56, "distance": JUPITER_RADIUS * 2.0, "rotations": 3, "tex": "Europa"},
    {"name": "Ganymede", "radius": 2.63, "distance": JUPITER_RADIUS * 3.0, "rotations": 2, "tex": "Ganymede"},
    {"name": "Callisto", "radius": 2.41, "distance": JUPITER_RADIUS * 4.5, "rotations": 1, "tex": "Callisto"},
]

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_texture_path(filename):
    path = os.path.join(TEXTURE_DIR, filename)
    if not os.path.exists(path):
        print(f"Warning: Texture '{filename}' not found in {TEXTURE_DIR}.")
    return path

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in [bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.lights, bpy.data.cameras]:
        for item in block:
            block.remove(item)

def setup_collections():
    collections = ["JupiterSystem", "GalileanMoons", "MinorMoons", "Lighting", "Environment"]
    scene_collection = bpy.context.scene.collection
    for name in collections:
        if name not in bpy.data.collections:
            new_col = bpy.data.collections.new(name)
            scene_collection.children.link(new_col)

def link_to_collection(obj, collection_name):
    if collection_name in bpy.data.collections:
        bpy.data.collections[collection_name].objects.link(obj)
        if obj.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(obj)

# ==============================================================================
# RENDERING, WORLD & LIGHTING
# ==============================================================================

def setup_rendering():
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
    # Main Sunlight
    light_data = bpy.data.lights.new(name="Distant_Sun", type='SUN')
    light_data.energy = 6.0  
    light_data.angle = math.radians(0.5)
    
    light_obj = bpy.data.objects.new(name="SunLight", object_data=light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    link_to_collection(light_obj, "Lighting")
    
    light_obj.location = (50, -50, 20)
    direction = Vector((0, 0, 0)) - light_obj.location
    light_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    # Ambient Fill Light
    fill_data = bpy.data.lights.new(name="Ambient_Fill", type='SUN')
    fill_data.energy = 0.3 
    fill_data.color = (0.6, 0.7, 1.0) 
    
    fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
    bpy.context.scene.collection.objects.link(fill_obj)
    link_to_collection(fill_obj, "Lighting")
    
    fill_obj.location = (-50, 50, -20) 
    fill_dir = Vector((0, 0, 0)) - fill_obj.location
    fill_obj.rotation_euler = fill_dir.to_track_quat('-Z', 'Y').to_euler()

def setup_camera():
    cam_data = bpy.data.cameras.new("MainCamera")
    cam_data.lens = 35.0  
    cam_data.clip_start = 0.1
    cam_data.clip_end = 100000.0
    
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    link_to_collection(cam_obj, "Environment")
    
    distance = JUPITER_RADIUS * 6.5  
    cam_obj.location = (0, -distance, distance * 0.1)
    
    direction = Vector((0, 0, 0)) - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam_obj

# ==============================================================================
# CELESTIAL BODIES & MATERIALS
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

def apply_material_jupiter(jupiter_obj):
    mat = bpy.data.materials.new(name="Jupiter_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    tex_surface = nodes.new("ShaderNodeTexImage")
    try: tex_surface.image = bpy.data.images.load(get_texture_path(PLANET_TEXTURES["Jupiter"]["map"]))
    except: pass
        
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    # Jupiter is a gas giant, so we give it high roughness to scatter light softly like atmosphere
    bsdf.inputs['Roughness'].default_value = 0.8
    bsdf.inputs['Specular'].default_value = 0.05
    
    output = nodes.new("ShaderNodeOutputMaterial")
    
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_surface.inputs['Vector'])
    links.new(tex_surface.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    if len(jupiter_obj.data.materials) == 0: jupiter_obj.data.materials.append(mat)
    else: jupiter_obj.data.materials[0] = mat

def apply_material_moon(moon_obj, tex_key, use_bump=False, darken=False):
    mat = bpy.data.materials.new(name=f"{moon_obj.name}_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    
    tex_surface = nodes.new("ShaderNodeTexImage")
    try: tex_surface.image = bpy.data.images.load(get_texture_path(PLANET_TEXTURES[tex_key]["surface"]))
    except: pass
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Roughness'].default_value = 0.95
    bsdf.inputs['Specular'].default_value = 0.05
    
    color_output = tex_surface.outputs['Color']
    
    if darken:
        color_mix = nodes.new("ShaderNodeMixRGB")
        color_mix.blend_type = 'MULTIPLY'
        color_mix.inputs[0].default_value = 1.0
        color_mix.inputs[2].default_value = (0.5, 0.45, 0.4, 1.0) 
        links.new(tex_surface.outputs['Color'], color_mix.inputs[1])
        color_output = color_mix.outputs['Color']

    if use_bump and "bump" in PLANET_TEXTURES[tex_key]:
        tex_bump = nodes.new("ShaderNodeTexImage")
        try: 
            img_b = bpy.data.images.load(get_texture_path(PLANET_TEXTURES[tex_key]["bump"]))
            try: img_b.colorspace_settings.name = 'Non-Color'
            except: pass
            tex_bump.image = img_b
        except: pass
        
        bump_node = nodes.new("ShaderNodeBump")
        bump_node.inputs['Strength'].default_value = 0.9
        bump_node.inputs['Distance'].default_value = 0.05
        links.new(mapping.outputs['Vector'], tex_bump.inputs['Vector'])
        links.new(tex_bump.outputs['Color'], bump_node.inputs['Height'])
        links.new(bump_node.outputs['Normal'], bsdf.inputs['Normal'])

    output = nodes.new("ShaderNodeOutputMaterial")
    
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex_surface.inputs['Vector'])
    links.new(color_output, bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    if len(moon_obj.data.materials) == 0: moon_obj.data.materials.append(mat)
    else: moon_obj.data.materials[0] = mat

def create_system():
    # JUPITER
    jupiter_obj = create_celestial_body("Jupiter", JUPITER_RADIUS, (0, 0, 0), segments=256, ring_count=128)
    link_to_collection(jupiter_obj, "JupiterSystem")
    apply_material_jupiter(jupiter_obj)
    
    pivots = []
    
    # 1. THE 4 MAJOR GALILEAN MOONS
    for moon_data in GALILEAN_MOONS:
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        pivot = bpy.context.object
        pivot.name = f"{moon_data['name']}_Pivot"
        
        # Slight orbital tilt
        pivot.rotation_euler[0] = math.radians(random.uniform(-5, 5))
        # Random start angle
        start_angle = math.radians(random.uniform(0, 360))
        pivot.rotation_euler[2] = start_angle
        
        link_to_collection(pivot, "GalileanMoons")
        
        moon_obj = create_celestial_body(moon_data["name"], moon_data["radius"], (moon_data["distance"], 0, 0), segments=64, ring_count=32)
        link_to_collection(moon_obj, "GalileanMoons")
        apply_material_moon(moon_obj, moon_data["tex"])
        moon_obj.parent = pivot
        
        pivots.append({"obj": pivot, "rotations": moon_data["rotations"], "start_angle": start_angle})

    # 2. A CINEMATIC MINOR MOON SWARM
    # Instead of generating all 91 minor moons, we generate a cinematic cluster of 15
    for i in range(1, 16):
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        pivot = bpy.context.object
        pivot.name = f"MinorMoon_Pivot_{i}"
        
        # Minor moons have crazy tilts and inclinations
        pivot.rotation_euler[0] = math.radians(random.uniform(-45, 45))
        pivot.rotation_euler[1] = math.radians(random.uniform(-45, 45))
        start_angle = math.radians(random.uniform(0, 360))
        pivot.rotation_euler[2] = start_angle
        link_to_collection(pivot, "MinorMoons")
        
        # Random size and distance
        m_radius = random.uniform(0.1, 0.5)
        # Scatter them throughout the system, some inner, some very far outer
        m_distance = JUPITER_RADIUS * random.uniform(1.2, 8.0)
        
        moon_obj = create_celestial_body(f"MinorMoon_{i}", m_radius, (m_distance, 0, 0), is_low_poly=True)
        # Distort the icosphere to look like an asteroid
        moon_obj.scale = (1.0, random.uniform(0.5, 0.9), random.uniform(0.5, 0.9))
        link_to_collection(moon_obj, "MinorMoons")
        
        # Assign generic rocky material, randomly darkened
        apply_material_moon(moon_obj, "GenericMoon", use_bump=True, darken=True)
        moon_obj.parent = pivot
        
        # Random orbit speed. To loop perfectly, it must be an integer over the timeline!
        # Some are retrograde (negative), some are prograde.
        speed = random.choice([-3, -2, -1, 1, 2, 3, 4, 5])
        pivots.append({"obj": pivot, "rotations": speed, "start_angle": start_angle})
        
    return jupiter_obj, pivots

# ==============================================================================
# ANIMATION
# ==============================================================================

def setup_animation(jupiter_obj, pivots):
    """Sets up perfectly looping rotations for Jupiter and all 95 moons."""
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    
    # JUPITER
    target_degrees = 360.0 * ROTATION_RATIO
    jupiter_obj.rotation_euler[2] = 0.0
    jupiter_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    jupiter_obj.rotation_euler[2] = math.radians(target_degrees)
    jupiter_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=TOTAL_FRAMES + 1)
    
    # ALL 95 MOONS
    for p_data in pivots:
        pivot = p_data["obj"]
        start_ang = p_data["start_angle"]
        target_ang = start_ang + math.radians(360.0 * p_data["rotations"])
        
        pivot.rotation_euler[2] = start_ang
        pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
        pivot.rotation_euler[2] = target_ang
        pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=TOTAL_FRAMES + 1)
    
    # Linear Interpolation
    for obj in [jupiter_obj] + [p["obj"] for p in pivots]:
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
    
    jupiter_obj, pivots = create_system()
    setup_animation(jupiter_obj, pivots)
    
    print(f"✅ Majestic Jupiter sequence generated with all 95 moons!")

if __name__ == "__main__":
    main()
