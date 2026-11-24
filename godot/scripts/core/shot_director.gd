class_name ShotDirector
extends RefCounted

enum State { MENU, LOADING, IDLE, TRAVEL, AIM, CHARGING, FIRING, IMPACT, AFTERMATH, RESETTING, PAUSED }
const NEXT := {
	State.MENU: [State.LOADING], State.LOADING: [State.IDLE],
	State.IDLE: [State.TRAVEL], State.TRAVEL: [State.AIM],
	State.AIM: [State.CHARGING], State.CHARGING: [State.FIRING],
	State.FIRING: [State.IMPACT], State.IMPACT: [State.AFTERMATH],
	State.AFTERMATH: [State.IDLE], State.RESETTING: [State.IDLE]
}

var state := State.MENU
var previous := State.MENU
var generation := 0
var active: ShotRequest
var used_ids: Dictionary[int, bool] = {}
var committed := false

func transition(next: State, token: int) -> bool:
	if token != generation or next not in NEXT.get(state, []):
		return false
	if next == State.CHARGING and active == null:
		return false
	if state == State.IMPACT and not committed:
		return false
	state = next
	if next == State.IDLE and active:
		var id := active.shot_id
		active = null
		EventBus.shot_finished.emit(id)
	return true

func fire(request: ShotRequest, token: int) -> bool:
	if token != generation or state != State.AIM or not request or not request.is_valid():
		return false
	if used_ids.has(request.shot_id):
		return false
	active = request.snapshot()
	used_ids[request.shot_id] = true
	committed = false
	transition(State.CHARGING, token)
	EventBus.shot_started.emit(active.snapshot())
	return true

func commit(report: ImpactReport, population: int, token: int) -> bool:
	if state != State.IMPACT or generation != token or committed or not active or not report:
		return false
	if report.shot_id != active.shot_id or report.target_id != active.target_id \
		or report.power != active.power or not report.is_valid(population):
		return false
	committed = true
	EventBus.impact_committed.emit(report)
	return true

func toggle_pause() -> void:
	if state == State.PAUSED:
		state = previous
	elif state not in [State.MENU, State.LOADING, State.RESETTING]:
		previous = state
		state = State.PAUSED

func abort(destination: State = State.IDLE) -> void:
	generation += 1
	active = null
	committed = false
	Engine.time_scale = 1.0
	state = destination
	previous = destination

func reset() -> void:
	abort(State.RESETTING)
	transition(State.IDLE, generation)
