class_name FractureController
extends Node3D

var data := FractureData.new()
var pool := FragmentPool.new()
var fx := preload("res://scenes/fracture/Impact.tscn").instantiate()
var remnant := MeshInstance3D.new()
var planet: PlanetController
var integrity := 1.
var atmosphere := 1.
var population := 0
var age := -1.
var last_power := 0.0
var last_plan: Dictionary
var last_hit := Vector3.ZERO
var original_spin: Transform3D

func prepare(body: PlanetController, quality: int) -> bool:
	planet = body
	planet.apply_quality(quality)
	if not data.prepare(planet): return false
	pool.name="DebrisRoot"
	add_child(pool)
	pool.prepare(quality,data.rows.size())
	add_child(fx)
	remnant.name="RemainingShell"
	planet.get_node("SpinPivot/CrustChunks").add_child(remnant)
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
	if not report.is_valid(population) or not director.fire(request,token): return {}
	director.transition(ShotDirector.State.FIRING,token)
	director.transition(ShotDirector.State.IMPACT,token)
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
	atmosphere=result.atmosphere_fraction
	GameState.registry.integrity_by_id[request.target_id]=integrity
	var old_population:=population
	population-=int(result.simulated_population_loss)
	last_plan=result
	last_hit=request.local_hit_dir
	last_power=request.power/100.
	age=0.
	for mat in [planet.surface,planet.clouds,planet.rim,data.exterior]:
		if mat:
			mat.set_shader_parameter("impact_dir",last_hit)
			mat.set_shader_parameter("impact_power",last_power)
	if planet.definition.type=="gas": planet.call("start_gas_impact",last_hit,request.power/100.,result.destroyed)
	for name_ in ["Clouds","Atmosphere"]:
		if result.destroyed and planet.definition.type!="star": planet.get_node("SpinPivot/"+name_).hide()
	if result.destroyed: planet.get_node("SpinPivot/AimArea").collision_layer=0
	fx.play(planet,last_hit,result,request.power,request.weapon_id)
	director.commit(report,old_population,token)
	if director.generation==token:
		director.transition(ShotDirector.State.AFTERMATH,token)
		director.transition(ShotDirector.State.IDLE,token)
	return result

func update_heat() -> void:
	var heat := maxf(0.,1.-age/float(last_plan.heat_seconds))
	data.interior.set_shader_parameter("heat",heat*minf(1.5,last_plan.emissivity*.58))
	for mat in [planet.surface,planet.clouds,planet.rim,data.exterior]:
		if mat:
			mat.set_shader_parameter("impact_age",age)
			mat.set_shader_parameter("impact_heat",heat)
	if planet.rim: planet.rim.set_shader_parameter("air_fraction",atmosphere)
	if planet.clouds: planet.clouds.set_shader_parameter("density",cloud_density()*atmosphere)

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
	if age<last_plan.heat_seconds+2.: update_heat()

func skip() -> void:
	if age<0.: return
	age=last_plan.heat_seconds+3.
	update_heat()
	fx.clear()
	pool.clear()
	if planet.definition.type=="gas": planet.call("finish_gas_impact")

func restore() -> void:
	skip()
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
		"power":last_power}

func load_damage(state: Dictionary) -> void:
	integrity=state.integrity
	population=state.population
	atmosphere=state.atmosphere
	last_plan=state.plan
	last_hit=state.hit
	last_power=state.power
	planet.spin_locked=true
	planet.get_node("SpinPivot").transform=state.spin
	GameState.registry.integrity_by_id[planet.definition.id]=integrity
	for i in state.ids: data.rows[i].active=true
	if not data.rows.is_empty():
		remnant.mesh=data.remaining() if integrity>0. else null
	if integrity<=0.:
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
	update_heat()
