class_name RailgunPlatform
extends Node3D

var muzzle: Node3D
var recoil: Node3D
var warp_origin: Node3D
var anchor: Node3D
var coils: Array[MeshInstance3D]=[]
var engine_face:=ShaderMaterial.new()
var signal_strip: ShaderMaterial
var bolt: MeshInstance3D
var flash: MeshInstance3D
var arc: MeshInstance3D
var trail: MeshInstance3D
var start_point:=Vector3.ZERO
var cool:=Color("#77e6ff")
var hot:=Color("#ffb868")

func glow(color: Color) -> StandardMaterial3D:
	var mat:=StandardMaterial3D.new()
	mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color=color
	return mat

func sphere_fx(parent: Node3D, shade: Color, size: float) -> MeshInstance3D:
	var node:=MeshInstance3D.new()
	node.mesh=PlanetController.sphere(0,size)
	node.material_override=glow(shade)
	node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(node)
	return node

func _ready() -> void:
	var model_id:="Railgun" if Settings.values.quality>=2 else "RailgunMedium"
	var model: Node3D=load("res://assets/models/%s.glb"%model_id).instantiate()
	add_child(model)
	recoil=model.find_child("RecoilPivot",true,false)
	muzzle=model.find_child("Muzzle",true,false)
	anchor=model.find_child("CameraAnchor",true,false)
	warp_origin=model.find_child("WarpOrigin",true,false)
	dress_platform(model)
	var face:=MeshInstance3D.new()
	var nozzle:=QuadMesh.new()
	nozzle.size=Vector2.ONE*1.64
	face.mesh=nozzle
	engine_face.shader=preload("res://shaders/engine_face.gdshader")
	face.material_override=engine_face
	face.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	warp_origin.add_child(face)
	$WarpEngineFX.top_level=true
	for i in 8:
		var node:=MeshInstance3D.new()
		var ring:=TorusMesh.new()
		ring.inner_radius=.51
		ring.outer_radius=.555
		ring.rings=32
		ring.ring_segments=6
		node.mesh=ring
		node.material_override=glow(cool)
		node.rotation.x=PI*.5
		node.position.z=1.45-i*.43
		node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		recoil.add_child(node)
		coils.append(node)
	arc=MeshInstance3D.new()
	var ribbon:=QuadMesh.new()
	ribbon.size=Vector2(1.0,4.45)
	arc.mesh=ribbon
	arc.rotation.x=-PI*.5
	arc.position=Vector3(0,.31,-1.75)
	var electricity:=ShaderMaterial.new()
	electricity.shader=preload("res://shaders/rail_arc.gdshader")
	arc.material_override=electricity
	recoil.add_child(arc)
	flash=sphere_fx(muzzle,Color("#e3ffff"),.5)
	bolt=sphere_fx(self,cool,.16)
	trail=sphere_fx(self,Color("#a2eaff"),.09)
	bolt.top_level=true
	trail.top_level=true
	$PulseLight.position=muzzle.position
	configure_particles($ChargeFX/Sparks,Vector3(0,.2,-1),2.8,.075)
	configure_particles($WarpEngineFX/Stars,Vector3.BACK,23.,.07)
	$WarpEngineFX/Stars.position.z=-12.
	$WarpEngineFX/Stars.process_material.emission_shape=ParticleProcessMaterial.EMISSION_SHAPE_BOX
	$WarpEngineFX/Stars.process_material.emission_box_extents=Vector3(7.,5.,1.)
	$ChargeFX/Sparks.position=muzzle.position
	cancel_sequence()

func dress_platform(model: Node3D) -> void:
	var materials: Dictionary={}
	for part: MeshInstance3D in model.find_children("*","MeshInstance3D",true,false):
		for i in part.mesh.get_surface_count():
			var base:=part.mesh.surface_get_material(i) as StandardMaterial3D
			if not base: continue
			if not materials.has(base):
				var skin:=ShaderMaterial.new()
				skin.shader=preload("res://shaders/platform_hull.gdshader")
				skin.set_shader_parameter("paint",base.albedo_color)
				skin.set_shader_parameter("finish",2. if base.emission_enabled else base.metallic)
				if base.emission_enabled: signal_strip=skin
				materials[base]=skin
			part.set_surface_override_material(i,materials[base])

func drive(value: float) -> void:
	engine_face.set_shader_parameter("drive",value)
	if signal_strip: signal_strip.set_shader_parameter("drive",value)

func configure_particles(node: GPUParticles3D, direction: Vector3, speed: float, radius: float) -> void:
	var pm:=ParticleProcessMaterial.new()
	pm.direction=direction
	pm.spread=24.
	pm.gravity=Vector3.ZERO
	pm.initial_velocity_min=speed*.52
	pm.initial_velocity_max=speed
	node.process_material=pm
	var mesh:=SphereMesh.new()
	mesh.radius=radius
	mesh.height=radius*3.
	mesh.radial_segments=6
	mesh.rings=3
	mesh.material=glow(cool)
	node.draw_pass_1=mesh

func get_valid_targets() -> Array:
	return TargetRegistry.STANDARD

func can_fire(request: ShotRequest) -> bool:
	return request!=null and request.weapon_id==&"railgun" and request.is_valid() and request.target_id in get_valid_targets()

func begin_travel(t: float, intensity: float) -> void:
	drive(intensity)
	var camera:=get_viewport().get_camera_3d()
	if camera and intensity>.015: $WarpEngineFX.global_transform=camera.global_transform
	$WarpEngineFX.visible=intensity>.015
	$WarpEngineFX/Stars.emitting=intensity>.18
	var shader: ShaderMaterial=$WarpEngineFX/Tunnel.material_override
	shader.set_shader_parameter("progress",t)
	shader.set_shader_parameter("intensity",intensity)
	shader.set_shader_parameter("compress",sin(t*PI))
	shader.set_shader_parameter("direction",1. if t<.5 else -.5)

func charge(t: float, elapsed: float, power: float) -> void:
	drive(t)
	for i in coils.size():
		var wave:=.5+.5*sin(elapsed*(8.+power*5.)-i*.93)
		coils[i].visible=t>.01
		coils[i].material_override.albedo_color=cool*(.18+wave*t*1.6)
	arc.visible=true
	arc.material_override.set_shader_parameter("charge",t*(.48+.52*power))
	arc.material_override.set_shader_parameter("clock",elapsed)
	$ChargeFX/Sparks.emitting=t>.16
	$ChargeFX/Sparks.amount_ratio=clampf(.12+power*t,0.,1.)

func pulse() -> void:
	drive(1.)
	start_point=muzzle.global_position
	$ChargeFX/Sparks.emitting=false
	arc.hide()
	for coil in coils: coil.hide()
	bolt.show()
	trail.show()

func flight(t: float, elapsed: float, endpoint: Vector3, center: Vector3, radius: float, profile: Dictionary) -> void:
	var kick: float=sin(clampf(elapsed/.3,0.,1.)*PI)*profile.recoil
	recoil.position.z=kick
	flash.visible=elapsed<.12
	flash.scale=Vector3(1,1,2.3)*maxf(.001,1.-elapsed/.12)*(1.+profile.flash)
	$PulseLight.light_energy=maxf(0.,1.-elapsed/.12)*2.7
	var point:=start_point.lerp(endpoint,t)
	var last:=start_point.lerp(endpoint,maxf(0.,t-.115))
	var dir:=endpoint-start_point
	bolt.global_position=point
	bolt.material_override.albedo_color=hot if point.distance_to(center)<=radius*1.04 else cool
	trail.global_position=(point+last)*.5
	if dir.length_squared()>.01:
		var up:=Vector3.UP if absf(dir.normalized().dot(Vector3.UP))<.98 else Vector3.RIGHT
		trail.global_basis=Basis.looking_at(dir.normalized(),up).scaled_local(Vector3(1,1,maxf(.001,point.distance_to(last)/.18)))
	trail.material_override.albedo_color=bolt.material_override.albedo_color

func set_paused(paused: bool) -> void:
	for node in [$ChargeFX/Sparks,$WarpEngineFX/Stars]: node.speed_scale=0. if paused else 1.
	for node in [$ChargeAudio,$MuzzleAudio,$ImpactAudio]: node.stream_paused=paused

func cancel_sequence() -> void:
	drive(0.)
	recoil.position.z=0.
	for node in coils: node.hide()
	for node in [arc,flash,bolt,trail,$WarpEngineFX]: node.hide()
	$ChargeFX/Sparks.emitting=false
	$WarpEngineFX/Stars.emitting=false
	$PulseLight.light_energy=0.
	for node in [$ChargeAudio,$MuzzleAudio,$ImpactAudio]: node.stop()
	set_paused(false)
