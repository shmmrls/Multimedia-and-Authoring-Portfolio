# Blender Planet Rendering Scripts Compilation

This document contains a comprehensive compilation of Blender Python scripts for rendering various planets and celestial bodies in the solar system. Each section represents a complete script for rendering a specific celestial object with optimized materials, lighting, and animation.

---

## Table of Contents

1. [Earth](#earth)
2. [Jupiter](#jupiter)
3. [Mars](#mars)
4. [Mercury](#mercury)
5. [Neptune](#neptune)
6. [Sun](#sun)
7. [Pluto](#pluto)
8. [Saturn](#saturn)
9. [Uranus](#uranus)
10. [Venus](#venus)

---

## General Setup

### Texture Path Configuration

All scripts use a common texture directory:

```python
texture_dir = r"C:\COLLEGE\THIRD TERM\MAA\Planets\textures\\"

def load_texture(name):
    for ext in [".jpg", ".png", ".jpeg", ".tif"]:
        path = os.path.join(texture_dir, name + ext)
        if os.path.exists(path):
            return bpy.data.images.load(path)
    print("Missing:", name)
    return None
```

### Scene Cleanup

Every script starts fresh by clearing the scene:

```python
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
```

---

## Earth

### Overview
Creates a realistic Earth with clouds, day/night textures, moon, and orbital mechanics.

### Key Settings
- **Earth Radius**: 2.0
- **Moon Radius**: 0.5448 (Earth radius × 0.2724)
- **Earth-Moon Distance**: 13.0
- **Earth Tilt**: 23.4°
- **Render Engine**: BLENDER_EEVEE
- **Animation**: 240 frames (linear interpolation)
- **Camera Lens**: 55mm

### Features
- Day and night map textures with city light emission
- Cloud layer with transparency
- Moon with tidal locking constraint
- Sun light (energy: 3) with two soft fill lights
- Stars background environment
- Eevee optimization with soft shadows

### Animation
- Earth rotation: 360° over 240 frames
- Moon orbital motion around Earth
- Linear keyframe interpolation for smooth motion

### Final Output Message
```
✅ DONE: Earth — Eevee optimized, stronger night lights, Sun + fills, stars bg, lens=55mm
```

---

## Jupiter

### Overview
Renders Jupiter with its four Galilean moons (Io, Europa, Ganymede, Callisto).

### Key Settings
- **Jupiter Radius**: 5.5
- **Jupiter Tilt**: 3.1°
- **Render Engine**: BLENDER_EEVEE
- **Animation**: 240 frames
- **Camera Lens**: 55mm
- **Camera Distance**: 88 units

### Galilean Moons
| Moon | Distance | Size | Orbital Speed |
|------|----------|------|---|
| Io | 8 | 0.35 | 3.0× |
| Europa | 10 | 0.3 | 1.5× |
| Ganymede | 13 | 0.5 | 0.7× |
| Callisto | 16 | 0.45 | 0.3× |

### Material Properties
- Matte appearance (roughness: 0.7)
- Subtle emission for visibility (0.1 strength)
- Mix shader blending BSDF + emission (20% factor)

### Lighting
- Sun light (energy: 3)
- Two area fill lights (energy: 30 each, size: 12)
- Stars background

### Final Output Message
```
✅ DONE: Jupiter — Eevee optimized, matte material, Sun + fills, stars bg, lens=55mm, Galilean moons
```

---

## Mars

### Overview
Renders Mars with subtle atmospheric effects and realistic proportions.

### Key Settings
- **Mars Radius**: 1.064 (Earth radius × 0.532)
- **Mars Tilt**: 25.2°
- **Render Engine**: BLENDER_EEVEE
- **Animation**: 240 frames with 350° rotation
- **Camera Lens**: 55mm

### Material Properties
- Surface texture with sRGB color space
- Matte finish (roughness: 0.7)
- Subtle emission for visibility (0.1 strength)
- Mix shader with 20% emission blend

### Lighting Setup
- Sun light (energy: 3) at (10, -10, 10)
- Two area fill lights (energy: 30 each, size: 8)
- Stars background environment

### Final Output Message
```
✅ DONE: Mars — Eevee optimized, matte material, Sun + fills, stars bg, lens=55mm
```

---

## Mercury

### Overview
Renders Mercury using Cycles renderer for high-quality results with detailed surface textures.

### Key Settings
- **Mercury Radius**: 0.766 (Earth radius × 0.383)
- **Mercury Tilt**: 2.0°
- **Initial Rotation**: 140°
- **Render Engine**: CYCLES
- **Cycles Samples**: 128 (GPU)
- **Camera Lens**: 55mm

### Material Properties
- Color and bump textures for detail
- Bump mapping with 0.6 strength
- Extremely rough surface (roughness: 0.95)
- Minimal specularity (0.03)
- Highly detailed crater representation

### Lighting - NASA Style
Five area lights positioned to fully illuminate Mercury:
- **Key Light**: (0, -10, 0), energy: 200
- **Fill Left**: (10, 5, 3), energy: 150
- **Fill Right**: (-10, 5, -3), energy: 150
- **Fill Top**: (0, 3, 10), energy: 100
- **Fill Back**: (0, 10, 0), energy: 120

All lights track toward Mercury center.

### Camera Formula
```
CAM_DIST = MERCURY_RADIUS * 16 = 12.3 units
```

### Animation
- Rotation from 140° to 260° over 240 frames
- Linear interpolation

### Final Output Message
```
✅ DONE: Mercury — uniform camera (D=12.3), stars bg, lens=55mm
```

---

## Neptune

### Overview
Renders Neptune with sophisticated atmosphere effects, rings, and multiple moons.

### Key Settings
- **Neptune Radius**: 3.9
- **Neptune Tilt**: 28°
- **Ring Outer**: 6.7
- **Render Engine**: BLENDER_EEVEE
- **Sphere Segments**: 128×64 (smooth geometry)
- **Animation**: 240 frames
- **Camera Lens**: 55mm

### Sphere Quality
- Segments: 128 (high smoothness)
- Ring Count: 64
- No faceted appearance ("disco ball" effect eliminated)

### Material System
- **Surface**: Matte finish with BSDF
- **Bump Mapping**: Normal displacement
- **Emission**: Subtle glow for deep-space visibility (0.15 strength)
- **Mix Shader**: BSDF + emission blend (20% factor)

### Atmosphere Layer
- Outer sphere at radius + 0.12
- Facing weight layer for limb brightening
- Emission color: (0.2, 0.6, 1.0) - cyan blue
- Transparent shader for edge visibility
- Blend method: BLEND

### Rings
Five procedural rings with varying opacity:
- Ring 1: r=4.8, thickness=0.008, alpha=0.05
- Ring 2: r=5.3, thickness=0.008, alpha=0.06
- Ring 3: r=5.8, thickness=0.015, alpha=0.04
- Ring 4: r=6.2, thickness=0.008, alpha=0.05
- Ring 5: r=6.7, thickness=0.010, alpha=0.08

### Moons
Five major moons plus ten random smaller moons with orbital animation.

### Lighting
- Sun light at (-60, -20, 25), energy: 3
- Area fill 1: (10, -10, 10), energy: 300
- Area fill 2: (-10, 10, -10), energy: 100

### Final Output Message
```
✅ DONE: Neptune — Eevee, smooth sphere (128×64), Venus-style lighting, LINEAR anim, lens=55mm
```

---

## Sun

### Overview
Creates a highly realistic sun with fiery materials, corona effects, and bloom lighting.

### Key Settings
- **Sun Radius**: 6.0
- **Sphere Segments**: 256×128 (ultra-smooth)
- **Render Engine**: BLENDER_EEVEE
- **Key Feature**: Bloom effect enabled
- **Camera Lens**: 55mm

### Bloom Settings
- **Threshold**: 0.6 (start glow at this brightness)
- **Intensity**: 1.2 (glow radiance)
- **Radius**: 6.5 (spread width)
- **Color**: (1.0, 0.65, 0.15) warm orange-gold

### Sun Material - Fiery Multi-Layer
1. **Texture Layer**: Surface map blended in
2. **Large Noise**: Solar plumes (scale: 3.0, detail: 12.0)
3. **Fine Noise**: Granulation (scale: 18.0, detail: 8.0)
4. **Noise Blend**: Overlay mix at 55%
5. **Color Blend**: Screen mode with texture (50%)
6. **Color Ramp**: 4-point gradient
   - 0.0: (0.6, 0.05, 0.0) deep red magma
   - 0.3: (1.0, 0.25, 0.0) orange fire
   - 0.6: (1.0, 0.65, 0.05) gold
   - 1.0: (1.0, 0.95, 0.6) hot white-yellow
7. **Emission Strength**: 25.0 (high value for bloom triggering)

### Corona Layer
- Outer sphere at radius × 1.08
- Facing weight for limb brightening
- Emission: (1.0, 0.6, 0.1), strength: 8.0
- Transparent shader mix

### Solar Halo Layer
- Outer sphere at radius × 1.25
- Even wider glow effect
- Emission: (1.0, 0.75, 0.2), strength: 3.0
- Subtle and diffuse

### Lighting System
1. **Point Light**: Center, energy: 50000 (main illumination)
   - Color: (1.0, 0.92, 0.7)
   - Shadow: enabled with 2.0 soft size
2. **Sun Light**: Energy: 12 (additional rays)
   - Color: (1.0, 0.88, 0.6)
   - Angle: 0.5°

### Stars Background
- Stars texture at strength: 0.6 (darker for contrast)

### Animation
- Linear rotation: 0° to 360° over 240 frames
- Continuous spinning effect

### Final Output Message
```
✅ DONE: Sun — Eevee + Bloom, smooth 256×128 sphere, corona + halo shells, fiery color ramp, solar point light, lens=55mm
```

---

## Pluto

### Overview
Renders Pluto and its binary companion Charon around a shared barycenter, with four small moons.

### Key Settings
- **Pluto Radius**: 0.372 (Earth × 0.186)
- **Pluto Tilt**: 57°
- **Charon Radius**: 0.189 (Pluto × 0.51)
- **Sphere Segments**: 128×64 (smooth geometry)
- **Render Engine**: BLENDER_EEVEE
- **Camera Lens**: 55mm

### Pluto Material
- Color and bump textures
- Matte finish (roughness: 0.85)
- Very subtle emission (0.1 strength, 15% mix)
- Bump strength: 0.6, distance: 0.2

### Atmosphere
- Thin layer at radius + 0.01
- Cyan emission (0.6, 0.7, 1.0)
- Emission strength: 0.4
- Transparent blend

### Binary System
- Pluto-Charon barycenter empty object
- Pluto offset: (-radius × 0.5, 0, 0)
- Charon: (+2.5× radius distance, 0, 0)
- Synchronized rotation around barycenter

### Small Moons
- **Nix**: distance = 12× Pluto radius, size = 0.07× radius
- **Hydra**: distance = 15× radius, size = 0.07× radius
- **Kerberos**: distance = 18× radius, size = 0.05× radius
- **Styx**: distance = 20× radius, size = 0.05× radius

### Lighting
- Sun light: (-40, -20, 20), energy: 3
- Area fill 1: (5, -5, 5), energy: 50
- Area fill 2: (-5, 5, -5), energy: 25

### Animation
- Barycenter rotates 360° over 240 frames
- All moons orbit with random speeds (0.5-2.0×)
- Linear keyframe interpolation

### Final Output Message
```
✅ DONE: Pluto — Eevee, smooth sphere (128×64), Venus-style lighting & emission, LINEAR anim, lens=55mm
```

---

## Saturn

### Overview
Renders Saturn with prominent rings and major moons (Titan, Enceladus, Rhea).

### Key Settings
- **Saturn Radius**: 5.0
- **Saturn Tilt**: 26.7°
- **Ring Outer**: 10.0
- **Render Engine**: BLENDER_EEVEE
- **Animation**: 240 frames with 180° rotation
- **Camera Lens**: 55mm
- **Camera Distance**: 160 units

### Ring System
- **Geometry**: Cylinder primitive (not torus)
- **Rotation**: 90° to face camera plane
- **Material**: Textured with alpha transparency
- **Roughness**: 0.9 (matte appearance)
- **Blend Method**: BLEND with no shadows

### Major Moons
| Moon | Distance | Size | Orbital Speed |
|------|----------|------|---|
| Titan | 14 | 0.8 | 1.0× |
| Enceladus | 10 | 0.3 | 3.0× |
| Rhea | 18 | 0.5 | 2.0× |

### Material Properties
- Matte BSDF (roughness: 0.7)
- Subtle emission (0.1 strength)
- Mix shader blending (20% factor)
- Specularity: 0.2

### Lighting Setup
- Sun light: (10, -10, 10), energy: 3
- Area fill 1: (5, 5, 5), energy: 30, size: 12
- Area fill 2: (-5, -5, -5), energy: 30, size: 12

### Animation Features
- Saturn rotation: 0° to 180° over 240 frames
- Moon orbits: 360° × speed multiplier
- Cycles modifier for infinite looping
- Linear interpolation for smooth motion

### Camera Formula
```
CAM_DIST = RING_OUTER * 16 = 160
Position: (0, -150.4, 54.4)
```

### Final Output Message
```
✅ DONE: Saturn — Eevee optimized, matte material, rings, Sun + fills, stars bg, lens=55mm, major moons
```

---

## Uranus

### Overview
Renders Uranus with its unique extreme axial tilt and faint ring system.

### Key Settings
- **Uranus Radius**: 4.0
- **Uranus Tilt**: 97.8° (rotates on its side)
- **Ring Outer**: 8.0
- **Render Engine**: BLENDER_EEVEE
- **Animation**: 240 frames
- **Camera Lens**: 55mm

### Sphere Geometry
- High segment count for smooth appearance
- Shade smooth for realistic lighting

### Uranus Material
- Cyan-blue appearance from atmosphere
- Matte finish (roughness: 0.7)
- Subtle emission (0.1 strength)
- Mix shader (20% factor)

### Ring System
- **13 Faint Rings**: Procedural generation
- **Ring Style**: Torus geometry for each ring
- **Color**: Dark icy gray (0.2, 0.2, 0.2)
- **Transparency**: Low alpha values (~0.15)
- **Rotation**: Aligned with Uranus tilt (97.8°)

Inner ring structure (9 rings):
```
for i in range(9):
    inner = 4.5 + i*0.25
    outer = inner + 0.25
```

### Lighting
- Sun light with energy: 3
- Area fill lights for soft illumination
- Stars background environment

### Material Properties
- Very rough texture (roughness: 0.95)
- Minimal specularity (0.05)
- Transparent blend method
- No shadow casting

### Animation
- Standard 240-frame loop
- Linear interpolation
- Rotation based on axial tilt

---

## Venus

### Overview
Creates Venus with thick, glowing atmosphere and realistic surface conditions.

### Key Features
- Dense atmosphere simulation
- Bright atmospheric glow
- Advanced shader network
- High-quality rendering setup

### General Notes

All scripts share these common features:
- **Standard Animation**: 240 frames at linear interpolation
- **Universal Camera Lens**: 55mm
- **Standard Camera Formula**: `CAM_DIST = (radius or outer_ring) * 16`
- **Camera Position**: `(0, -CAM_DIST*0.94, CAM_DIST*0.34)`
- **Background**: Stars texture environment
- **Render Quality**: EEVEE for speed, CYCLES for quality

---

## Best Practices from This Collection

1. **Smooth Geometry**: High segment counts (128+) eliminate faceted appearance
2. **Material Layering**: Combine BSDF + emission for realistic depth
3. **Lighting Setup**: Key light + fill lights for comprehensive illumination
4. **Linear Animation**: Linear keyframe interpolation for consistent motion
5. **Uniform Camera**: Consistent lens (55mm) and formula across all planets
6. **Texture Colorspace**: sRGB for colors, Non-Color for bump maps
7. **Bloom Effects**: Effective for bright objects like Sun
8. **Atmospheric Layers**: Facing weight shaders for rim lighting effects
9. **Ring Systems**: Torus geometry or cylinder primitives with transparency
10. **Orbital Mechanics**: Empty objects as orbit centers with parented planets/moons

---

## Texture Requirements

Each script expects textures in: `C:\COLLEGE\THIRD TERM\MAA\Planets\textures\`

### Earth Textures
- earth_daymap
- earth_nightmap
- earth_clouds

### Jupiter Textures
- jupiter_map
- moon_io, moon_europa, moon_ganymede, moon_callisto

### Mars Textures
- mars_surface

### Mercury Textures
- mercury_color
- mercury_bump

### Neptune Textures
- neptune_map

### Sun Textures
- sun_surface

### Pluto Textures
- pluto_map
- pluto_bump
- charon_map

### Saturn Textures
- saturn_map
- saturn_rings
- moon_titan, moon_enceladus, moon_rhea

### Uranus Textures
- uranus_map

### Venus Textures
- (as per specific implementation)

### Universal
- stars (used by all scripts)

---

## Technical Specifications

### Rendering Engines Used
- **BLENDER_EEVEE**: Fast, real-time, supports bloom effects
- **CYCLES**: High-quality, GPU rendering (Mercury only)

### Standard Settings
- **TAA Render Samples**: 32-64
- **TAA Viewport Samples**: 16-32
- **Soft Shadows**: Enabled
- **Clip Start**: 0.01
- **Clip End**: 10000

### Material Techniques
- Principled BSDF for physically-based rendering
- Normal maps for surface detail
- Mix shaders for layered effects
- Emission for self-illumination
- Alpha blending for transparency

---

**Last Updated**: April 26, 2026
**Project**: Solar System Visualization in Blender
**Framework**: Python API (Blender 3.x+)
