class_name RailSequence
extends Node

var world: Node3D
var platform: RailgunPlatform
var clock:=SequenceClock.new()
var phase: StringName=&""
var age:=0.
var token: int
var destination: StringName
var swapped:=false
var pending_impact:=false
var fast_finish:=false
var bass_played:=false
var profile: Dictionary
var request: ShotRequest
var report: ImpactReport
var travel_start:=Basis.IDENTITY
var travel_end:=Basis.IDENTITY

func setup(host: Node3D) -> void:
	world=host
	EventBus.impact_committed.connect(on_report)
	clock.restart()

func on_report(value: ImpactReport) -> void:
	if request and request.shot_id==value.shot_id: report=value

func begin_travel(id: StringName) -> void:
	if not platform or not phase.is_empty() or id==world.planet.definition.id or id not in platform.get_valid_targets(): return
	var director:=GameState.director
	director.abort()
	token=director.generation
	if not director.transition(ShotDirector.State.TRAVEL,token): return
	destination=id
	swapped=false
	world.launch_view=false
	world.frame_view()
	travel_start=platform.global_basis.orthonormalized()
	travel_end=travel_start.rotated(travel_start.y,deg_to_rad(13.)*signf(float(TargetRegistry.STANDARD.find(id))-2.1))
	enter(&"TRAVEL")
	world.update_controls()

func swap_target() -> void:
	if swapped: return
	swapped=true
	world.load_target(destination)
	world.frame_view()
	EventBus.target_selected.emit(destination)

func arrive() -> void:
	swap_target()
	platform.begin_travel(1.,0.)
	world.screen_pulse(0.)
	world.rig.camera.fov=60.
	GameState.director.transition(ShotDirector.State.AIM,token)
	EventBus.discovered.emit(destination)
	enter(&"")
	world.update_controls()

func start_sequence(value: ShotRequest, generation: int) -> bool:
	if not phase.is_empty() or not platform or not platform.can_fire(value): return false
	if not world.fracture or world.fracture.integrity<=0. or not GameState.director.fire(value,generation): return false
	request=GameState.director.active
	token=generation
	profile=RailBalance.sample(request.power)
	report=null
	fast_finish=false
	bass_played=false
	enter(&"CHARGING")
	EventBus.charge_started.emit(request.shot_id,request.power)
	AudioManager.play_at(platform.get_node("ChargeAudio"),&"charge")
	world.update_controls()
	return true

func enter(next: StringName) -> void:
	phase=next
	age=0.
	clock.restart()

func discharge() -> void:
	if not GameState.director.transition(ShotDirector.State.FIRING,token): return
	platform.get_node("ChargeAudio").stop()
	platform.pulse()
	AudioManager.play_at(platform.get_node("MuzzleAudio"),&"pulse")
	EventBus.fired.emit(request.shot_id)
	world.rig.shake(profile.recoil*.55,request.seed)
	enter(&"FIRING")

func queue_impact() -> void:
	if not GameState.director.transition(ShotDirector.State.IMPACT,token): return
	pending_impact=true
	enter(&"IMPACT")

func _physics_process(_delta: float) -> void:
	if clock.suspended or not pending_impact or GameState.director.state!=ShotDirector.State.IMPACT: return
	pending_impact=false
	if token!=GameState.director.generation: return
	platform.cancel_sequence()
	var result: Dictionary=world.fracture.commit_active(request,world.rig.camera.global_position,token)
	if token!=GameState.director.generation: return
	if result.is_empty() or not report:
		GameState.director.abort()
		cancel_sequence()
		world.update_controls()
		return
	platform.get_node("ImpactAudio").global_position=world.hit_endpoint(request.local_hit_dir)
	world.rig.shake(.10+profile.recoil*.8,request.seed+19)
	Engine.time_scale=profile.slow_scale
	world.screen_pulse(0.)
	world.update_controls()
	var key: StringName=&"SIGNAL_LOST" if report.destroyed else StringName("WIRE_"+String(request.target_id).to_upper())
	EventBus.news_event.emit(request.shot_id,request.target_id,key)
	if report.destroyed: EventBus.signal_lost.emit(request.target_id)
	if fast_finish: finish(true)

func finish(skipped: bool) -> void:
	if not request or GameState.director.generation!=token: return
	if GameState.director.state==ShotDirector.State.IMPACT:
		GameState.director.transition(ShotDirector.State.AFTERMATH,token)
	if skipped: world.fracture.skip()
	GameState.director.transition(ShotDirector.State.IDLE,token)
	cancel_sequence()
	world.finish_rail_shot()

func skip() -> void:
	if token!=GameState.director.generation or GameState.director.state==ShotDirector.State.PAUSED: return
	if phase==&"TRAVEL":
		arrive()
	elif request:
		fast_finish=true
		if phase==&"CHARGING": discharge()
		if phase==&"FIRING": queue_impact()
		if GameState.director.committed: finish(true)

func cancel_sequence() -> void:
	pending_impact=false
	fast_finish=false
	request=null
	report=null
	if is_instance_valid(platform) and platform.is_node_ready(): platform.cancel_sequence()
	if is_instance_valid(world):
		world.screen_pulse(0.)
		world.rig.clear_shake()
	Engine.time_scale=1.
	enter(&"")

func _notification(what: int) -> void:
	if what==NOTIFICATION_APPLICATION_FOCUS_OUT: clock.suspended=true
	if what==NOTIFICATION_APPLICATION_FOCUS_IN:
		clock.suspended=false
		clock.restart()

func _process(_delta: float) -> void:
	var elapsed:=clock.step(GameState.director.state==ShotDirector.State.PAUSED)
	if phase.is_empty() or elapsed<=0.: return
	if token!=GameState.director.generation:
		cancel_sequence()
		return
	advance(elapsed)

func advance(seconds: float) -> void:
	if phase.is_empty() or token!=GameState.director.generation or GameState.director.state==ShotDirector.State.PAUSED: return
	age+=seconds
	match phase:
		&"TRAVEL":
			var t:=clampf(age/2.4,0.,1.)
			var intensity:=smoothstep(.40,1.10,age)*(1.-smoothstep(1.34,2.18,age))
			if not swapped and age<1.2:
				platform.global_basis=travel_start.slerp(travel_end,smoothstep(0.,.50,age)).scaled_local(Vector3.ONE*world.rig.platform_scale)
			if age>=1.2: swap_target()
			platform.begin_travel(t,intensity)
			world.rig.camera.fov=60.+intensity*(4. if Settings.values.reduced_motion else 25.)
			world.screen_pulse(.39*(1.-smoothstep(0.,.20,absf(age-1.2))))
			world.phase_progress(phase,t)
			if t>=1.: arrive()
		&"CHARGING":
			var t:=clampf(age/float(profile.charge_seconds),0.,1.)
			platform.charge(t,age,request.power/100.)
			var tone: AudioStreamPlayer3D=platform.get_node("ChargeAudio")
			tone.pitch_scale=.70+t*(.62+request.power*.004)
			tone.volume_db=-16.+t*8.
			progress(t)
			if t>=1.: discharge()
		&"FIRING":
			var t:=clampf(age/float(profile.flight_seconds),0.,1.)
			platform.flight(t,age,world.hit_endpoint(request.local_hit_dir),world.planet.global_position,world.planet.definition.visual_radius,profile)
			progress(t)
			if t>=1.: queue_impact()
		&"IMPACT":
			if pending_impact or not GameState.director.committed: return
			var hold:=.60+.26*request.power/100.
			Engine.time_scale=lerpf(profile.slow_scale,1.,smoothstep(hold,hold+.47,age))
			world.screen_pulse(profile.flash*smoothstep(0.,.06,age)*(1.-smoothstep(.06,.36,age)))
			aftershock()
			progress(clampf(age/(hold+.47),0.,1.))
			if age>=hold+.47:
				Engine.time_scale=1.
				GameState.director.transition(ShotDirector.State.AFTERMATH,token)
				enter(&"AFTERMATH")
		&"AFTERMATH":
			aftershock()
			progress(clampf(age/float(profile.aftermath_seconds),0.,1.))
			if age>=profile.aftermath_seconds: finish(false)

func aftershock() -> void:
	var elapsed:=age if phase==&"IMPACT" else age+1.07+.26*request.power/100.
	if not bass_played and elapsed>=.5+.95*request.power/100.:
		bass_played=true
		AudioManager.play_at(platform.get_node("ImpactAudio"),&"bass")
		EventBus.aftershock.emit(request.shot_id)

func progress(t: float) -> void:
	EventBus.phase_changed.emit(request.shot_id,phase,t)
	world.phase_progress(phase,t)
