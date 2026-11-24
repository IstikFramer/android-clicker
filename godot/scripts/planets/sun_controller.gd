extends PlanetController

var arcs: Array[MeshInstance3D] = []

func _ready() -> void:
	super()
	var loop := TorusMesh.new()
	loop.inner_radius=.70
	loop.outer_radius=.80
	loop.rings=32
	loop.ring_segments=6
	var glow := StandardMaterial3D.new()
	glow.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	glow.albedo_color=Color("#ff8532")
	for i in range(6):
		var arc := MeshInstance3D.new()
		arc.name="Prominence%d" % i
		arc.mesh=loop
		arc.material_override=glow
		var angle := TAU*i/6.0
		arc.position=Vector3(cos(angle),sin(i*2.1)*.44,sin(angle)).normalized()*9.95
		arc.rotation.y=-angle
		$SpinPivot.add_child(arc)
		arcs.append(arc)

func advance(delta: float, sun_dir: Vector3) -> void:
	super(delta,sun_dir)
	for i in range(arcs.size()):
		arcs[i].scale=Vector3(1.25+.36*sin(elapsed*.32+i),1,.63)
