extends Node

func _unhandled_key_input(event: InputEvent) -> void:
	if event.is_action_pressed("mute"):
		var master := AudioServer.get_bus_index("Master")
		AudioServer.set_bus_mute(master, not AudioServer.is_bus_mute(master))
		get_viewport().set_input_as_handled()
