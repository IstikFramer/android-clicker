class_name FractureController
extends Node3D

var data := FractureData.new()
var pool := FragmentPool.new()
var fx := preload("res://scenes/fracture/Impact.tscn").instantiate()
var remnant := MeshInstance3D.new()
var residue:=MultiMeshInstance3D.new()
var heat_factor:=1.
var planet: PlanetController
var integrity := 1.
var atmosphere := 1.
var population := 0
var age := -1.
var last_power := 0.0
var last_plan: Dictionary
var last_hit := Vector3.ZERO
var original_spin: Transform3D
var prior_air:=1.
var weather_age:=-1.
var strip:=0.
var wave:=0.
var scars:=Image.create_empty(192,96,false,Image.FORMAT_R8)
var scar_texture: ImageTexture
var weather_materials: Array[ShaderMaterial]=[]

func prepare(body: PlanetController, quality: int) -> bool:
	planet = body
	scar_texture=ImageTexture.create_from_image(scars)

	planet.apply_quality(quality)
	if not data.prepare(planet): return false
	for mat in [planet.clouds,planet.rim]:
		if mat and planet.definition.type!="star": weather_materials.append(mat)
	if planet.definition.id==&"earth": weather_materials.append_array([planet.surface,data.exterior])
	for mat in weather_materials: mat.set_shader_parameter("old_cloud_scars",scar_texture)
	pool.name="DebrisRoot"
	add_child(pool)
	pool.prepare(quality,data.rows.size())
	add_child(fx)
	remnant.name="RemainingShell"
	planet.get_node("SpinPivot/CrustChunks").add_child(remnant)
	residue.name="OrbitalRemains"
	add_child(residue)
	original_spin=planet.get_node("SpinPivot").transform
	population = planet.definition.population
	atmosphere = 0. if planet.definition.atmosphere==&"VACUUM" else 1.
	if not data.rows.is_empty():
		# Use the baked source shell even before the first impact.
		remnant.mesh=data.remaining()
		planet.surface_mesh.hide()
	return true

func apply_hit(request: ShotRequest, eye: Vector3, token: int) -> Dictionary:
	var director := GameState.director
	if director.generation!=token or not request.is_valid() or integrity<=0. or director.state!=ShotDirector.State.AIM: return {}
	if not director.fire(request,token): return {}
	director.transition(ShotDirector.State.FIRING,token)
	director.transition(ShotDirector.State.IMPACT,token)
	var result:=commit_active(director.active,eye,token)
	if result.is_empty():
		director.abort()
	elif director.generation==token:
		director.transition(ShotDirector.State.AFTERMATH,token)
		director.transition(ShotDirector.State.IDLE,token)
	return result

func commit_active(request: ShotRequest, eye: Vector3, token: int) -> Dictionary:
	var director:=GameState.director
	if director.generation!=token or director.state!=ShotDirector.State.IMPACT or director.committed or request!=director.active: return {}
	if request.target_id!=planet.definition.id or integrity<=0.: return {}
	var params := {"weapon_id":request.weapon_id,"target_type":planet.definition.type,"power":request.power,
		"local_hit_dir":request.local_hit_dir,"resistance":planet.definition.damage_resistance,
		"seed":request.seed,"prior_integrity":integrity,"scene_radius":planet.definition.visual_radius,
		"atmosphere_fraction":atmosphere,"remaining_population":population}
	var result: Dictionary = CountryLookup.geometry.plan_impact(data.rows,params)
	if not result.ok:
		push_error(str(result.error))
		return {}
	var report := ImpactReport.new()
	report.shot_id=request.shot_id
	report.target_id=request.target_id
	report.power=request.power
	report.activated_fragment_count=result.selected_ids.size()
	for field in ["damage_fraction","integrity","atmosphere_fraction","crater_radius_game_km",
			"simulated_population_loss","energy_index","destroyed","status_key"]:
		report.set(field,result[field])
	if not report.is_valid(population): return {}
	if age>=0. and last_power>0.: stamp_previous_scar()
	var snapshot: Transform3D = planet.get_node("SpinPivot").global_transform
	for id in result.selected_ids: data.rows[id].active=true
	if not data.rows.is_empty():
		remnant.mesh=data.remaining() if not result.destroyed else null
		pool.launch(data,result,snapshot,planet.definition.rotation_rate if age<0 else 0.,eye)
		var props:=planet.get_node("SpinPivot/Markers")
		for item in props.get_children():
			if item==planet.marker:
				item.hide()
			elif result.destroyed or request.local_hit_dir.dot(item.position.normalized())>1.-sqrt(result.damage_fraction):
				item.hide()
	planet.spin_locked=true
	integrity=result.integrity
	prior_air=atmosphere
	atmosphere=result.atmosphere_fraction
	GameState.registry.integrity_by_id[request.target_id]=integrity
	var old_population:=population
	population-=int(result.simulated_population_loss)
	last_plan=result
	last_hit=request.local_hit_dir
	last_power=request.power/100.
	age=0.
	weather_age=0.
	var visual:=RailBalance.sample(maxi(10,request.power))
	heat_factor=.50+.78*float(visual.heat)
	strip=visual.stripping
	wave=visual.wave_angle
	for mat in weather_materials:
		if mat:
			mat.set_shader_parameter("stripping",strip)
			mat.set_shader_parameter("weather_wave",wave)
			mat.set_shader_parameter("dispersal",1. if result.destroyed else 0.)
	for mat in [planet.surface,planet.clouds,planet.rim,data.exterior]:
		if mat:
			mat.set_shader_parameter("impact_dir",last_hit)
			mat.set_shader_parameter("impact_power",last_power)
	if planet.definition.type=="gas": planet.call("start_gas_impact",last_hit,request.power/100.,result.destroyed)
	update_weather()
	if result.destroyed:
		planet.get_node("SpinPivot/AimArea").collision_layer=0
		if planet.definition.type=="rocky" and not result.annihilate:
			var core: MeshInstance3D=planet.get_node("SpinPivot/Core")
			var glow:=core.material_override as StandardMaterial3D
			glow.emission_enabled=true
			glow.emission=Color("#ff842b")
			glow.emission_energy_multiplier=1.4
			core.show()
	fx.play(planet,last_hit,result,request.power,request.weapon_id)
	director.commit(report,old_population,token)
	return result

func update_heat() -> void:
	var heat := maxf(0.,1.-age/float(last_plan.heat_seconds))
	data.interior.set_shader_parameter("heat",heat*heat_factor*minf(1.5,last_plan.emissivity*.58))
	for mat in [planet.surface,planet.clouds,planet.rim,data.exterior]:
		if mat:
			mat.set_shader_parameter("impact_age",age)
			mat.set_shader_parameter("impact_heat",heat)

func update_weather() -> void:
	if planet.definition.type=="star": return
	var air:=lerpf(prior_air,atmosphere,smoothstep(.3,3.9,weather_age))
	if planet.rim: planet.rim.set_shader_parameter("air_fraction",air)
	if planet.clouds: planet.clouds.set_shader_parameter("density",cloud_density()*air)
	for mat in weather_materials:
		if mat: mat.set_shader_parameter("weather_age",weather_age)
	if integrity<=0. and weather_age>=3.9:
		planet.get_node("SpinPivot/Clouds").hide()
		planet.get_node("SpinPivot/Atmosphere").hide()

func stamp_previous_scar() -> void:
	if not planet.clouds and not planet.rim: return
	for y in scars.get_height():
		var lat:=PI*(.5-(y+.5)/scars.get_height())
		for x in scars.get_width():
			var lon:=TAU*((x+.5)/scars.get_width()-.5)
			var n:=Vector3(cos(lat)*cos(lon),sin(lat),cos(lat)*sin(lon))
			var angle:=acos(clampf(n.dot(last_hit),-1.,1.))
			var lost:=1.-smoothstep(wave*.67,wave,angle)
			if lost>scars.get_pixel(x,y).r: scars.set_pixel(x,y,Color(lost,0.,0.))
	scar_texture.update(scars)


func cloud_density() -> float:
	match planet.definition.id:
		&"venus": return .94
		&"mars": return .16
		_: return .82

func _process(delta: float) -> void:
	if planet and data.exterior:
		data.exterior.set_shader_parameter("sun_dir_local",planet.sun_local)
		data.exterior.set_shader_parameter("u_time",planet.elapsed)
	if age<0. or GameState.director.state==ShotDirector.State.PAUSED: return
	age+=delta
	if integrity<=0. and planet.definition.type=="rocky":
		var core: MeshInstance3D=planet.get_node("SpinPivot/Core")
		if core.visible:
			core.scale=Vector3.ONE*maxf(.005,1.-smoothstep(.55,1.9,age))
			core.visible=age<1.9
	if weather_age<4.:
		weather_age+=minf(.1,delta/maxf(Engine.time_scale,.01))
		update_weather()
	if age<last_plan.heat_seconds+2.: update_heat()
	if integrity<=0. and age>2.8: show_remains()

func show_remains() -> void:
	if residue.multimesh or last_plan.get("annihilate",false) or planet.definition.type=="star": return
	# Distant decorative debris stays after active bodies return to the pool.
	var debris:=MultiMesh.new()
	debris.transform_format=MultiMesh.TRANSFORM_3D
	var rock:=preload("res://assets/models/Rock03.glb").instantiate()
	var instance: MeshInstance3D=rock.find_children("*","MeshInstance3D",true,false)[0]
	debris.mesh=instance.mesh
	rock.free()
	debris.instance_count=64
	var rng:=RandomNumberGenerator.new()
	rng.seed=planet.definition.fracture_count+712
	for i in debris.instance_count:
		var theta:=rng.randf()*TAU
		var span:=planet.definition.visual_radius*rng.randf_range(.31,1.9)
		var pos:=Vector3(cos(theta)*span,rng.randf_range(-2.,2.)+sin(theta)*span*.32,sin(theta)*span*.64)
		var orientation:=Basis.from_euler(Vector3(rng.randf(),theta,rng.randf()))
		var size:=rng.randf_range(.12,.7)
		debris.set_instance_transform(i,Transform3D(orientation.scaled_local(Vector3(size,size*.67,size*1.4)),pos))
	residue.multimesh=debris

func skip() -> void:
	if age<0.: return
	age=last_plan.heat_seconds+3.
	weather_age=4.
	update_weather()
	update_heat()
	if planet.definition.type=="rocky":
		planet.get_node("SpinPivot/Core").hide()
		planet.get_node("SpinPivot/Core").scale=Vector3.ONE
	fx.clear()
	pool.clear()
	if integrity<=0.: show_remains()
	if planet.definition.type=="gas": planet.call("finish_gas_impact")

func restore() -> void:
	skip()
	set_effects_paused(false)
	residue.multimesh=null
	integrity=1.
	atmosphere=0. if planet.definition.atmosphere==&"VACUUM" else 1.
	population=planet.definition.population
	GameState.registry.integrity_by_id[planet.definition.id]=1.
	for row in data.rows: row.active=false
	if not data.rows.is_empty(): remnant.mesh=data.remaining()
	planet.spin_locked=false
	planet.get_node("SpinPivot").transform=original_spin
	planet.get_node("SpinPivot/AimArea").collision_layer=2
	planet.get_node("SpinPivot/Markers").show()
	for item in planet.get_node("SpinPivot/Markers").get_children():
		item.visible=item!=planet.marker
	planet.surface_mesh.visible=data.rows.is_empty()
	planet.get_node("SpinPivot/Clouds").visible=planet.clouds!=null
	planet.get_node("SpinPivot/Atmosphere").visible=planet.rim!=null
	for mat in [data.exterior,planet.surface,planet.clouds,planet.rim]:
		if mat: mat.set_shader_parameter("impact_age",-1.)
	if planet.rim: planet.rim.set_shader_parameter("air_fraction",1.)
	if planet.clouds: planet.clouds.set_shader_parameter("density",cloud_density())
	if planet.definition.type=="gas": planet.call("restore_gas")
	age=-1.
	weather_age=-1.
	scars.fill(Color.BLACK)
	scar_texture.update(scars)
	for mat in weather_materials:
		if mat: mat.set_shader_parameter("weather_age",-1.)
	last_plan={}

func set_effects_paused(paused: bool) -> void:
	for emitter in fx.PARTICLES: fx.get_node(emitter).speed_scale=0. if paused else 1.
	for item in pool.physical:
		var body: RigidBody3D=item.body
		if paused and not body.freeze:
			item.paused_linear=body.linear_velocity
			item.paused_angular=body.angular_velocity
			body.freeze=true
		elif not paused and item.has("paused_linear"):
			body.freeze=false
			body.linear_velocity=item.paused_linear
			body.angular_velocity=item.paused_angular
			item.erase("paused_linear")
			item.erase("paused_angular")

func save_damage() -> Dictionary:
	var ids:=PackedInt32Array()
	for row in data.rows:
		if row.active: ids.append(row.id)
	return {"ids":ids,"integrity":integrity,"population":population,"atmosphere":atmosphere,
		"hit":last_hit,"plan":last_plan,"spin":planet.get_node("SpinPivot").transform,
		"hidden_props":planet.get_node("SpinPivot/Markers").get_children().filter(func(n): return n!=planet.marker and not n.visible).map(func(n): return n.name),
		"power":last_power,"scars":scars.get_data(),"wave":wave,"strip":strip}

func load_damage(state: Dictionary) -> void:
	integrity=state.integrity
	population=state.population
	atmosphere=state.atmosphere
	last_plan=state.plan
	last_hit=state.hit
	last_power=state.power
	for item in planet.get_node("SpinPivot/Markers").get_children():
		if item.name in state.get("hidden_props",[]): item.hide()
	prior_air=atmosphere
	wave=state.wave
	strip=state.strip
	scars.set_data(192,96,false,Image.FORMAT_R8,state.scars)
	scar_texture.update(scars)
	for mat in weather_materials:
		if mat:
			mat.set_shader_parameter("weather_wave",wave)
			mat.set_shader_parameter("stripping",strip)
			mat.set_shader_parameter("dispersal",1. if integrity<=0. else 0.)
	planet.spin_locked=true
	planet.get_node("SpinPivot").transform=state.spin
	GameState.registry.integrity_by_id[planet.definition.id]=integrity
	for i in state.ids: data.rows[i].active=true
	if not data.rows.is_empty():
		remnant.mesh=data.remaining() if integrity>0. else null
	if integrity<=0.:
		show_remains()
		planet.get_node("SpinPivot/AimArea").collision_layer=0
		if planet.definition.type!="star":
			planet.get_node("SpinPivot/Clouds").hide()
			planet.get_node("SpinPivot/Atmosphere").hide()
			planet.get_node("SpinPivot/Markers").hide()
	if planet.definition.type=="gas":
		planet.call("start_gas_impact",last_hit,float(state.power),integrity<=0.)
		planet.call("finish_gas_impact")
	for mat in [planet.rim,planet.surface,planet.clouds,data.exterior]:
		if mat:
			mat.set_shader_parameter("impact_dir",last_hit)
			mat.set_shader_parameter("impact_power",state.power)
	age=last_plan.heat_seconds+3.
	weather_age=4.
	update_weather()
	update_heat()
