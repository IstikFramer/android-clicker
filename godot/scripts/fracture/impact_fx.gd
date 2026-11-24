extends Node3D

const PARTICLES := ["Ejecta","Dust","Fire","Smoke","Sparks","ExitPlume"]
var age := -1.0
var duration := 0.
var power := 0.
var radius := 1.
var strength := 1.

func _ready() -> void:
	for label in PARTICLES:
		var cloud := get_node(label) as GPUParticles3D
		var pm := ParticleProcessMaterial.new()
		pm.direction = Vector3.UP
		pm.gravity = Vector3.ZERO
		pm.spread = 58. if label!="ExitPlume" else 22.
		pm.damping_min = .1
		pm.damping_max = .7
		pm.scale_min = .35
		pm.scale_max = 1.3
		var ramp := GradientTexture1D.new()
		ramp.gradient = Gradient.new()
		pm.color_ramp = ramp
		cloud.process_material = pm
		if label=="Ejecta":
			var shard := PrismMesh.new()
			shard.size = Vector3(.16,.32,.15)
			var stone := StandardMaterial3D.new()
			stone.vertex_color_use_as_albedo = true
			shard.material=stone
			cloud.draw_pass_1 = shard
		else:
			var sprite := QuadMesh.new()
			sprite.size = Vector2.ONE*(.74 if label in ["Dust","Smoke"] else .48)
			var mat := ShaderMaterial.new()
			mat.shader = preload("res://shaders/ejecta.gdshader")
			sprite.material = mat
			cloud.draw_pass_1 = sprite
	clear()

func clear() -> void:
	age = -1.
	hide()
	for label in PARTICLES:
		get_node(label).emitting = false
	for mesh in [$Crater,$Flash,$Shockwave,$FractureCloud]: mesh.hide()

func play(planet: PlanetController, direction: Vector3, plan: Dictionary, p: int, weapon: StringName) -> void:
	clear()
	show()
	var def := planet.definition
	var normal := planet.world_direction(direction)
	radius = def.visual_radius
	global_transform = Transform3D(Basis(Quaternion(Vector3.UP,normal)),planet.global_position+normal*radius)
	age = 0.
	duration = plan.heat_seconds
	strength = plan.wave_intensity
	power = float(p)/100.
	var dust := Color("#cdad82")
	if def.id == &"mars": dust=Color("#cc7548")
	if def.id == &"mercury": dust=Color("#aba99d")
	if def.id == &"venus": dust=Color("#ffc067")
	var station_near := direction.dot(Vector3(.82,.54,.20).normalized())>.92
	for i in PARTICLES.size():
		var label: String = PARTICLES[i]
		var cloud := get_node(label) as GPUParticles3D
		if label=="ExitPlume" and (def.type!="gas" or weapon!=&"gungnir"): continue
		if label=="Ejecta" and def.type!="rocky": continue
		if label=="Fire" and def.id==&"mercury" and not station_near: continue
		if label=="Smoke" and (def.id==&"mercury" or p<35): continue
		var pm := cloud.process_material as ParticleProcessMaterial
		var smoke := label in ["Smoke","Dust"]
		var hot := Color("#fff3b5") if not smoke else dust
		var mid := Color("#f27a32") if not smoke else dust.darkened(.19)
		if label=="Smoke": mid=Color("#55515a")
		var ramp := pm.color_ramp as GradientTexture1D
		ramp.gradient.offsets = PackedFloat32Array([0,.38,1.])
		ramp.gradient.colors = PackedColorArray([Color(hot.r,hot.g,hot.b,.43 if smoke else 1.),Color(mid.r,mid.g,mid.b,.32 if smoke else .85),Color(mid.r,mid.g,mid.b,0)])
		pm.initial_velocity_min = plan.ejecta_speed*(.18 if smoke else .6)
		pm.initial_velocity_max = plan.ejecta_speed*(.75 if smoke else 1.48)
		pm.scale_max = (.72+power)*(1.7 if smoke else 1.)
		cloud.lifetime = (2.5+1.3*power) if smoke else (1.1+power)
		cloud.amount = maxi(4,int((10.+56.*power)*(.45+.45*int(Settings.values.particles))))
		cloud.position = Vector3.DOWN*2.*radius if label=="ExitPlume" else Vector3.ZERO
		cloud.rotation = Vector3(PI if label=="ExitPlume" else 0.,0.,0.)
		cloud.restart()
	$Crater.visible = def.type=="rocky" and not plan.destroyed
	$Crater.scale = Vector3.ONE*radius*sqrt(plan.damage_fraction)*.86
	$Flash.show()
	$Shockwave.show()
	$FractureCloud.show()
	$FractureCloud.position = Vector3.DOWN*radius if plan.annihilate else Vector3.ZERO
	update_meshes()

func update_meshes() -> void:
	var wave := .18+age*(3.+power*8.)
	$Shockwave.scale=Vector3.ONE*wave
	$Shockwave.material_override.set_shader_parameter("strength",maxf(0.,1.-age/2.3)*.81)
	$FractureCloud.scale=Vector3.ONE*(.12+age*(3.+strength*3.))
	$FractureCloud.material_override.set_shader_parameter("strength",maxf(0.,.30-age*.13))
	$Flash.scale=Vector3.ONE*(.28+power*1.6+age*3.)
	$Flash.material_override.set_shader_parameter("strength",maxf(0.,1.-age*2.8))
	$Crater.material_override.set_shader_parameter("heat",maxf(0.,1.-age/duration))

func _process(delta: float) -> void:
	if age<0. or GameState.director.state==ShotDirector.State.PAUSED: return
	age+=delta
	if age>duration+1.:
		clear()
	else:
		update_meshes()
