extends PlanetController

func make_surface() -> ShaderMaterial:
	CountryLookup.initialize()
	return material(preload("res://shaders/earth_surface.gdshader"), {
		"cloud_map":definition.cloud_map,"day_map":definition.day_map,"night_map":definition.night_map,"ocean_mask":definition.ocean_mask})

func advance(delta: float, sun_dir: Vector3) -> void:
	super(delta,sun_dir)
	surface.set_shader_parameter("u_time",elapsed)
	surface.set_shader_parameter("sun_dir_local",sun_local)

func region_at(direction: Vector3) -> Dictionary:
	return CountryLookup.region(direction)
