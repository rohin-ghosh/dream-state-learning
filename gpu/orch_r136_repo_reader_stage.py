"""R136 fresh-life preparation with the original, unextended ovx3 lease."""

import argparse
import json
from pathlib import Path

from gpu.orch_r133_stage_child import sha, stage


LEASE_PATH = Path('/localhome/local-rohing/orch_r115_grid_pair_20260915/A4/independent_r119_recovery_v2/LEASE_BUDGET.json')
LEASE_SHA256 = '287e36bc9b646401f5382b06c8bda4e71748a5f94d6eb011d436c1ead7b246a5'
GPU_UUID = 'GPU-9e6cdf73-7181-4405-2aec-787cc73a3e5b'
REQUESTED_WALL = 1789617240
LEASE_END = 1789617840


def new_template(template):
    result = dict(template)
    result.pop('authorized_wall_extension', None)
    result.pop('preupdate_recovery', None)
    expected = dict(seed=0, anchor_lambda=0.25, new_presentations=16, rehearsal_presentations=1,
                    segments_per_sleep=2, segment_tokens=512, context_limit=16384,
                    readout_revision=2, max_sleeps=None, presentation_version='R125_PLAIN_CONTEXT_V1')
    if any(result.get(key) != value for key, value in expected.items()):
        raise ValueError('unchanged_R127_free_seed0_configuration')
    if result.get('presleep_variant', 'free_distillation') != 'free_distillation':
        raise ValueError('free_distillation_only')
    return result


def startup(original, base, wall):
    public = original.split('### Resources and initial orientation')[0]
    return public + f'''### Resources and initial orientation

You run on one assigned GPU, physical 7, under the ovx3 allocation. Your ongoing
session archive is at {base}/run1. Your read-only reviewed repository snapshot
is at {base}/snapshot1. The snapshot initially contains only overview.md,
continuity.md and access.md: public-facing documentation and a published
aggregate continuity digest. It is NOT all experiment results.

The repository file tool is pending at startup. Do not assume it is connected
until a real Tool environment result from access.md arrives. Thereafter you can
request an actual file read with a standalone line such as:
repo_read overview.md
Only those three allowlisted names are accepted. Arbitrary paths, writes,
shell, CPU/GPU execution and network tools are not connected. A proposed read
or predicted output is not a result. Real file results arrive as attributed
Tool environment messages with retained source receipts. No autonomous writer,
unrestricted repository access or extra GPUs are available.

Your programme is repository exploration: investigate what the project does,
what its published evidence establishes, what remains uncertain, and how to
distinguish observations from your own hypotheses. Astra is one asynchronous
conversational parent, attending to your actual activity, metacognition,
self-reflection, judgment, perception and reported confidence or frustration.
Ask questions, disagree with reasons, follow curiosity, and avoid inventing
unread files or treating repeated claims as evidence. No fixed thought format
is required. The parent cannot see sealed evaluations.

Coverage excludes credentials, host/provider configuration, the coordination
notebook, held/FINAL material, answer keys, raw evaluations and R130 outputs.
Only newly reviewed safe snapshots can expand access. Separate capability
checks keep their contents outside this conversation and training. No learning
improvement is established by this launch or by the earlier continuity audit.

The existing allocation ends this life by Unix {wall:.0f}; this is the earlier
authorized receipt wall, not a new lease or an extension. Do not infer access
to additional resources from plans or suggestions. Continue useful activity
while awaiting messages; raw history and tool receipts remain preserved.
'''


def prepare(source, base, template_path, startup_base, commit, cpu_receipt):
    source, base = Path(source), Path(base)
    if sha(LEASE_PATH) != LEASE_SHA256:
        raise ValueError('original_lease_receipt_hash')
    lease = json.loads(LEASE_PATH.read_text())
    if lease['lease_end_unix'] != LEASE_END or lease['hard_end_unix'] > REQUESTED_WALL:
        raise ValueError('original_lease_budget_only')
    template = new_template(json.loads(Path(template_path).read_text()))
    fresh = base / 'FRESH_TEMPLATE.json'
    with fresh.open('x') as output:
        json.dump(template, output, sort_keys=True, indent=2)
    startup_path = source / 'STARTUP.md'
    with startup_path.open('x') as output:
        output.write(startup(Path(startup_base).read_text(), base, lease['hard_end_unix']))
    result = stage(fresh, source, base / 'control1', base / 'run1', startup_path,
                   LEASE_PATH, 7, GPU_UUID, commit, cpu_receipt)
    result.update(effective_wall=lease['hard_end_unix'], requested_wall=REQUESTED_WALL,
                  lease_sha256=LEASE_SHA256, lease_end_unix=LEASE_END)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'base', 'template-path', 'startup-base', 'commit', 'cpu-receipt'):
        parser.add_argument('--' + name, required=True)
    print(json.dumps(prepare(**vars(parser.parse_args())), sort_keys=True))
