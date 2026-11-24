class_name PlanetController
extends Node3D

@export var definition: PlanetDefinition
var is_backdrop := false
var sun_local: Vector3
var elapsed := 0.0
var detail := -1
var surface: ShaderMaterial
var clouds: ShaderMaterial
var rim: ShaderMaterial
var marker: MeshInstance3D
var local_hit_dir := Vector3.ZERO
var destroyed := false
var spin_locked := false
var quality_level := -1
static var spheres: Dictionary[Vector2, SphereMesh] = {}
@onready var surface_mesh: MeshInstance3D = $SpinPivot/Surface
const SEGMENTS := [32, 48, 96, 128]
const ROCK := preload("res://shaders/planet_surface.gdshader")
const GAS := preload("res://shaders/gas_giant.gdshader")
const SOLAR := preload("res://shaders/sun_surface.gdshader")
const CLOUD := preload("res://shaders/clouds.gdshader")
const AIR := preload("res://shaders/atmosphere.gdshader")
const CORONA := preload("res://shaders/solar_corona.gdshader")

func material(shader: Shader, parameters: Dictionary) -> ShaderMaterial:
	var result := ShaderMaterial.new()
	result.shader = shader
	for key in parameters:
		result.set_shader_parameter(key, parameters[key])
	return result

func make_surface() -> ShaderMaterial:
	match definition.type:
		"gas": return material(GAS, {"tint":definition.tint,"belt":definition.accent,"storm":definition.id == &"jupiter"})
		"star": return material(SOLAR, {})
	var style := 2 if definition.id == &"mars" else (1 if definition.id == &"venus" else 0)
	return material(ROCK, {"tint":definition.tint,"geology":style})

func _ready() -> void:
	var r := definition.visual_radius
	surface = make_surface()
	setup_layer(surface_mesh, surface, r)
	if definition.type == "gas":
		surface_mesh.name = "GasSphere"
	if is_backdrop:
		$SpinPivot/AimArea.free()
	else:
		var collision := SphereShape3D.new()
		collision.radius = r
		$SpinPivot/AimArea/CollisionShape3D.shape = collision
		make_marker()
	if definition.id != &"mercury":
		var size_ratio := 1.025
		match definition.id:
			&"mars": size_ratio = 1.014
			&"venus": size_ratio = 1.052
			&"sun": size_ratio = 1.20
		rim = material(CORONA, {}) if definition.type == "star" else material(AIR, {"tint":definition.accent})
		setup_layer($SpinPivot/Atmosphere, rim, r*size_ratio)
	if definition.cloud_map:
		var venus := definition.id == &"venus"
		clouds = material(CLOUD, {"cloud_map":definition.cloud_map, "tint":definition.accent if venus else Color.WHITE,
			"density":0.94 if venus else (0.16 if definition.id == &"mars" else 0.82),
			"cover":0.85 if venus else 0.0})
		setup_layer($SpinPivot/Clouds, clouds, r*1.008)
	if definition.type == "rocky" and not is_backdrop:
		for layer in [$SpinPivot/Core, $SpinPivot/Mantle]:
			var interior := StandardMaterial3D.new()
			interior.albedo_color = Color("#ffb14d") if layer == $SpinPivot/Core else Color("#63291e")
			setup_layer(layer, interior, r*(0.47 if layer == $SpinPivot/Core else 0.86))
			layer.hide()
		var props := {"mercury":"MercuryStation", "mars":"MarsDomes"}
		if props.has(definition.id):
			add_model(props[definition.id], $SpinPivot/Markers, Vector3(0.82,0.54,0.20).normalized()*r, 0.28)
	set_detail(0 if is_backdrop else 2)
	apply_quality(0 if is_backdrop else int(get_node("/root/Settings").values.quality))

func setup_layer(node: MeshInstance3D, mat: Material, radius: float) -> void:
	node.mesh = sphere(0,radius)
	node.material_override = mat
	node.show()
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

static func sphere(level: int, radius := 1.0) -> SphereMesh:
	var key := Vector2(level,radius)
	if not spheres.has(key):
		var mesh := SphereMesh.new()
		mesh.radius = radius
		mesh.height = 2.0*radius
		mesh.radial_segments = SEGMENTS[level]
		mesh.rings = SEGMENTS[level]/2
		spheres[key] = mesh
	return spheres[key]

func set_detail(level: int) -> void:
	if level == detail:
		return
	detail = level
	for layer in [surface_mesh,$SpinPivot/Atmosphere,$SpinPivot/Clouds,$SpinPivot/Core,$SpinPivot/Mantle]:
		if layer.material_override:
			layer.mesh = sphere(level, layer.mesh.radius)

func apply_quality(level: int) -> void:
	if level==quality_level: return
	quality_level=level
	for mat in [surface,clouds,rim]:
		if mat: mat.set_shader_parameter("quality_level",level)
	if rim and definition.type!="star":
		$SpinPivot/Atmosphere.scale=Vector3.ONE*(1.+.004*level)

func update_lod(radius_pixels: float, quality: int) -> void:
	if is_backdrop:
		return
	apply_quality(quality)
	var next := detail
	if radius_pixels < 76.0:
		next = 1
	elif radius_pixels > 100.0 and detail < 2:
		next = 2
	if radius_pixels > 280.0:
		next = 3
	elif radius_pixels < 230.0 and next == 3:
		next = 2
	set_detail(clampi(next,1,mini(3,quality+1)))

func make_marker() -> void:
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color("#ffb76a")
	var ring := TorusMesh.new()
	ring.inner_radius = 0.20
	ring.outer_radius = 0.27
	ring.rings = 32
	ring.ring_segments = 8
	marker = MeshInstance3D.new()
	marker.mesh = ring
	marker.material_override = mat
	$SpinPivot/Markers.add_child(marker)
	marker.hide()

func set_hit(direction: Vector3) -> void:
	local_hit_dir = direction
	marker.visible = direction != Vector3.ZERO
	if marker.visible:
		marker.position = direction*definition.visual_radius*1.013
		marker.quaternion = Quaternion(Vector3.UP,direction)

func hit_direction(origin: Vector3, ray: Vector3) -> Vector3:
	var spin: Node3D = $SpinPivot
	return CountryLookup.geometry.pick_globe(spin.to_local(origin), spin.global_basis.inverse()*ray, definition.visual_radius)

func world_direction(direction: Vector3) -> Vector3:
	return ($SpinPivot.global_basis * direction).normalized()

func advance(delta: float, sun_dir: Vector3) -> void:
	elapsed += delta
	if not spin_locked: $SpinPivot.rotate_y(definition.rotation_rate*delta)
	sun_local = ($SpinPivot.global_basis.inverse()*sun_dir).normalized()
	if definition.type != "rocky":
		surface.set_shader_parameter("u_time",elapsed)
	if clouds:
		clouds.set_shader_parameter("u_time",elapsed)
		clouds.set_shader_parameter("sun_dir_local",sun_local)
	if rim:
		if definition.type == "star":
			rim.set_shader_parameter("u_time",elapsed)
		else:
			rim.set_shader_parameter("sun_dir_local",sun_local)

func set_destroyed(value: bool) -> void:
	destroyed = value
	$SpinPivot.visible = not value
	if not is_backdrop:
		$SpinPivot/AimArea.collision_layer = 0 if value else 2

func add_model(model_name: String, parent: Node3D, pos: Vector3, size: float) -> Node3D:
	var model: Node3D = load("res://assets/models/%s.glb" % model_name).instantiate()
	parent.add_child(model)
	model.position = pos
	model.scale = Vector3.ONE*size
	if pos != Vector3.ZERO:
		model.quaternion = Quaternion(Vector3.UP,pos.normalized())
	return model
