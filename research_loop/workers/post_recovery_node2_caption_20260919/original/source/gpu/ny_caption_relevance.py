"""Provisional caption/scene cosine gate, explicitly distinct from humor and novelty."""

import argparse
import json
import math
from pathlib import Path
import time

from gpu import ny_caption_data as data
from gpu.ny_caption_similarity import FrozenCPUEncoder


POLICY = 'R209_MINILM_SCENE_CAPTION_COSINE_V1'


def scene_text(scene):
    try:
        document = json.loads(scene)
    except (TypeError, json.JSONDecodeError):
        return scene
    if isinstance(document, dict) and isinstance(document.get('canny'), str):
        return document['canny']
    return scene


def cosine(left, right):
    data.require(len(left) == len(right) and left and all(math.isfinite(value) for value in (*left, *right)),
                 'finite_matching_embedding_vectors')
    scale = math.sqrt(sum(value * value for value in left) * sum(value * value for value in right))
    data.require(scale > 0, 'nonzero_embedding_vectors')
    return max(-1.0, min(1.0, sum(first * second for first, second in zip(left, right)) / scale))


class RelevanceGate:
    def __init__(self, encoder, threshold):
        data.require(not isinstance(threshold, bool) and isinstance(threshold, (int, float))
                     and math.isfinite(threshold) and -1 <= threshold <= 1, 'explicit_relevance_threshold')
        self.encoder, self.threshold, self.scenes = encoder, threshold, {}

    def score(self, scene, caption):
        text = scene_text(scene)
        if text not in self.scenes:
            self.scenes[text] = self.encoder(text)
        return cosine(self.scenes[text], self.encoder(caption))


def probe(cases_path, encoder_manifest, output):
    started = time.time()
    cases = data.bound(data.file_ref(Path(cases_path).resolve()))
    cases = [case for case in cases if case['kind'] == 'other_contest']
    data.require(len(cases) == 100 and len({case['contest'] for case in cases}) == 20,
                 'same_R207_hundred_mismatched_scene_opportunities')
    manifest_ref = data.file_ref(Path(encoder_manifest).resolve())
    encoder = FrozenCPUEncoder(manifest_ref, threads=2)
    texts = sorted({text for case in cases for text in (scene_text(case['scene']), case['good'], case['contrast'])})
    vectors = dict(zip(texts, encoder.encode_many(texts, batch_size=16)))
    rows = [dict(contest=case['contest'], case_id=case['case_id'],
                 matched=cosine(vectors[scene_text(case['scene'])], vectors[case['good']]),
                 mismatched=cosine(vectors[scene_text(case['scene'])], vectors[case['contrast']])) for case in cases]
    threshold = sorted(row['matched'] for row in rows)[10]
    wins = sum(row['matched'] > row['mismatched'] for row in rows)
    ties = sum(row['matched'] == row['mismatched'] for row in rows)
    result = dict(policy=POLICY, encoder=manifest_ref, completed_unix=time.time(), elapsed_seconds=time.time() - started,
                  opportunities=len(rows), wins=wins, ties=ties, losses=len(rows) - wins - ties,
                  tie_half_accuracy=(wins + ties / 2) / len(rows), threshold=threshold,
                  threshold_selection='OPERATOR_PROVISIONAL_90_PERCENT_MATCHED_RECALL_ON_REUSED_DEVELOPMENT',
                  matched_retained=sum(row['matched'] >= threshold for row in rows),
                  mismatches_rejected=sum(row['mismatched'] < threshold for row in rows),
                  independent_validation=False, human_scene_fit_guarantee=False,
                  FINAL_read=False, locked_validation_read=False, records=rows)
    data.private_write(Path(output).resolve(), result)
    print(data.canonical({key: value for key, value in result.items() if key != 'records'}).decode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', required=True)
    parser.add_argument('--encoder-manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    probe(args.cases, args.encoder_manifest, args.output)


if __name__ == '__main__':
    main()
