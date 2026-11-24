extends Node3D

var planet: PlanetController
var weapon: StringName = &"railgun"
var launch_view := false
var missed := false
var station: Node3D
var fracture: FractureController
var demo_power := 0
var damage_history: Dictionary
var sequence:=RailSequence.new()
var last_region:=""
var power:=50

var confirmed: ShotRequest
var current_region: Dictionary = {}
@onready var picker = $HUD/TargetPicker
@onready var countries = $HUD/CountryPicker
@onready var rig = $CameraRig
@onready var point: Label = $HUD/Readout/Row/Info/Point
@onready var hint: Label = $HUD/Readout/Row/Info/Hint
@onready var lock_button: Button = $HUD/Readout/Row/Lock

func _ready() -> void:
	damage_history=GameState.damage_history
	add_child(sequence)
	sequence.setup(self)
	%Back.pressed.connect(SceneRouter.show_menu)
	%Fire.pressed.connect(fire_rail)
	picker.get_node("Body/Power").value_changed.connect(change_power)
	picker.get_node("Body/Restore").pressed.connect(restore_target)
	EventBus.news_event.connect(on_news)
	EventBus.impact_committed.connect(receive_report)
	picker.weapon_picked.connect(choose_weapon)
	picker.target_picked.connect(choose_target)
	picker.station_requested.connect(toggle_station)
	picker.country_requested.connect(open_countries)
	countries.region_picked.connect(choose_region)
	lock_button.pressed.connect(confirm_aim)
	EventBus.settings_changed.connect(apply_settings)
	EventBus.world_reset.connect(on_reset)
	var places := {&"jupiter":Vector3(-89,-17,-129), &"saturn":Vector3(-146,24,108), &"sun":Vector3(115,34,-180)}
	for id: StringName in places:
		var body := TargetRegistry.instantiate_body(id,true)
		body.position = places[id]
		$Backdrop.add_child(body)
	load_target(&"earth")
	load_station()
	$KeyLight.shadow_enabled = bool(Settings.values.shadows)
	frame_view()
	apply_presentation()
	EventBus.discovered.emit(planet.definition.id)

func accepts_input() -> bool:
	return GameState.director.state in [ShotDirector.State.IDLE, ShotDirector.State.AIM]

func load_target(id: StringName) -> void:
	if is_instance_valid(fracture):
		if fracture.integrity<1.: damage_history[planet.definition.id]=fracture.save_damage()
		fracture.free()
		fracture=null
	if is_instance_valid(planet):
		$Targets.remove_child(planet)
		planet.queue_free()
	planet = TargetRegistry.instantiate_body(id)
	$Targets.add_child(planet)
	current_region = {}
	missed = false
	confirmed = null
	if weapon==&"railgun" or demo_power or damage_history.has(id):
		if prepare_fracture() and damage_history.has(id): fracture.load_damage(damage_history[id])
	$HUD/Report.hide()

func load_station() -> void:
	if is_instance_valid(station):
		$Weapons.remove_child(station)
		station.queue_free()
	var medium: bool = Settings.values.quality < 2
	var model: String = {"railgun":"RailgunMedium" if medium else "Railgun", "vera":"VeraMedium" if medium else "Vera", "gungnir":"Gungnir"}[weapon]
	station=preload("res://scenes/weapons/Railgun.tscn").instantiate() if weapon==&"railgun" else load("res://assets/models/%s.glb"%model).instantiate()
	sequence.platform=station as RailgunPlatform
	$Weapons.add_child(station)
	match weapon:
		&"railgun":
			station.position = Vector3(18,1,24)
		&"gungnir":
			station.position = $Backdrop/Jupiter.position
			station.rotation_degrees.z = 18
			station.scale = Vector3.ONE*3.18
			var dart: Node3D = load("res://assets/models/GungnirProjectile.glb").instantiate()
			station.find_child("ProjectileAnchor",true,false).add_child(dart)
			dart.scale = Vector3.ONE*.34
		&"vera":
			station.position = $Backdrop/Saturn.position + Vector3(7,3,20)
			station.rotation_degrees.x = 29
	station.visible = launch_view

func choose_weapon(id: StringName) -> void:
	if not accepts_input() or id == weapon:
		picker.refresh(weapon,planet.definition,launch_view,fracture.population if fracture else planet.definition.population)
		return
	GameState.director.abort()
	weapon = id
	confirmed = null
	if not TargetRegistry.allows(weapon, planet.definition.id):
		load_target(&"earth")
	EventBus.weapon_selected.emit(id)
	EventBus.target_selected.emit(planet.definition.id)
	load_station()
	frame_view()

func choose_target(id: StringName) -> void:
	if not accepts_input() or not TargetRegistry.allows(weapon,id):
		picker.refresh(weapon,planet.definition,launch_view,fracture.population if fracture else planet.definition.population)
		return
	if weapon==&"railgun" and not demo_power:
		if id!=planet.definition.id: sequence.begin_travel(id)
		else: update_controls()
		return
	GameState.director.abort()
	launch_view = false
	load_target(id)
	EventBus.target_selected.emit(id)
	frame_view()

func toggle_station() -> void:
	if accepts_input():
		launch_view = not launch_view
		frame_view()

func frame_view() -> void:
	for body: PlanetController in $Backdrop.get_children():
		body.visible = launch_view or body.definition.id != planet.definition.id
	planet.visible = not launch_view
	var rear:=weapon==&"railgun" and not launch_view and not demo_power
	rig.set_rear(station,rear)
	station.visible=launch_view or rear
	if launch_view:
		var scale_radius := 11.0 if weapon == &"gungnir" else 3.3
		var direction := Vector3(.38,.32,1.0) if weapon == &"vera" else Vector3(.8,.62,.73)
		rig.frame(station.global_position,scale_radius,GameState.director.generation,direction.normalized())
	else:
		var r := planet.definition.visual_radius
		rig.frame(planet.global_position,r*1.25 if planet.definition.id == &"saturn" else r,GameState.director.generation,Vector3(.88,.37,.34).normalized())
	picker.refresh(weapon,planet.definition,launch_view,fracture.population if fracture else planet.definition.population)
	refresh_readout()

func open_countries() -> void:
	if accepts_input() and not launch_view and planet.definition.id == &"earth":
		countries.open()

func choose_region(row: Dictionary) -> void:
	if not accepts_input() or launch_view or planet.definition.id != &"earth":
		return
	select_direction(CountryLookup.representative(row))
	rig.locked = true
	rig.target_point=hit_endpoint(planet.local_hit_dir)
	rig.follow(planet.world_direction(planet.local_hit_dir),GameState.director.generation)

func pick_screen(pixel: Vector2) -> void:
	if not accepts_input() or launch_view:
		return
	if fracture and fracture.integrity<=0.: return
	get_viewport().gui_release_focus()
	var cam: Camera3D = rig.camera
	select_direction(planet.hit_direction(cam.project_ray_origin(pixel),cam.project_ray_normal(pixel)))

func select_direction(direction: Vector3) -> void:
	confirmed = null
	rig.locked = false
	planet.set_hit(direction)
	missed = direction == Vector3.ZERO
	current_region = {}
	if direction != Vector3.ZERO:
		if planet.definition.id == &"earth":
			current_region = CountryLookup.region(direction)
		if GameState.director.state == ShotDirector.State.IDLE:
			var director := GameState.director
			director.transition(ShotDirector.State.TRAVEL,director.generation)
			director.transition(ShotDirector.State.AIM,director.generation)
	refresh_readout()

func confirm_aim() -> void:
	if not accepts_input() or launch_view or planet.local_hit_dir == Vector3.ZERO or (fracture and fracture.integrity<=0.):
		return
	var request := ShotRequest.new()
	request.shot_id = GameState.next_shot_id
	request.weapon_id = weapon
	request.target_id = planet.definition.id
	request.power = power if weapon==&"railgun" else 100
	request.local_hit_dir = planet.local_hit_dir
	request.country_id = current_region.get("code","")
	request.seed = GameState.snapshot.seed + GameState.next_shot_id
	if request.is_valid():
		GameState.next_shot_id += 1
		confirmed = request
		rig.locked = true
		refresh_readout()

func refresh_readout() -> void:
	update_controls()
	lock_button.visible = not launch_view and (weapon!=&"railgun" or demo_power>0)
	lock_button.disabled = planet.local_hit_dir == Vector3.ZERO or confirmed != null
	if launch_view:
		point.text = String(weapon).to_upper()
		hint.text = tr("POSITION_"+String(weapon).to_upper())
		return
	if planet.local_hit_dir == Vector3.ZERO:
		point.text = "EMPTY_SPACE" if missed else "PICK_POINT"
	else:
		var uv := CountryLookup.geometry.globe_uv(planet.local_hit_dir)
		var place := CountryLookup.localized(current_region) if not current_region.is_empty() else tr(planet.definition.name_key)
		point.text = tr("POINT_COORDS") % [place,(.5-uv.y)*180.0,(uv.x-.5)*360.0]
	hint.text = "POINT_STORED" if confirmed else "AIM_HELP"

func apply_presentation() -> void:
	var grade: ShaderMaterial=$Presentation/Grade.material
	grade.set_shader_parameter("sharpness",Settings.SHARPNESS[Settings.values.sharpness])
	grade.set_shader_parameter("texel_scale",1./minf(1.,Settings.RENDER_SCALES[Settings.values.render_scale]))
	grade.set_shader_parameter("saturation",1.16)

func apply_settings() -> void:
	apply_presentation()
	$KeyLight.shadow_enabled = bool(Settings.values.shadows)
	if fracture:
		fracture.pool.resize_idle(Settings.values.quality,fracture.data.rows.size())
		fracture.data.exterior.set_shader_parameter("quality_level",Settings.values.quality)
	if station and accepts_input():
		load_station()
		frame_view()
	picker.refresh(weapon,planet.definition,launch_view,fracture.population if fracture else planet.definition.population)
	refresh_readout()

func on_reset(_generation: int) -> void:
	countries.hide()
	launch_view = false
	sequence.cancel_sequence()
	var target:=planet.definition.id
	if fracture: fracture.restore()
	damage_history.clear()
	load_target(target)
	load_station()
	for body: PlanetController in $Backdrop.get_children():
		body.elapsed = 0.0
		body.get_node("SpinPivot").rotation = Vector3.ZERO
	$HUD/Paused.hide()
	frame_view()

func _process(delta: float) -> void:
	if GameState.director.state==ShotDirector.State.PAUSED: return
	var light_dir: Vector3 = $KeyLight.global_basis.z
	planet.advance(delta,light_dir)
	for body: PlanetController in $Backdrop.get_children():
		if body.visible: body.advance(delta,light_dir)
	if not launch_view:
		var pixels: float = get_viewport().get_visible_rect().size.y * planet.definition.visual_radius / (2.0*rig.distance*tan(deg_to_rad(rig.camera.fov)*.5))
		planet.update_lod(pixels,Settings.values.quality)
		var direction:=planet.local_hit_dir if not sequence.request else sequence.request.local_hit_dir
		if direction!=Vector3.ZERO:
			rig.target_point=hit_endpoint(direction)
			if accepts_input(): rig.follow(planet.world_direction(direction),GameState.director.generation)
		else: rig.target_point=planet.global_position
		if rig.rear_mode:
			var dt:=minf(.08,delta/maxf(Engine.time_scale,.01))
			rig.position_rear(dt,false,sequence.phase!=&"TRAVEL" or sequence.swapped)
			rig.tick_shake(dt)
		var reticle: Control=$HUD/AimReticle
		reticle.visible=rig.rear_mode and direction!=Vector3.ZERO and (not fracture or fracture.integrity>0.) and not rig.camera.is_position_behind(hit_endpoint(direction))
		if reticle.visible:
			reticle.position=rig.camera.unproject_position(hit_endpoint(direction))-reticle.size*.5

func _unhandled_input(event: InputEvent) -> void:
	if countries.visible or get_viewport().gui_get_focus_owner() is LineEdit:
		return
	if event is InputEventMouseButton and event.is_action_pressed("select"):
		pick_screen(event.position)
	elif event is InputEventKey and event.is_action_pressed("fire"):
		if event.echo: return
		var owner:=get_viewport().gui_get_focus_owner()
		if owner is Range or owner is BaseButton or owner is ItemList: return
		if demo_power and fracture and accepts_input() and planet.local_hit_dir!=Vector3.ZERO:
			demo_hit(planet.local_hit_dir,demo_power)
		elif weapon==&"railgun": fire_rail()
		else: confirm_aim()
	elif event.is_action_pressed("skip_cinematic"):
		if not sequence.phase.is_empty(): sequence.skip()
		elif fracture: fracture.skip()
	elif event.is_action_pressed("pause"):
		GameState.director.toggle_pause()
		if sequence.platform: sequence.platform.set_paused(GameState.director.state==ShotDirector.State.PAUSED)
		sequence.clock.restart()
		update_controls()
		if fracture: fracture.set_effects_paused(GameState.director.state==ShotDirector.State.PAUSED)
		$HUD/Paused.visible = GameState.director.state == ShotDirector.State.PAUSED
	elif event.is_action_pressed("reset"):
		GameState.reset_world()
	else:
		return
	get_viewport().set_input_as_handled()

func prepare_fracture() -> bool:
	if fracture: return true
	fracture=FractureController.new()
	$VFX.add_child(fracture)
	if fracture.prepare(planet,Settings.values.quality): return true
	fracture.free()
	fracture=null
	return false

func demo_hit(direction: Vector3, shot_power: int) -> Dictionary:
	if not fracture or not accepts_input() or fracture.integrity<=0.: return {}
	select_direction(direction)
	confirm_aim()
	if not confirmed: return {}
	var request:=confirmed
	request.power=shot_power
	var result:=fracture.apply_hit(request,rig.camera.global_position,GameState.director.generation)
	confirmed=null
	rig.locked=false
	planet.set_hit(Vector3.ZERO)
	refresh_readout()
	return result

func change_power(value: float) -> void:
	if not accepts_input():
		picker.get_node("Body/Power").set_value_no_signal(power)
		return
	power=roundi(value)
	confirmed=null
	picker.get_node("Body/PowerRow/Value").text="%d%%"%power
	update_controls()

func update_controls() -> void:
	if not is_node_ready() and not point: return
	var rail_mode:=weapon==&"railgun" and not launch_view and demo_power==0
	var remaining:=fracture.integrity if fracture else 1.
	if not rail_mode: $HUD/AimReticle.hide()
	var busy:=not accepts_input() and GameState.director.state!=ShotDirector.State.LOADING
	picker.controls(rail_mode,busy,remaining)
	picker.get_node("Body/Restore").disabled=busy
	%Fire.visible=rail_mode
	%Fire.disabled=busy or remaining<=0. or planet.local_hit_dir==Vector3.ZERO
	$HUD/Phase.visible=busy and not sequence.phase.is_empty()
	if not $HUD/Phase.visible: $HUD/Phase/Bar.value=0.
	if sequence.phase.is_empty(): $Presentation/Pulse.color.a=0.

func fire_rail() -> void:
	if weapon!=&"railgun" or not accepts_input() or launch_view or not prepare_fracture(): return
	if planet.local_hit_dir==Vector3.ZERO or fracture.integrity<=0.: return
	confirm_aim()
	if not confirmed: return
	if GameState.director.state==ShotDirector.State.IDLE:
		GameState.director.transition(ShotDirector.State.TRAVEL,GameState.director.generation)
		GameState.director.transition(ShotDirector.State.AIM,GameState.director.generation)
	last_region=CountryLookup.localized(current_region) if not current_region.is_empty() else tr(planet.definition.name_key)
	if sequence.start_sequence(confirmed,GameState.director.generation):
		$HUD/Report.hide()
		countries.hide()
		get_viewport().gui_release_focus()

func hit_endpoint(direction: Vector3) -> Vector3:
	return planet.get_node("SpinPivot").to_global(direction*planet.definition.visual_radius)

func screen_pulse(amount: float) -> void:
	$Presentation/Pulse.color.a=clampf(amount,0.,.20 if Settings.values.reduced_motion else .64)

func phase_progress(phase: StringName, t: float) -> void:
	$HUD/Phase.visible=true
	$HUD/Phase/Title.text=tr("PHASE_"+String(phase))+"  %d%%"%roundi(t*100.)
	$HUD/Phase/Bar.value=t*100.

func receive_report(report: ImpactReport) -> void:
	if not sequence.request or sequence.request.shot_id!=report.shot_id: return
	picker.refresh(weapon,planet.definition,launch_view,fracture.population)
	var severity:="HIT_LOST" if report.destroyed else ("HIT_EXTENSIVE" if report.damage_fraction>=.2 else "HIT_LOCAL")
	var stats:=PackedStringArray([tr("READ_ENERGY")%report.energy_index,tr("READ_LOSS")%picker.spaced(report.simulated_population_loss),
		tr("READ_DAMAGE")%(report.damage_fraction*100.),tr("INTEGRITY_READ")%roundi(report.integrity*100.),tr("READ_AIR")%(report.atmosphere_fraction*100.)])
	stats.append(tr(severity))
	if report.crater_radius_game_km>0.: stats.insert(1,tr("READ_CRATER")%report.crater_radius_game_km)
	$HUD/Report/Body/Stats.text="\n".join(stats)
	$HUD/Report/Body/News.text=""
	$HUD/Report.show()

func on_news(id: int, target: StringName, key: StringName) -> void:
	if sequence.request and id==sequence.request.shot_id and target==planet.definition.id:
		$HUD/Report/Body/News.text=last_region+"  ·  "+tr(key)

func finish_rail_shot() -> void:
	confirmed=null
	if fracture.integrity<=0.: planet.set_hit(Vector3.ZERO)
	rig.locked=false
	refresh_readout()

func restore_target() -> void:
	if not fracture: return
	GameState.director.abort()
	sequence.cancel_sequence()
	fracture.restore()
	damage_history.erase(planet.definition.id)
	planet.set_hit(Vector3.ZERO)
	confirmed=null
	$HUD/Paused.hide()
	$HUD/Report.hide()
	frame_view()

func _exit_tree() -> void:
	if is_instance_valid(fracture) and fracture.integrity<1.:
		damage_history[planet.definition.id]=fracture.save_damage()
	sequence.cancel_sequence()
