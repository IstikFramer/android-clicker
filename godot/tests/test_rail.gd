extends RefCounted

var reports: Array[ImpactReport]=[]
var wires: Array[int]=[]
var events: Array[String]=[]

func check(world: Node, expect: Callable) -> void:
	var tree:=world.get_tree()
	var director:=GameState.director
	world.choose_weapon(&"railgun")
	world.demo_power=0
	world.restore_target()
	var seq: RailSequence=world.sequence
	var power_control: HSlider=world.picker.get_node("Body/Power")
	expect.call(power_control.min_value==10. and power_control.max_value==100. and power_control.step==1.,"one-percent power control")
	var last: Dictionary
	for power in range(10,101):
		var current:=RailBalance.sample(power)
		for key in current:
			if not last.is_empty(): expect.call(current[key]!=last[key],"continuous "+key+" at "+str(power))
		last=current
	EventBus.impact_committed.connect(record_report)
	EventBus.news_event.connect(record_news)
	EventBus.discovered.connect(record_discovery)
	EventBus.charge_started.connect(record_charge)
	EventBus.fired.connect(record_fire)
	EventBus.aftershock.connect(record_bass)
	for id in TargetRegistry.STANDARD:
		if id==world.planet.definition.id: continue
		world.choose_target(id)
		expect.call(seq.phase==&"TRAVEL" and not world.accepts_input(),"travel "+String(id))
		seq.advance(1.21)
		expect.call(world.planet.definition.id==id,"midpoint swaps target")
		seq.advance(1.2)
		expect.call(director.state==ShotDirector.State.AIM and is_equal_approx(world.rig.camera.fov,60.),"arrived")
	world.choose_target(&"earth")
	seq.skip()
	expect.call(world.planet.definition.id==&"earth" and world.fracture.integrity==1.,"skip travel")
	world.choose_target(&"mars")
	GameState.reset_world()
	expect.call(world.planet.definition.id==&"earth" and seq.phase.is_empty(),"reset during warp cancels destination")
	world.choose_region(CountryLookup.by_code["FI"])
	power_control.value=35.
	world.fire_rail()
	expect.call(seq.request and seq.request.country_id=="FI","country snapshot")
	world.confirmed.power=100
	expect.call(seq.request.power==35,"frozen fire request")
	world.choose_weapon(&"vera")
	world.choose_target(&"mars")
	var previous_age:=seq.age
	director.toggle_pause()
	seq.advance(1.)
	expect.call(seq.age==previous_age and world.weapon==&"railgun","pause and busy input")
	director.toggle_pause()
	GameState.reset_world()
	seq.advance(10.)
	expect.call(reports.is_empty() and Engine.time_scale==1.,"reset during charge")
	for power in [10,20,50,100]:
		world.choose_region(CountryLookup.by_code["Ocean"])
		power_control.value=power
		var previous_count:=reports.size()
		world.get_node("%Fire").pressed.emit()
		world.fire_rail()
		var shot:=seq.request
		expect.call(shot and director.state==ShotDirector.State.CHARGING,"fire from HUD")
		if not shot: break
		expect.call(world.get_node("%Fire").disabled and not power_control.editable,"lock controls")
		if power==20:
			seq.skip()
		else:
			seq.advance(seq.profile.charge_seconds+.01)
			expect.call(director.state==ShotDirector.State.FIRING,"charge to flight")
			seq.advance(seq.profile.flight_seconds+.01)
		for step in 3: await tree.physics_frame
		expect.call(reports.size()==previous_count+1 and wires.size()==reports.size(),"single report and wire")
		if reports.size()==previous_count: break
		var report:=reports.back() as ImpactReport
		expect.call(report.power==power and report.shot_id==shot.shot_id and world.get_node("HUD/Report").visible,"real report panel")
		if power==100:
			expect.call(world.planet.get_node("SpinPivot/Clouds").visible and world.fracture.weather_age<1., "cloud shell starts dispersing at impact")
		if power==10:
			expect.call(Engine.time_scale<.2,"physical slow motion")
			GameState.reset_world()
			expect.call(Engine.time_scale==1. and seq.phase.is_empty(),"reset during slow motion")
		elif power==50:
			seq.advance(1.5)
			seq.advance(7.)
			expect.call(events.has("aftershock"),"delayed sonification")
		else: seq.skip()
		expect.call(seq.phase.is_empty() and Engine.time_scale==1. and reports.size()==previous_count+1,"clean finish")
	var lost: float=world.fracture.integrity
	expect.call(lost==0. and world.get_node("%Fire").disabled,"destroyed target cannot fire")
	world.choose_target(&"venus")
	seq.skip()
	world.choose_target(&"earth")
	seq.skip()
	expect.call(world.fracture.integrity==lost and world.fracture.residue.multimesh!=null,"destroyed body has debris after return")
	expect.call(not world.planet.get_node("SpinPivot/Clouds").visible and not world.planet.get_node("SpinPivot/Atmosphere").visible,"no intact weather at destination")
	world.restore_target()
	expect.call(world.fracture.residue.multimesh==null and world.planet.get_node("SpinPivot/Clouds").visible and world.fracture.integrity==1. and world.fracture.population==8000000000,"restore action")
	expect.call(events.count("charge")==5 and events.count("fire")==4,"one event per accepted phase")
	var original: Dictionary=Settings.values.duplicate()
	for scale_id in Settings.RENDER_SCALES.size():
		var candidate:=original.duplicate()
		candidate.render_scale=scale_id
		Settings.apply(candidate)
		expect.call(is_equal_approx(tree.root.scaling_3d_scale,Settings.RENDER_SCALES[scale_id]),"actual internal resolution scale")
	Settings.apply(original)
	EventBus.impact_committed.disconnect(record_report)
	EventBus.news_event.disconnect(record_news)
	EventBus.discovered.disconnect(record_discovery)
	EventBus.charge_started.disconnect(record_charge)
	EventBus.fired.disconnect(record_fire)
	EventBus.aftershock.disconnect(record_bass)
	print("RAIL SEQUENCE CHECK routes=5 powers=91 reports=",reports.size()," news=",wires.size())

func record_report(report: ImpactReport) -> void: reports.append(report)
func record_news(id: int,_target: StringName,_key: StringName) -> void: wires.append(id)
func record_discovery(_id: StringName) -> void: events.append("arrived")
func record_charge(_id: int,_power: int) -> void: events.append("charge")
func record_fire(_id: int) -> void: events.append("fire")
func record_bass(_id: int) -> void: events.append("aftershock")
