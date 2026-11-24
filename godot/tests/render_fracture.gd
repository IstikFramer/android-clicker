extends SceneTree

func _initialize() -> void:
	run.call_deferred()

func save_frame(path: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var frame:=root.get_texture().get_image()
	if not frame or frame.save_jpg(path,.92)!=OK:
		push_error("Capture failed")
		quit(1)

func run() -> void:
	var folder:=OS.get_cmdline_user_args()[0]
	DirAccess.make_dir_recursive_absolute(folder)
	change_scene_to_file("res://scenes/main/Main.tscn")
	await scene_changed
	await root.get_node("SceneRouter").show_world()
	var world=current_scene.get_node("SceneHost/SpaceWorld")
	world.set_process(false)
	var settings=root.get_node("Settings")
	var options: Dictionary=settings.values.duplicate()
	options.resolution=0
	options.vsync=0
	world.get_node("HUD").hide()
	var planet: PlanetController=world.planet
	planet.get_node("SpinPivot").rotation=Vector3.ZERO
	planet.elapsed=0.
	planet.advance(0.,world.get_node("KeyLight").global_basis.z)
	for q in [0,2]:
		options.quality=q
		settings.apply(options)
		planet.update_lod(400,q)
		await save_frame(folder.path_join("stage03-"+("low" if q==0 else "high")+".jpg"))
	if not world.prepare_fracture():
		quit(1)
		return
	var result: Dictionary=world.demo_hit(Vector3(.77,.26,.58).normalized(),50)
	if result.is_empty():
		quit(1)
		return
	for i in 42: await physics_frame
	await save_frame(folder.path_join("stage03-fracture.jpg"))
	quit(0)
