extends RefCounted

func check(expect: Callable) -> void:
	var request := ShotRequest.new()
	request.shot_id = 11
	request.weapon_id = &"railgun"
	request.target_id = &"earth"
	request.power = 10
	request.local_hit_dir = Vector3.UP
	expect.call(not request.is_valid(), "Earth railgun needs a region or Ocean")
	request.country_id = "Ocean"
	expect.call(request.is_valid(), "railgun lower bound")
	request.country_id = "RU"
	expect.call(request.is_valid(), "country identifier")
	request.country_id = "unknown"
	expect.call(not request.is_valid(), "invalid country")
	request.country_id = ""
	request.target_id = &"saturn"
	request.power = 9
	expect.call(not request.is_valid(), "power below range")
	request.weapon_id = &"vera"
	request.target_id = &"sun"
	request.power = 20
	expect.call(request.is_valid(), "VERA can target Sun")
	request.power = 19
	expect.call(not request.is_valid(), "VERA lower bound")
	request.weapon_id = &"gungnir"
	request.power = 100
	expect.call(not request.is_valid(), "Gungnir cannot target Sun")
	request.target_id = &"jupiter"
	expect.call(not request.is_valid(), "Jupiter is scenery")
	request.target_id = &"mars"
	request.power = 99
	expect.call(not request.is_valid(), "Gungnir power fixed")
	request.power = 100
	request.local_hit_dir *= 2
	expect.call(not request.is_valid(), "reject unnormalized directions")
	request.local_hit_dir = Vector3.LEFT

	var director := ShotDirector.new()
	var token := director.generation
	expect.call(not director.fire(request, token), "fire gated by AIM")
	for phase in [ShotDirector.State.LOADING, ShotDirector.State.IDLE, ShotDirector.State.TRAVEL, ShotDirector.State.AIM]:
		expect.call(director.transition(phase, token), "valid preparation transition")
	expect.call(director.fire(request, token), "accept valid shot")
	director.toggle_pause()
	expect.call(director.state == ShotDirector.State.PAUSED, "pause")
	director.toggle_pause()
	expect.call(director.state == ShotDirector.State.CHARGING, "restore previous state")
	director.transition(ShotDirector.State.FIRING, token)
	director.transition(ShotDirector.State.IMPACT, token)
	var report := ImpactReport.new()
	report.shot_id = request.shot_id
	report.target_id = request.target_id
	report.power = request.power
	report.status_key = &"solid_impact"
	report.simulated_population_loss = 2
	expect.call(not director.commit(report, 1, token), "reject impossible loss")
	expect.call(director.commit(report, 2, token), "first commit")
	expect.call(not director.commit(report, 2, token), "reject duplicate")
	director.reset()
	expect.call(not director.transition(ShotDirector.State.TRAVEL, token), "reject stale callback")
	expect.call(not director.commit(report, 2, token), "reject stale report")
