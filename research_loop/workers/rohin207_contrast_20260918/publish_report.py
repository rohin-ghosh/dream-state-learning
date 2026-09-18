"""Publish aggregate and pseudonymous contest metrics, never caption text."""

from datetime import datetime, timezone
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    reports = [json.loads((root / name).read_text()) for name in ('WIDEGAP_REPORT.json', 'BT8K_REPORT.json')]
    widegap, bt8k = reports
    assert widegap['case_ids_sha256'] == bt8k['case_ids_sha256']
    assert widegap['private_cases_sha256'] == bt8k['private_cases_sha256']
    assert all(not report['FINAL_read'] and not report['locked_validation_read'] for report in reports)
    kinds = ('word_shuffled', 'other_contest', 'scene_description', 'truncated', 'nonsense', 'mid_tier')
    lines = ['# R207: constructed-contrast results', '',
             'Owner: Main. Actual inference: node4 physical0, existing selected scalar adapters, no weight updates.',
             '20 fitting-held DEVELOPMENT contests, five top published-ranked captions per contest, six contrast types; '
             '600 scored pairs per judge. The two judges received exactly the same cases. No skips. '
             'This reuses development contests, not a fresh confirmatory test; locked validation and FINAL were untouched.', '',
             '| Contrast | Widegap wins/ties/losses | Accuracy (ties ½) | BT8k wins/ties/losses | Accuracy (ties ½) |',
             '| --- | --- | ---: | --- | ---: |']
    for kind in kinds:
        metrics = [report['by_type'][kind] for report in reports]
        cells = [kind]
        for metric in metrics:
            cells.extend((f"{metric['wins']}/{metric['ties']}/{metric['losses']}",
                          f"{100 * metric['tie_half_accuracy']:.1f}%"))
        lines.append('| ' + ' | '.join(cells) + ' |')
    lines += ['', '**Readout:** widegap improves over BT8k on truncated, nonsense, and real mid-tier contrasts. '
              '**Both fail to reliably distinguish good captions for this image from good captions for another image.** '
              'Widegap51% / BT8k46% on mismatches is not evidence of scene grounding. Shuffling/nonsense discrimination '
              'does not establish human humor judgment. Relative-rank game acceptance remains explicitly provisional; '
              'pixel novelty is separate from scene relevance and humor.', '',
              'The 30% positive-vote-mass condition is removed by Rohin207. It is not a promotion gate. '
              'Scalar values are not vote probabilities. Mid-tier means the center of the real published-rank ordering; '
              'other-contest pairs use a different scene group. Ties and losses remain in the report.', '',
              '## Actual receipts', '']
    for report in reports:
        completed = datetime.fromtimestamp(report['completed_unix'], timezone.utc).isoformat()
        lines.append(f"- {report['judge']}: completed {completed}; load+prepare+score {report['elapsed_seconds']:.2f}s; "
                     f"selected config SHA256 `{report['judge_config']['sha256']}`.")
    lines += [f"- Common case-ID digest: `{widegap['case_ids_sha256']}`.",
              '- Remote root: `/localhome/local-rohing/orch_r207_caption_contrast_20260918`.',
              '- Two input-preparation failures (unready scene selection; old BT8k metadata missing ranks) were preserved '
              'and repaired before those cases were scored. Both scored jobs use the same rank-bearing development suite.',
              '- Per-pair pseudonymous scores and skipped-case counts: `WIDEGAP_REPORT.json`, `BT8K_REPORT.json` '
              'under `research_loop/workers/rohin207_contrast_20260918/`. Private captions remain evaluator-only on node4.', '',
              '## Per-contest accuracy', '',
              'Each cell is **widegap / BT8k**, wins plus half ties out of5 opportunities. IDs are pseudonyms.', '',
              '| Contest | Shuffled | Other contest | Scene | Truncated | Nonsense | Mid-tier |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for contest in sorted(widegap['by_contest']):
        cells = [contest]
        for kind in kinds:
            cells.append(' / '.join(f"{100 * report['by_contest'][contest][kind]['tie_half_accuracy']:.0f}%"
                                    for report in reports))
        lines.append('| ' + ' | '.join(cells) + ' |')
    target = Path('research_notes/analysis/R207_CONSTRUCTED_CONTRAST_2026-09-18.md')
    target.write_text('\n'.join(lines) + '\n')
    print(target)


if __name__ == '__main__':
    main()
