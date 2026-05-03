# Solar System Animation Suite — Scientific References

This document outlines the primary references used to construct the procedural generation and animation scripts for all celestial bodies in the Blender Solar System showcase.

## The Sun
**Reference:** [NASA Sun Facts](https://science.nasa.gov/sun/facts/)
**Facts Implemented:**
* **Scale & Visuals:** The massive central star of our solar system, implemented using a powerful emission shader and volumetric scattering to create a blinding, glowing corona of plasma.
* **Lighting:** Acts as the primary "true sunlight" source for the entire solar system simulation, casting sharp, deep-space shadows across all orbiting bodies.

## Mercury
**Reference:** [NASA Mercury Facts](https://science.nasa.gov/mercury/facts/)
**Facts Implemented:**
* **Rotation:** Mercury has an incredibly slow rotation (one day is 59 Earth days). Its rotation in the timeline was scaled to be drastically slower than the baseline 360-frame loop used for Earth.
* **Atmosphere:** Mercury has essentially no atmosphere, so it was modeled with a completely bare, highly cratered rocky surface with zero atmospheric haze or Fresnel glow.

## Venus
**Reference:** [NASA Venus Facts](https://science.nasa.gov/venus/facts/)
**Facts Implemented:**
* **Retrograde Spin:** Venus spins extremely slowly *and* backward (retrograde). It takes 243 Earth days to rotate once!
* **Atmosphere:** Modeled with a highly matte, completely opaque shader to replicate its extremely dense, toxic, thick cloud cover that completely obscures its surface.

## Earth
**Reference:** [NASA Earth Facts](https://science.nasa.gov/earth/facts/)
**Facts Implemented:**
* **The Baseline:** Earth's 24-hour day was used as the mathematical baseline for the entire suite, taking exactly **360 frames** (15 frames per hour) to complete one perfect loop.
* **Materials:** Complex shading separating the matte landmasses from the highly specular and reflective liquid oceans, overlaid with a separate procedural cloud sphere.
* **The Moon (Luna):** Tidally locked to Earth, orbiting once every ~27 days, correctly scaled to showcase its relative proximity and size.

## Mars
**Reference:** [NASA Mars Facts](https://science.nasa.gov/mars/facts/)
**Facts Implemented:**
* **Moons:** Modeled its two tiny, captured-asteroid moons, **Phobos and Deimos**, buzzing in close orbits around the planet.
* **Visuals:** Implemented deep bump mapping to highlight its dusty, cratered red surface, canyons, and mountains, surrounded by a very thin atmospheric glow.
* **Timeline:** Mars has a day length very similar to Earth's (just over 24 hours), so its timeline speed is almost identical to the 360-frame baseline.

## Jupiter
**Reference:** [NASA Jupiter Facts](https://science.nasa.gov/jupiter/jupiter-facts/)
**Facts Implemented:**
* **Moons:** Jupiter has 95 known moons. To keep the scene performant while maintaining scale, the script models the 4 major Galilean moons (Io, Europa, Ganymede, Callisto) along with a cinematic swarm of minor procedural moons.
* **Rotation:** As the fastest spinning planet in our solar system, its rotational timeline was matched proportionally against Earth's 24-hour cycle.

## Saturn
**Reference:** [NASA Saturn Facts](https://science.nasa.gov/saturn/facts/)
**Facts Implemented:**
* **Axial Tilt:** Saturn's 26.7-degree tilt was implemented via a master pivot.
* **Ring System:** NASA data informed the scale, density, and shadowing logic of the massive ice rings, ensuring they cast physically accurate contact shadows onto the planet's atmosphere.

## Uranus
**Reference:** [NASA Uranus Facts](https://science.nasa.gov/uranus/facts/)
**Facts Implemented:**
* **Sideways Spin:** Uranus spins almost perfectly on its side. Implemented its famous **97.77-degree axial tilt**, creating the iconic "rolling barrel" view with perfectly vertical rings relative to its orbit.
* **Timeline:** A 17-hour day, translated mathematically into a **255-frame** perfect loop.
* **Moons:** Modeled the 5 largest moons (Titania, Oberon, Umbriel, Ariel, Miranda) orbiting vertically along the tilted equator.

## Neptune
**Reference:** [NASA Neptune Facts](https://science.nasa.gov/neptune/neptune-facts/)
**Facts Implemented:**
* **Retrograde Moon:** Neptune's largest moon, Triton, is the only large moon in the solar system that orbits backward. This was implemented via a negative rotation ratio.
* **Distinct Rings:** Using Voyager 2 photographic data, the rings were modeled as multiple physically separated, extremely thin, and dusty 3D wireframes (specifically Adams, Le Verrier, and Galle rings).
* **Visuals:** A vivid, deep cobalt blue atmosphere, standing in stark contrast to Uranus.

## Pluto
**Reference:** [NASA Pluto Facts](https://science.nasa.gov/dwarf-planets/pluto/facts/)
**Facts Implemented:**
* **Binary System:** Charon is so massive (half the size of Pluto) that it acts as a binary system. Charon is tidally locked, meaning its orbit perfectly matches Pluto's rotation speed.
* **Extreme Tilt:** Pluto spins retrograde on its side with a **122.5-degree** axial tilt.
* **Atmosphere:** Inspired by the New Horizons probe discovery, a tenuous glowing "blue haze" was integrated natively into the planet's Fresnel shader.
* **Lighting:** Because it resides deep in the Kuiper Belt, the sun's energy was drastically reduced to create extremely dim, deep-space lighting.
