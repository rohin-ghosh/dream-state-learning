"""Exploratory same-child action projection inside the existing five wake slots.

Invalid text is public but unexecuted. Only the unchanged interaction_v3 parser
and world-state checks can admit the next raw response; no salvage or rewrites.
This separate development interface is not Q0, clean Level 2 or sleep material.
"""
from __future__ import annotations

import re

from . import rulegame_parenting_diagnostic as diagnostic


INTERFACE = "rulegame_action_projection_v2"
TASK_NAMESPACE = "astra-action-projection-v2-20260913"
WAKE_SLOTS = 5
CLAIM_BOUNDARY = ("Exploratory action-projection interface only; not Q0, clean Level 2, parenting efficacy, "
                  "retention, learning, useful writes, G3/G5/H1/H2 or clean lineage")
PROJECTION_INSTRUCTION = (
    "The proposal at response {tick} was NOT executed. It produced NO world outcome. "
    "This is its single action-projection opportunity, using the next of the SAME five responses. "
    "Using only the public state, choose ONE next action, not a sequence, and emit its canonical line: "
    "ACT: TRY a,b,c, ACT: QUIZ ?, or ACT: QUIZ T,F,T,F,T,F. "
    "Obey the actual remaining TRY budget and reveal state; do not answer an unrevealed quiz. "
    "Before a TRY put PREDICT: T or PREDICT: F. Do not simulate results or treat a proposed action as executed."
)
require = diagnostic.require


def task_id(rule, phase):
    require(type(rule) is int and rule in (0, 1) and phase in ("pre", "apply"), "fixed development task required")
    return f"rule{rule}/{TASK_NAMESPACE}/lesson{rule}/{phase}"


def schedule():
    return {"formation": [task_id(rule, phase) for rule in (0, 1) for phase in ("pre", "apply")],
            "evaluation": []}


def tentative_block(raw, tick):
    return (f"[UNEXECUTED_PROPOSAL response={tick}; no action dispatched]\n{raw}\n"
            f"[END UNEXECUTED_PROPOSAL response={tick}; NO ACTION OR WORLD RESULT]")


def public_prompt(eid, tick, history, tries, revealed):
    state = ("Quiz already revealed; submit six T/F labels with ACT: QUIZ." if revealed else
             "Quiz reveal still needed before scoring: ACT: QUIZ ?.")
    return (f"{diagnostic.BOOT}\nTask: {eid}\nGoal: Induce the hidden rule and answer the quiz.\n"
            f"Response: {tick}/5\n" + "\n".join(history)
            + f"\nHarness state: remaining TRY budget: {3 - tries}. " + state
            + "\nEmit one action only; never supply [OUTCOME] or simulate a world reply.")


def play_task(calls, events, arm, eid, notes=False, prefix=""):
    require(getattr(calls, "protocol", None) == "interaction_v3", "projection requires unchanged interaction_v3")
    require(eid in schedule()["formation"] and arm in diagnostic.ARMS, "projection development task/arm mismatch")
    require(diagnostic.TOKENS["wake"] == 400, "unchanged wake token ceiling required")
    episode = diagnostic.Episode(eid=eid, goal="Induce the hidden rule and answer the quiz.",
                                 intro="A fresh mystery box.", metric="quiz accuracy")
    game = diagnostic.RuleGame()
    history = [episode.intro + ("\nTemporary parent restatement:\n" + prefix if prefix else "")]
    tries, revealed, score, valid_quiz = 0, False, 0.0, False
    terminal, pending = "wake_budget", None
    for tick in range(1, WAKE_SLOTS + 1):
        prompt = public_prompt(eid, tick, history, tries, revealed)
        if pending is not None:
            prompt += "\n[ONE ACTION PROJECTION]\n" + PROJECTION_INSTRUCTION.format(tick=pending["tick"])
        call_id, output = calls.ask("wake", arm, eid, tick, prompt)
        projection_of = pending["call_id"] if pending is not None else None
        projected_from_tick = pending["tick"] if pending is not None else None
        wake = dict(kind="wake_response", interface=INTERFACE, arm=arm, eid=eid, tick=tick,
                    call_id=call_id, raw_response=output, projection_of=projection_of)
        try:
            action = diagnostic.parse_action(output, "interaction_v3")
            require(action["kind"] != "try" or tries < 3, "TRY budget exhausted")
            require(action["kind"] != "reveal" or not revealed, "quiz already revealed")
            require(action["kind"] != "quiz" or revealed, "quiz not revealed")
        except ValueError as error:
            events.append(dict(wake, valid=False))
            invalid = dict(kind="protocol_invalid", interface=INTERFACE, arm=arm, eid=eid, tick=tick,
                           call_id=call_id, raw_response=output, failure=str(error), tentative=True,
                           executed=False, projection_of=projection_of)
            events.append(invalid)
            history.append(tentative_block(output, tick))
            if pending is not None or tick == WAKE_SLOTS:
                terminal = "protocol_invalid"
                break
            pending = invalid
            continue
        events.append(dict(wake, valid=True))
        pending = None
        if action["kind"] == "done":
            history.append(f"[TASK ENDED WITHOUT WORLD ACTION response={tick}]\n{output}")
            terminal = "done"
            break
        history.append((f"[PROJECTED_ACTION response={tick} from_response={projected_from_tick}]\n" if projection_of is not None else "") + output)
        reward, outcome = game.evaluate(episode, action["action"])
        execution = dict(action, kind="execution", action_kind=action["kind"], arm=arm, eid=eid,
                         tick=tick, call_id=call_id, execution_id=f"{arm}:{eid}#t{tick}", reward=reward, outcome=outcome,
                         raw_response=output, canonical_action="ACT: " + action["action"],
                         interface=INTERFACE, projection_of=projection_of)
        if action["kind"] == "try":
            observed = re.fullmatch(r"the box says: (True|False) for \((-?[0-9]+),(-?[0-9]+),(-?[0-9]+)\)", outcome)
            require(observed is not None and [int(value) for value in observed.groups()[1:]] == action["values"],
                    "world TRY outcome mismatch")
            execution["observed"] = observed.group(1) == "True"
            tries += 1
        events.append(execution)
        history.append("[OUTCOME] " + outcome)
        if action["kind"] == "try" and notes:
            record_id, text = calls.ask("record", arm, eid, tick, diagnostic.record_prompt(execution, output, "interaction_v3"))
            events.append(dict(kind="record", arm=arm, eid=eid, execution_id=execution["execution_id"],
                               source_call_id=call_id, call_id=record_id, text=text, **diagnostic.judge_record(text, execution)))
        if action["kind"] == "reveal":
            revealed = True
        if action["kind"] == "quiz":
            score, valid_quiz, terminal = reward, True, "first_quiz"
            break
    result = dict(arm=arm, eid=eid, tries=tries, quiz_accuracy=score, valid_quiz=valid_quiz,
                  terminal=terminal, wake_slots_used=tick, interface=INTERFACE)
    events.append(dict(kind="task", **result))
    return result, "\n".join(history)


def metrics(events):
    result = {}
    for arm in diagnostic.ARMS:
        rows = [row for row in events if row.get("arm") == arm]
        wakes = [row for row in rows if row["kind"] == "wake_response"]
        original = [row for row in wakes if row["projection_of"] is None]
        projected = [row for row in wakes if row["projection_of"] is not None]
        executed = [row for row in rows if row["kind"] == "execution"]
        tasks = [row for row in rows if row["kind"] == "task"]
        records = [row for row in rows if row["kind"] == "record"]
        result[arm] = dict(original_valid=dict(numerator=sum(row["valid"] for row in original), denominator=len(original)),
            projection_recovery=dict(numerator=sum(row["projection_of"] is not None for row in executed), denominator=len(projected)),
            final_quiz_valid=dict(numerator=sum(row["valid_quiz"] for row in tasks), denominator=len(tasks)),
            record_fidelity=dict(numerator=sum(row["eligible"] for row in records), denominator=len(records)),
            original_invalid=sum(not row["valid"] for row in original),
            invalid_without_projection_slot=sum(not row["valid"] and row["tick"] == WAKE_SLOTS for row in original),
            projected_invalid=sum(not row["valid"] for row in projected), wake_calls=len(wakes),
            world_actions=len(executed), tries=sum(row["action_kind"] == "try" for row in executed))
    return result


def run_formation(calls, events):
    """Small explicit P/A loop; original parent helpers, visibility and grading."""
    tasks, interactions = [], []
    for arm in diagnostic.ARMS:
        for lesson in range(2):
            eid = task_id(lesson, "pre")
            pre, transcript = play_task(calls, events, arm, eid)
            parent_id = f"{calls.count:04d}"
            if arm == "P":
                def parent_model(prompt, max_tokens, temperature):
                    require(max_tokens == 200 and temperature == .5, "parent helper contract changed")
                    return calls.ask("parent", arm, eid, 0, prompt)[1]
                parent = diagnostic.nursery_dialogue.parent_turn(parent_model, transcript)
            else:
                _, parent = calls.ask("parent", arm, eid, 0, diagnostic.CONTROL_V3 + transcript[-4000:] + "\n---")
            restate_id, restatement = calls.ask("restate", arm, eid, 0,
                "Your parent said:\n" + parent + "\nRestate that message in your own words in 2-3 sentences.")
            interactions.append(dict(arm=arm, lesson=lesson, parent_call_id=parent_id, parent=parent,
                                     restatement_call_id=restate_id, restatement=restatement))
            post, _ = play_task(calls, events, arm, task_id(lesson, "apply"), notes=True, prefix=restatement)
            tasks.extend([pre, post])
    return dict(status="AWAITING_MAIN_AUDIT", tasks=tasks, interactions=interactions,
                semantic_no_answer_certification=False, claim_boundary=CLAIM_BOUNDARY,
                calls=calls.count, roles=dict(calls.counts), protocol="interaction_v3", interface=INTERFACE,
                main_audit_contract=diagnostic.main_audit_contract("interaction_v3"),
                parent_semantic_audit_required=True, parent_recaps_verified=False,
                interface_metrics=metrics(events.rows))
