extends Node3D

var planet: PlanetController
var weapon: StringName = &"railgun"
var launch_view := false
var missed := false
var station: Node3D
var fracture: FractureController
var demo_power := 0
var demo_history: Dictionary = {}
var confirmed: ShotRequest
var current_region: Dictionary = {}
@onready var picker = $HUD/TargetPicker
@onready var countries = $HUD/CountryPicker
@onready var rig = $CameraRig
@onready var point: Label = $HUD/Readout/Row/Info/Point
@onready var hint: Label = $HUD/Readout/Row/Info/Hint
@onready var lock_button: Button = $HUD/Readout/Row/Lock

func _ready() -> void:
	%Back.pressed.connect(SceneRouter.show_menu)
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

func accepts_input() -> bool:
	return GameState.director.state in [ShotDirector.State.IDLE, ShotDirector.State.AIM]

func load_target(id: StringName) -> void:
	if is_instance_valid(fracture):
		if demo_power and fracture.integrity<1.: demo_history[planet.definition.id]=fracture.save_damage()
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
	if demo_power and prepare_fracture() and demo_history.has(id):
		fracture.load_damage(demo_history[id])

func load_station() -> void:
	if is_instance_valid(station):
		$Weapons.remove_child(station)
		station.queue_free()
	var medium: bool = Settings.values.quality < 2
	var model: String = {"railgun":"RailgunMedium" if medium else "Railgun", "vera":"VeraMedium" if medium else "Vera", "gungnir":"Gungnir"}[weapon]
	station = load("res://assets/models/%s.glb" % model).instantiate()
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
		picker.refresh(weapon,planet.definition,launch_view)
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
		picker.refresh(weapon,planet.definition,launch_view)
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
	station.visible = launch_view
	if launch_view:
		var scale_radius := 11.0 if weapon == &"gungnir" else 3.3
		var direction := Vector3(.38,.32,1.0) if weapon == &"vera" else Vector3(.8,.62,.73)
		rig.frame(station.global_position,scale_radius,GameState.director.generation,direction.normalized())
	else:
		var r := planet.definition.visual_radius
		rig.frame(planet.global_position,r*1.25 if planet.definition.id == &"saturn" else r,GameState.director.generation,Vector3(.88,.37,.34).normalized())
	picker.refresh(weapon,planet.definition,launch_view)
	refresh_readout()

func open_countries() -> void:
	if accepts_input() and not launch_view and planet.definition.id == &"earth":
		countries.open()

func choose_region(row: Dictionary) -> void:
	if not accepts_input() or launch_view or planet.definition.id != &"earth":
		return
	select_direction(CountryLookup.representative(row))
	rig.locked = true
	rig.follow(planet.world_direction(planet.local_hit_dir),GameState.director.generation)

func pick_screen(pixel: Vector2) -> void:
	if not accepts_input() or launch_view:
		return
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
	if not accepts_input() or launch_view or planet.local_hit_dir == Vector3.ZERO:
		return
	var request := ShotRequest.new()
	request.shot_id = GameState.next_shot_id
	request.weapon_id = weapon
	request.target_id = planet.definition.id
	request.power = 100
	request.local_hit_dir = planet.local_hit_dir
	request.country_id = current_region.get("code","")
	request.seed = GameState.snapshot.seed + GameState.next_shot_id
	if request.is_valid():
		GameState.next_shot_id += 1
		confirmed = request
		rig.locked = true
		refresh_readout()

func refresh_readout() -> void:
	lock_button.visible = not launch_view
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

func apply_settings() -> void:
	$KeyLight.shadow_enabled = bool(Settings.values.shadows)
	if station:
		load_station()
	picker.refresh(weapon,planet.definition,launch_view)
	refresh_readout()

func on_reset(_generation: int) -> void:
	countries.hide()
	launch_view = false
	if not demo_power: weapon = &"railgun"
	if demo_power:
		var target:=planet.definition.id
		if fracture: fracture.restore()
		demo_history.clear()
		load_target(target)
	else: load_target(&"earth")
	load_station()
	for body: PlanetController in $Backdrop.get_children():
		body.elapsed = 0.0
		body.get_node("SpinPivot").rotation = Vector3.ZERO
	$HUD/Paused.hide()
	frame_view()

func _process(delta: float) -> void:
	if not accepts_input():
		return
	var light_dir: Vector3 = $KeyLight.global_basis.z
	planet.advance(delta,light_dir)
	for body: PlanetController in $Backdrop.get_children():
		if body.visible: body.advance(delta,light_dir)
	if not launch_view:
		var pixels: float = get_viewport().get_visible_rect().size.y * planet.definition.visual_radius / (2.0*rig.distance*tan(deg_to_rad(rig.camera.fov)*.5))
		planet.update_lod(pixels,Settings.values.quality)
		if planet.local_hit_dir != Vector3.ZERO:
			rig.follow(planet.world_direction(planet.local_hit_dir),GameState.director.generation)

func _unhandled_input(event: InputEvent) -> void:
	if countries.visible or get_viewport().gui_get_focus_owner() is LineEdit:
		return
	if event is InputEventMouseButton and event.is_action_pressed("select"):
		pick_screen(event.position)
	elif event is InputEventKey and event.is_action_pressed("fire"):
		if demo_power and fracture and accepts_input() and planet.local_hit_dir!=Vector3.ZERO:
			demo_hit.call_deferred(planet.local_hit_dir,demo_power)
		else: confirm_aim()
	elif event.is_action_pressed("skip_cinematic") and fracture:
		fracture.skip()
	elif event.is_action_pressed("pause"):
		GameState.director.toggle_pause()
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

func demo_hit(direction: Vector3, power: int) -> Dictionary:
	if not fracture or not accepts_input() or fracture.integrity<=0.: return {}
	select_direction(direction)
	confirm_aim()
	if not confirmed: return {}
	var request:=confirmed
	request.power=power
	var result:=fracture.apply_hit(request,rig.camera.global_position,GameState.director.generation)
	confirmed=null
	rig.locked=false
	planet.set_hit(Vector3.ZERO)
	refresh_readout()
	return result
