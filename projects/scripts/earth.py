import bpy
import os
import math
import random
import bmesh
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

# Scale factor to adapt sizes and positions of objects from here.py (where Earth radius is 0.3)
S = EARTH_RADIUS / 0.3

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

def assign_material(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

def create_empty(name, location=(0, 0, 0)):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
    obj = bpy.context.active_object
    obj.name = name
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
    obj.scale = (0.12 * S, 0.12 * S, 0.12 * S)
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
    obj.scale = (0.2 * S, 0.2 * S, 0.2 * S)
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
    obj.scale = (0.1 * S, 0.1 * S, 0.1 * S)
    return obj

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
    bpy.ops.mesh.primitive_cone_add(
        vertices=8, radius1=1.0, radius2=0.0, depth=1.0, location=(0, 0, 0)
    )
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return obj

def set_linear_cycles(obj):
    if not (obj.animation_data and obj.animation_data.action):
        return
    for fc in obj.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

def add_meteor_system(earth_obj, cam_obj):
    scene = bpy.context.scene
    met_mat = create_meteor_material()
    
    # Create a local meteor system for Earth
    meteor_system = create_empty("Earth_Meteor_System", location=(0, 0, 0))
    link_to_collection(meteor_system, "EarthSystem")
    
    # Template mesh specifically for Earth
    base_mesh_obj = create_meteor_mesh("Earth_Meteor_Template")
    base_mesh_obj.parent = meteor_system
    base_mesh_obj.hide_viewport = True
    base_mesh_obj.hide_render = True
    assign_material(base_mesh_obj, met_mat)
    link_to_collection(base_mesh_obj, "EarthSystem")
    
    # Schedule starts for Earth over 360 frames (scattered)
    scheduled_starts = [45, 120, 210, 290]
    
    meteor_counter = 0
    prad = EARTH_RADIUS
    
    for f_start in scheduled_starts:
        duration = random.randint(8, 16)
        f_end = f_start + duration
        if f_end >= TOTAL_FRAMES:
            continue
            
        # Get camera direction relative to Earth at f_start to bias visibility
        scene.frame_set(f_start)
        bpy.context.view_layer.update()
        p_loc = earth_obj.matrix_world.translation.copy()
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
        met.name = f"Meteor_Earth_{meteor_counter}"
        meteor_counter += 1
        met.hide_viewport = False
        met.hide_render = False
        met.parent = meteor_system
        link_to_collection(met, "EarthSystem")
        
        # Calculate rotation so it points base-first along path vector (using -Z tracking)
        path_vec = p_end - p_start
        rot_quat = path_vec.to_track_quat('-Z', 'Y')
        met.rotation_mode = 'QUATERNION'
        met.rotation_quaternion = rot_quat
        
        # Size proportional to host planet's radius
        scale_xy = prad * random.uniform(0.04, 0.08)
        scale_z = prad * random.uniform(0.66, 1.16)
        brightness = 1.0
        
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

def create_system():
    """Creates Earth, the Atmospheric Clouds, the Moon, Satellite, Station, Spaceship, and Comet."""
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
    
    # --- Spacecraft ---
    
    # 1. Satellite
    sat_pivot = create_empty("Earth_Satellite_Orbit", location=(0, 0, 0))
    link_to_collection(sat_pivot, "EarthSystem")
    sat = build_satellite("Earth_Satellite")
    link_to_collection(sat, "EarthSystem")
    sat.parent = sat_pivot
    sat.location = (0.7 * S, 0, 0.2 * S)
    
    # 2. Space Station
    iss_pivot = create_empty("Earth_Space_Station_Orbit", location=(0, 0, 0))
    link_to_collection(iss_pivot, "EarthSystem")
    iss = build_space_station("Earth_Space_Station")
    link_to_collection(iss, "EarthSystem")
    iss.parent = iss_pivot
    iss.location = (-0.45 * S, 0.0, -0.2 * S)
    
    # 3. Space Shuttle (Spaceship)
    shuttle_pivot = create_empty("Earth_Space_Shuttle_Pivot", location=(0, 0, 0))
    link_to_collection(shuttle_pivot, "EarthSystem")
    shuttle = build_space_shuttle("Earth_Space_Shuttle")
    link_to_collection(shuttle, "EarthSystem")
    shuttle.parent = shuttle_pivot
    shuttle.location = (0.4 * S, -0.5 * S, 0.15 * S)
    
    return earth_obj, clouds_obj, moon_pivot, sat_pivot, iss_pivot, shuttle_pivot, shuttle

# ==============================================================================
# ANIMATION
# ==============================================================================

def setup_animation(earth_obj, clouds_obj, moon_pivot, sat_pivot, iss_pivot, shuttle_pivot, shuttle):
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
    
    # 1. Earth Satellite
    sat_pivot.rotation_euler.z = 0.0
    sat_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    # Scale speed from 2941 frames to TOTAL_FRAMES
    sat_target_degrees = (360.0 * 20.0 / 2941.0) * TOTAL_FRAMES
    sat_pivot.rotation_euler.z = math.radians(sat_target_degrees)
    sat_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=TOTAL_FRAMES + 1)
    
    # 2. Earth Space Station
    iss_pivot.rotation_euler.z = math.radians(180.0)
    iss_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    # Scale speed from 2941 frames to TOTAL_FRAMES
    iss_target_degrees = 180.0 - (360.0 * 15.0 / 2941.0) * TOTAL_FRAMES
    iss_pivot.rotation_euler.z = math.radians(iss_target_degrees)
    iss_pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=TOTAL_FRAMES + 1)
    
    # 3. Earth Space Shuttle (departs outward from Earth)
    shuttle_pivot.rotation_euler = (0, 0, 0)
    shuttle.rotation_mode = 'XYZ'
    shuttle.rotation_euler = (math.radians(15), 0, math.radians(-167))
    shuttle.keyframe_insert(data_path="rotation_euler", frame=1)
    shuttle.keyframe_insert(data_path="rotation_euler", frame=TOTAL_FRAMES + 1)
    
    # Location keyframes scaled to S and mapped to TOTAL_FRAMES
    shuttle.location = (0.4 * S, -0.5 * S, 0.15 * S)
    shuttle.keyframe_insert(data_path="location", frame=1)
    
    f_showcase_start = int(540 * TOTAL_FRAMES / 2941.0)
    shuttle.location = (0.4 * S, -0.5 * S, 0.15 * S)
    shuttle.keyframe_insert(data_path="location", frame=f_showcase_start)
    
    f_showcase_end = int(660 * TOTAL_FRAMES / 2941.0)
    shuttle.location = (-0.5 * S, -0.7 * S, 0.4 * S)
    shuttle.keyframe_insert(data_path="location", frame=f_showcase_end)
    
    f_mid = int(1200 * TOTAL_FRAMES / 2941.0)
    shuttle.location = (-3.0 * S, -2.0 * S, 2.0 * S)
    shuttle.keyframe_insert(data_path="location", frame=f_mid)
    
    shuttle.location = (-10.0 * S, -5.0 * S, 5.0 * S)
    shuttle.keyframe_insert(data_path="location", frame=TOTAL_FRAMES + 1)

    # Linear Interpolation for basic orbits
    for obj in [earth_obj, clouds_obj, moon_pivot, sat_pivot, iss_pivot]:
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'LINEAR'
                    
    # Bezier Interpolation for shuttle path
    for obj in [shuttle]:
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'BEZIER'

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
    
    earth_obj, clouds_obj, moon_pivot, sat_pivot, iss_pivot, shuttle_pivot, shuttle = create_system()
    setup_animation(earth_obj, clouds_obj, moon_pivot, sat_pivot, iss_pivot, shuttle_pivot, shuttle)
    
    # Add shooting stars / meteor system
    add_meteor_system(earth_obj, bpy.context.scene.camera)
    
    print(f"✅ Majestic Earth sequence generated with advanced multi-layer textures.")

if __name__ == "__main__":
    main()
