extends SceneTree

var started_at:=0
var events: Array[String]=[]
var impact_power: int

func _initialize() -> void:
	test.call_deferred()

func test() -> void:
	var bus:=root.get_node("EventBus")
	bus.charge_started.connect(func(_id,_power): events.append("charge"))
	bus.fired.connect(func(_id): events.append("fire"))
	bus.impact_committed.connect(func(report): events.append("impact"); impact_power=report.power)
	bus.aftershock.connect(func(_id): events.append("aftershock"))
	bus.shot_finished.connect(func(_id): events.append("finished"))
	started_at=Time.get_ticks_msec()
	change_scene_to_file("res://scenes/main/Main.tscn")
	while not events.has("finished") and Time.get_ticks_msec()-started_at<32000:
		await process_frame
	var elapsed:=float(Time.get_ticks_msec()-started_at)/1000.
	if events!=["charge","fire","impact","aftershock","finished"] or impact_power!=50 or elapsed<8. or not is_equal_approx(Engine.time_scale,1.):
		push_error("Unexpected quick-launch sequence %s in %.2fs" % [events,elapsed])
		quit(1)
		return
	print("RAIL LIVE CLOCK PASS seconds=%.2f" % elapsed)
	quit(0)
