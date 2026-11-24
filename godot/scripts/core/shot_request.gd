class_name ShotRequest
extends RefCounted

var shot_id: int
var weapon_id: StringName
var target_id: StringName
var power: int
var local_hit_dir: Vector3
var country_id: String
var seed: int

func is_valid() -> bool:
	if not TargetRegistry.allows(weapon_id, target_id):
		return false
	if not local_hit_dir.is_finite() or not local_hit_dir.is_normalized():
		return false
	if target_id != &"earth" and not country_id.is_empty():
		return false
	if not country_id.is_empty() and country_id != "Ocean" and country_id not in TranslationServer.get_all_countries():
		return false
	if target_id == &"earth" and weapon_id == &"railgun" and country_id.is_empty():
		return false
	match weapon_id:
		&"railgun": return power >= 10 and power <= 100
		&"gungnir": return power == 100
		&"vera": return power >= 20 and power <= 100
	return false
