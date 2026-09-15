"""R109 bounded learning, source labels, and held-exclusion contract."""

from datetime import datetime, timezone
import hashlib
import json


START = datetime(2026,9,15,8,56,tzinfo=timezone.utc).timestamp()
END = datetime(2026,9,15,16,56,tzinfo=timezone.utc).timestamp()
CUTOFF = END-300
CHILD = '121655d491bc55ba6bbd8eb732bc4f7a65215a07d3b6b2492f4fa623026f80f1'
BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
ANCHORS = '2ad09dbe9673f95cbe92cd41e70d83635702b615fb7295b8b3f850e9ee674753'
LABELS = ('ORIGINAL_8932_REHEARSAL','VERIFIED_BASE_ANCHOR',
          'R109_SELF_GENERATED_FUNCTIONAL','R109_CORRECTED_L2_CHILD_CONTINUATION')
CONDITIONS = ('ORDINARY_CONTROL','PERSISTENCE','FUNCTIONAL_METACOGNITION','PERCEPTION','EVIDENCE_HOPS')
GUIDANCE = {
    'ORDINARY_CONTROL': 'Solve the actual task using only the supplied evidence. Do not invent observations or tests.',
    'PERSISTENCE': 'Continue useful work on the actual unresolved goal. If an approach stalls, identify the concrete obstacle, try an evidence-grounded alternative, and carry the resulting state forward. Stop when the goal is satisfied or a genuine limitation is reached. Do not manufacture obstacles.',
    'FUNCTIONAL_METACOGNITION': 'Allocate effort to the actual uncertainty that could change the answer or next action. Check the consequential premise or intermediate result, then use the finding to continue, revise, or stop. Describe only work you actually perform; announcements and self-ratings are not evidence.',
    'PERCEPTION': 'Separate the task observations from your assumptions. Attend to the relevant constraint, relationship, unit, or boundary before proceeding. If new evidence changes the interpretation, update the working representation and use it in the next step. Never change the problem to make an alternative work.',
    'EVIDENCE_HOPS': 'Follow the evidence needed for the current goal: choose a relevant observation or memory, use its contents to select the next evidence, and integrate what you actually obtained. Carry intermediate state across steps and resolve contradictions against the source. Do not invent a retrieval, count hops as success, or repeat a path without new information.',
}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def allocation(node,index):
    require(node in ('node1','node2') and type(index) is int and index in range(7),'R109_only_physical0_to6')
    return index if node=='node1' else index+7


def lifetime(now,lease_end):
    require(START<=now<CUTOFF,'fixed_R109_lifetime_expired_or_not_started')
    require(END<=lease_end-21600,'verified_lease_margin')
    return dict(started_unix=START,native_deadline_unix=CUTOFF,hard_deadline_unix=END,
                max_gpu_hours=112,max_gpus=14,lease_end_unix=lease_end)


def batch_positions(update, prior_count, anchor_count, eligible_count=0):
    require(update>8932 and prior_count>=2394 and anchor_count==42,'resume8932_and_exact_sources')
    cursor=update-1
    return [('legacy',cursor%210),('prior',(2*cursor)%prior_count),
            ('anchor',cursor%anchor_count),
            ('eligible',cursor%eligible_count) if eligible_count else ('prior',(2*cursor+1)%prior_count)]


def validate_eligible(row,held_ids,held_families):
    require(row['source_label'] in LABELS[2:],'new_source_label_required')
    require(row['split']=='TRAIN' and row['task_id'] not in held_ids
            and row['contamination_family'] not in held_families,'held_excluded')
    require(row['functional_verdict']=='PASS' and row['grounding_verdict']=='PASS','actual_realization_and_grounding_required')
    require(row['source_archive_sha256'] and row['source_call_sha256'] and row['annotation_sha256'],'exact_native_provenance')
    require(row['target_actor']=='CHILD' and row['parent_text_masked'] is True,'child_only_target_parent_masked')
    require(row['target_sha256']==hashlib.sha256(row['target'].encode()).hexdigest(),'target_hash')
    require(bool(row['native_token_ids']) and row['prefix_sha256']==digest(row['student_prefix']),'actual_prefix_and_tokens')
    return row


def generation_messages(task,condition,previous=None):
    from organism_v6 import orch_rich_hot_node2_supply as old
    require(condition in CONDITIONS,'generation_condition')
    messages=old.messages(task,'ORIGINAL_RICH')
    messages[0]=dict(role='system',content=GUIDANCE[condition]+' No prescribed headings, method counts, minimum length, or first-person style.')
    if task['family']=='math':
        messages[-1]['content']+='\nFinish with FINAL: and the numeric answer.'
    if previous is not None:
        messages += [dict(role='assistant',content=previous),dict(role='user',content=
            'Continue from your actual work. Resolve any remaining uncertainty using the task evidence, correct a concrete error if found, and give the final answer. No external feedback or new observations were supplied. Do not fabricate a correction.')]
    return messages
