extends PlanetController

func _ready() -> void:
	super()
	var frame := Node3D.new()
	frame.name = "RingSystem"
	$SpinPivot.add_child(frame)
	frame.rotation_degrees = Vector3(12,0,21)
	var bands := add_model("SaturnRings",frame,Vector3.ZERO,definition.visual_radius)
	bands.name = "RingMesh"
	for node in bands.find_children("*","MeshInstance3D",true,false):
		node.material_override = material(preload("res://shaders/saturn_rings.gdshader"),{})
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if is_backdrop:
		return
	var shell := MeshInstance3D.new()
	shell.name = "InnerGasShells"
	shell.mesh = sphere(1)
	shell.material_override = material(GAS,{"tint":definition.accent,"belt":Color("#975e39")})
	shell.scale = Vector3.ONE*definition.visual_radius*.90
	shell.hide()
	$SpinPivot.add_child(shell)
	var stations := Node3D.new()
	stations.name = "Stations"
	frame.add_child(stations)
	for i in range(3):
		var a := i*TAU/3+.2
		add_model("SaturnStation",stations,Vector3(cos(a)*18,.6,sin(a)*18),.56)
	var grains := MultiMesh.new()
	grains.transform_format = MultiMesh.TRANSFORM_3D
	var chip := BoxMesh.new()
	chip.size = Vector3(.075,.045,.14)
	var ice := StandardMaterial3D.new()
	ice.albedo_color = Color("#dac6a9")
	chip.material = ice
	grains.mesh = chip
	grains.instance_count = 320
	var rng := RandomNumberGenerator.new()
	rng.seed = 71023
	for i in range(grains.instance_count):
		var a := rng.randf()*TAU
		var radius := rng.randf_range(12.4,20.8)
		grains.set_instance_transform(i,Transform3D(Basis(Vector3.UP,a),Vector3(cos(a)*radius,rng.randf_range(-.09,.09),sin(a)*radius)))
	var debris := MultiMeshInstance3D.new()
	debris.name = "RingDebris"
	debris.multimesh = grains
	frame.add_child(debris)
