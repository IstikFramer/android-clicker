extends Node

var director := ShotDirector.new()
var registry := TargetRegistry.new()
var snapshot := WorldSnapshot.new(71023, registry)

func reset_world() -> void:
	director.reset()
	damage_history.clear()
	registry.integrity_by_id = snapshot.starting_integrity.duplicate()
	EventBus.world_reset.emit(director.generation)

var damage_history: Dictionary={}

var next_shot_id := 1
