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

var ring_origins: Array[Transform3D] = []
var gas_age := -1.
var gas_power := 0.
var dispersing := false
var gas_direction := Vector3.UP

func start_gas_impact(direction: Vector3, power: float, full: bool) -> void:
	if ring_origins.is_empty():
		var grains: MultiMesh=$SpinPivot/RingSystem/RingDebris.multimesh
		for i in grains.instance_count: ring_origins.append(grains.get_instance_transform(i))
	gas_age=0.
	gas_power=power
	gas_direction=direction
	dispersing=full
	$SpinPivot/RingSystem/RingMesh.visible=not full

func advance(delta: float, sun_dir: Vector3) -> void:
	super(delta,sun_dir)
	if gas_age<0.: return
	gas_age+=delta
	var frame: Node3D=$SpinPivot/RingSystem
	frame.get_node("RingMesh").rotation.x=sin(gas_age*2.2)*.14*gas_power*exp(-gas_age*.4)
	var grains: MultiMesh=frame.get_node("RingDebris").multimesh
	for i in grains.instance_count:
		var at:=ring_origins[i]
		var axis:=at.origin.normalized()
		var drift:=(axis+gas_direction*.23+Vector3.UP*sin(i*13.7)*.42)*gas_power*(1.4+sin(i*.35))
		at.origin+=drift*gas_age*(1. if dispersing else exp(-gas_age*.6))
		grains.set_instance_transform(i,at)
	if dispersing:
		surface_mesh.scale=Vector3.ONE*maxf(.001,1.-gas_age*.72)
		frame.get_node("Stations").hide()
	if gas_age>=8.: finish_gas_impact()

func finish_gas_impact() -> void:
	gas_age=-1.
	if dispersing:
		surface_mesh.hide()
		$SpinPivot/RingSystem.hide()
	else: restore_gas()

func restore_gas() -> void:
	gas_age=-1.
	dispersing=false
	surface_mesh.scale=Vector3.ONE
	surface_mesh.show()
	$SpinPivot/RingSystem.show()
	$SpinPivot/RingSystem/RingMesh.show()
	$SpinPivot/RingSystem/RingMesh.rotation=Vector3.ZERO
	$SpinPivot/RingSystem/Stations.show()
	var grains: MultiMesh=$SpinPivot/RingSystem/RingDebris.multimesh
	for i in ring_origins.size(): grains.set_instance_transform(i,ring_origins[i])
