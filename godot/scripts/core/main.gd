extends Node

func _ready() -> void:
	SceneRouter.attach($SceneHost, $LoadingOverlay)
	# Release templates run package verification through the normal entry point.
	if "--verify-package" in OS.get_cmdline_user_args():
		add_child(load("res://tests/test_application.gd").new())
	elif "--railgun-demo" in OS.get_cmdline_user_args():
		start_railgun_demo.call_deferred()
	elif "--test-impact" in OS.get_cmdline_user_args():
		start_impact_demo.call_deferred()

func start_railgun_demo() -> void:
	await SceneRouter.show_world()
	var world=$SceneHost/SpaceWorld
	world.select_direction(Vector3(.83,.34,.43).normalized())
	world.fire_rail()

func start_impact_demo() -> void:
	var args:=OS.get_cmdline_user_args()
	var i:=args.find("--test-impact")
	if i+2>=args.size() or StringName(args[i+1]) not in TargetRegistry.ALL or not args[i+2].is_valid_int():
		push_error("Expected --test-impact <planet> <power> [railgun|gungnir|vera]")
		get_tree().quit(2)
		return
	var id:=StringName(args[i+1])
	var power:=args[i+2].to_int()
	var weapon:=StringName(args[i+3]) if args.size()>i+3 else (&"vera" if id==&"sun" else &"railgun")
	if not TargetRegistry.allows(weapon,id) or power>100 or power<(20 if weapon==&"vera" else 10) or (weapon==&"gungnir" and power!=100):
		push_error("Invalid test impact")
		get_tree().quit(2)
		return
	await SceneRouter.show_world()
	var world=$SceneHost/SpaceWorld
	world.demo_power=power
	world.choose_weapon(weapon)
	world.choose_target(id)
	SceneRouter.loading.show()
	await get_tree().process_frame
	if not world.prepare_fracture():
		get_tree().quit(1)
		return
	SceneRouter.loading.hide()
	world.frame_view()
	var token:=GameState.director.generation
	await get_tree().create_timer(1.2).timeout
	if not is_instance_valid(world) or token!=GameState.director.generation: return
	var hit:=Vector3(.77,.26,.58).normalized()
	var result: Dictionary=world.demo_hit(hit,power)
	if result.is_empty():
		push_error("Impact did not commit")
		return
	print("TEST IMPACT ",id," selected=",result.selected_ids.size()," physical=",world.fracture.pool.physical.size()," integrity=",result.integrity)
