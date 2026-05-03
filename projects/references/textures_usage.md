# Texture Usage Directory

This document provides a comprehensive mapping of every texture file required by each Python script in the Solar System Animation Suite. 

> All scripts attempt to load textures from the configured directory: `C:\COLLEGE\THIRD TERM\MAA\Planets\textures\`

---

## 1. `sun.py`
* **`sun_map.jpg`**: Base color map used in conjunction with the high-strength emission shader to create the glowing corona.
* **`stars.jpg`**: Used in the World shader for the deep space environment background.

## 2. `mercury.py`
* **`mercury_map.jpg`**: The primary color map for the rocky surface.
* **`mercury_bump.jpg`**: Used to physically indent the craters and ridges.
* **`stars.jpg`**: Environment background.

## 3. `venus.py`
* **`venus_map.jpg`**: Base color map representing the dense, toxic cloud cover.
* **`venus_bump.jpg`**: Subtle bump map to give depth to the atmospheric storms.
* **`stars.jpg`**: Environment background.

## 4. `earth.py`
* **`earth_map.jpg`**: The primary diffuse/color map for landmasses and oceans.
* **`earth_specular.jpg`**: Black-and-white mask used to make the oceans reflective while keeping the landmasses matte.
* **`earth_bump.jpg`**: Normal/bump map to give physical height to mountain ranges.
* **`earth_clouds.jpg`**: An alpha-masked texture applied to a slightly larger secondary sphere to create volumetric clouds.
* **`moon_surface.jpg`**: Color map applied to Luna.
* **`moon_bump.jpg`**: Bump map applied to Luna's craters.
* **`stars.jpg`**: Environment background.

## 5. `mars.py`
* **`mars_map.jpg`**: The red, dusty primary color map.
* **`mars_bump.jpg`**: Deep bump map to highlight the massive Valles Marineris canyon and Olympus Mons volcano.
* **`moon_surface.jpg`**: Used as a fallback surface texture for the captured asteroid moons (Phobos and Deimos).
* **`stars.jpg`**: Environment background.

## 6. `jupiter.py`
* **`jupiter_map.jpg`**: The primary gas giant banding map (including the Great Red Spot).
* **`io_map.jpg`**: Specific surface texture for the volcanic moon Io.
* **`europa_map.jpg`**: Specific surface texture for the icy moon Europa.
* **`ganymede_map.jpg`**: Specific surface texture for Ganymede.
* **`callisto_map.jpg`**: Specific surface texture for Callisto.
* **`stars.jpg`**: Environment background.

## 7. `saturn.py`
* **`saturn_map.jpg`**: The primary gas giant color map.
* **`saturn_rings.png`**: An Alpha-Blend texture mapped radially to a flat disc to render the massive ice rings and cast physical shadows.
* **`moon_surface.jpg`**: Generic fallback surface texture used for Titan and Enceladus.
* **`stars.jpg`**: Environment background.

## 8. `uranus.py`
* **`uranus_map.jpg`**: The pale blue base map (enhanced procedurally with noise banding).
* **`uranus_rings.png`**: Alpha-Blend texture mapped radially (enhanced with procedural alpha multipliers to make them realistically faint).
* **`moon_surface.jpg`**: Applied to the 5 major vertical moons (Titania, Oberon, Umbriel, Ariel, Miranda).
* **`stars.jpg`**: Environment background.

## 9. `neptune.py`
* **`neptune_map.jpg`**: The deep cobalt blue primary color map.
* **`moon_surface.jpg`**: Applied to the retrograde moon Triton and minor moons.
* **`stars.jpg`**: Environment background.
* *(Note: `neptune_rings.png` is no longer required, as Neptune's rings are now generated 100% procedurally via 3D Torus meshes!)*

## 10. `pluto.py`
* **`pluto_map.jpg`**: The base color map featuring the famous "heart" shape (Tombaugh Regio).
* **`pluto_bump.jpg`**: Bump map to highlight the icy mountain ranges.
* **`moon_surface.jpg`**: Generic rocky texture applied to the massive binary moon Charon, as well as Styx, Nix, Kerberos, and Hydra.
* **`stars.jpg`**: Environment background.
