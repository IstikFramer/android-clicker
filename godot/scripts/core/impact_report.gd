class_name ImpactReport
extends RefCounted

var shot_id: int
var target_id: StringName
var power: int
var damage_fraction: float
var integrity: float
var atmosphere_fraction: float
var crater_radius_game_km: float
var simulated_population_loss: int
var energy_index: float
var destroyed: bool
var status_key: StringName
var activated_fragment_count: int

func is_valid(population: int) -> bool:
	if target_id == &"saturn" and status_key not in [&"gas_impact", &"gas_dispersed"]:
		return false
	if target_id == &"sun" and status_key not in [&"solar_impact", &"supernova"]:
		return false
	if target_id not in [&"sun", &"saturn"] and status_key not in [&"solid_impact", &"solid_destroyed"]:
		return false
	return target_id in TargetRegistry.ALL and power >= 0 and power <= 100 \
		and damage_fraction >= 0.0 and damage_fraction <= 1.0 \
		and integrity >= 0.0 and integrity <= 1.0 \
		and atmosphere_fraction >= 0.0 and atmosphere_fraction <= 1.0 \
		and is_finite(crater_radius_game_km) and crater_radius_game_km >= 0.0 \
		and (target_id not in [&"saturn", &"sun"] or crater_radius_game_km == 0.0) \
		and simulated_population_loss >= 0 and simulated_population_loss <= population \
		and is_finite(energy_index) and energy_index >= 0.0 and activated_fragment_count >= 0
