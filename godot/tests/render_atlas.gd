extends SceneTree
## Capture the normal application on a real rendering driver.
## Run with --script res://tests/render_atlas.gd -- <output directory>.

func _initialize() -> void:
	run.call_deferred()

func capture(label: String, folder: String) -> bool:
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	if image == null or image.is_empty():
		return false
	return image.save_jpg(folder.path_join(label+".jpg"),0.90) == OK

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1 or DisplayServer.get_name() == "headless":
		push_error("Supply a capture directory and a graphical display")
		quit(2)
		return
	var output := args[0]
	DirAccess.make_dir_recursive_absolute(output)
	change_scene_to_file("res://scenes/main/Main.tscn")
	await scene_changed
	root.get_node("SceneRouter").show_world()
	for i in 4: await process_frame
	var world := current_scene.get_node("SceneHost/SpaceWorld")
	world.choose_weapon(&"vera")
	for id in TargetRegistry.ALL:
		world.choose_target(id)
		if id == &"earth":
			world.choose_region(CountryLookup.by_code["FI"])
			world.confirm_aim()
		if not await capture(id,output):
			quit(1)
			return
	for id in [&"railgun",&"gungnir",&"vera"]:
		world.choose_weapon(id)
		if not world.launch_view: world.toggle_station()
		if not await capture(id,output):
			quit(1)
			return
	quit(0)
