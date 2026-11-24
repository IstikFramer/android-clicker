extends Node3D

const PARTICLES := ["Ejecta","Dust","Fire","Smoke","Sparks","ExitPlume"]
var age := -1.0
var duration := 0.
var power := 0.
var radius := 1.
var strength := 1.

var vapor:=MeshInstance3D.new()
var height:=1.
var width:=1.
var visual: Dictionary
var haze:=0.

func _ready() -> void:
	vapor.mesh=PlanetController.sphere(1,.5)
	vapor.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var vapor_skin:=ShaderMaterial.new()
	vapor_skin.shader=preload("res://shaders/vapor_column.gdshader")
	vapor.material_override=vapor_skin
	add_child(vapor)
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
	vapor.hide()
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
	visual=RailBalance.sample(maxi(10,p))
	var shape: Vector3={&"earth":Vector3(1.1,1.7,.50),&"venus":Vector3(1.35,2.75,.79),
		&"mars":Vector3(.43,3.6,.76),&"mercury":Vector3(.90,.60,.13),
		&"saturn":Vector3(3.7,1.25,.86)}.get(def.id,Vector3.ONE)
	height=shape.x
	width=shape.y
	haze=shape.z
	if def.id==&"earth": dust=Color("#bad7dd")
	if def.id==&"saturn": dust=Color("#ffe5a6")
	vapor.visible=def.type!="star"
	vapor.material_override.set_shader_parameter("pigment",dust)
	vapor.material_override.set_shader_parameter("curl",width)
	for mesh in [$Shockwave,$Flash,$FractureCloud]: mesh.material_override.set_shader_parameter("tint",dust.lightened(.17))
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
		# Render each body with its own plume silhouette, including at equal power.
		pm.spread=clampf(70.*width/(height+width),12.,79.) if smoke else 53.
		var mid := Color("#f27a32") if not smoke else dust.darkened(.19)
		if label=="Smoke": mid=Color("#55515a")
		var ramp := pm.color_ramp as GradientTexture1D
		ramp.gradient.offsets = PackedFloat32Array([0,.38,1.])
		ramp.gradient.colors = PackedColorArray([Color(hot.r,hot.g,hot.b,.43 if smoke else 1.),Color(mid.r,mid.g,mid.b,.32 if smoke else .85),Color(mid.r,mid.g,mid.b,0)])
		pm.initial_velocity_min = plan.ejecta_speed*(.18 if smoke else .6)
		pm.initial_velocity_max = plan.ejecta_speed*(.75 if smoke else 1.48)*(.70+.48*float(visual.ejecta))
		pm.scale_max = (.72+power)*(1.7*float(visual.dust) if smoke else 1.)
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
	var wave := .18+age*(2.7+float(visual.wave_angle)*3.1)
	var growth: float=(1.-exp(-age*.94))*radius*(.35+visual.dust)
	vapor.scale=Vector3(maxf(.02,growth*width),maxf(.02,growth*height),maxf(.02,growth*width*.79))
	vapor.position.y=growth*height*.43
	vapor.material_override.set_shader_parameter("age",age)
	vapor.material_override.set_shader_parameter("density",haze*smoothstep(.02,.31,age)*(1.-smoothstep(1.6,5.1,age)))
	vapor.visible=vapor.visible and age<5.1
	$Shockwave.scale=Vector3.ONE*wave
	$Shockwave.material_override.set_shader_parameter("strength",maxf(0.,1.-age/2.3)*.81)
	$FractureCloud.scale=Vector3.ONE*(.12+age*(3.+strength*3.))
	$FractureCloud.material_override.set_shader_parameter("strength",maxf(0.,.30-age*.13))
	$Flash.scale=Vector3.ONE*(.28+power*1.6+age*3.)
	$Flash.material_override.set_shader_parameter("strength",maxf(0.,1.-age*2.8))
	$Crater.material_override.set_shader_parameter("heat",maxf(0.,1.-age/duration)*float(visual.heat))

func _process(delta: float) -> void:
	if age<0. or GameState.director.state==ShotDirector.State.PAUSED: return
	age+=delta
	if age>duration+1.:
		clear()
	else:
		update_meshes()
