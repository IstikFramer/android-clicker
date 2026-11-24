class_name TargetRegistry
extends RefCounted

const STANDARD := [&"mercury", &"venus", &"earth", &"mars", &"saturn"]
const ALL := [&"mercury", &"venus", &"earth", &"mars", &"saturn", &"sun"]
var integrity_by_id: Dictionary[StringName, float] = {}

func _init() -> void:
	for id in ALL:
		integrity_by_id[id] = 1.0

static func allows(weapon: StringName, target: StringName) -> bool:
	match weapon:
		&"railgun", &"gungnir": return target in STANDARD
		&"vera": return target in ALL
	return false
