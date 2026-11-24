extends Node

const MENU := preload("res://scenes/ui/MainMenu.tscn")
const WORLD := preload("res://scenes/main/SpaceWorld.tscn")
const SETTINGS := preload("res://scenes/ui/SettingsMenu.tscn")
const CREDITS := preload("res://scenes/ui/Credits.tscn")
var host: Node
var loading: CanvasLayer

func attach(scene_host: Node, overlay: CanvasLayer) -> void:
	host = scene_host
	loading = overlay
	show_menu()

func replace(scene: PackedScene) -> void:
	for old in host.get_children():
		host.remove_child(old)
		old.queue_free()
	host.add_child(scene.instantiate())

func show_world() -> void:
	var director := GameState.director
	var token := director.generation
	if not director.transition(ShotDirector.State.LOADING, token):
		return
	loading.show()
	await get_tree().process_frame
	await get_tree().process_frame
	if token == director.generation and is_instance_valid(host):
		replace(WORLD)
		director.transition(ShotDirector.State.IDLE, token)
		loading.hide()

func show_menu() -> void:
	GameState.director.abort(ShotDirector.State.MENU)
	loading.hide()
	replace(MENU)

func show_settings() -> void:
	replace(SETTINGS)

func show_credits() -> void:
	replace(CREDITS)
