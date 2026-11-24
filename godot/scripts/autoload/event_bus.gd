extends Node

signal target_selected(target_id: StringName)
signal weapon_selected(weapon_id: StringName)
signal shot_started(request: ShotRequest)
signal phase_changed(shot_id: int, phase: StringName, progress: float)
signal impact_committed(report: ImpactReport)
signal news_event(shot_id: int, target_id: StringName, event_key: StringName)
signal shot_finished(shot_id: int)
signal world_reset(reset_id: int)
signal settings_changed

signal discovered(target_id: StringName)
signal charge_started(shot_id: int, power: int)
signal fired(shot_id: int)
signal aftershock(shot_id: int)
signal signal_lost(target_id: StringName)
