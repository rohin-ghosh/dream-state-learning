# EVENT-sequence-v2 raw reduction report

Receipt FILE SHA256: `49dad92b29779ccbcd346deba243ab81e38e34d1288f67936050c0f752a5ee1f`
Receipt sealed digest: `901b063f0d1cfd279f42f0e3b86e679599377c8496016c576f3e2385dd0a463d`
Schema: `pcfl.event_sequence.v2.reduce_followup.v1/receipt`
Recorded kind/status: `NATIVE` / `VALIDATED_NOT_PROMOTED`

This renders an already-validated raw reduction. It checks the supplied file pin, seals and reporting consistency; it does not itself verify native custody, re-score raw text, execute models, or promote G3/H1/H2/parenting.
Three learner seeds (0/1/2), one shared bank8events (A4/B4), not independent banks. Strict correctness requires the recorded strict score and stop termination. W0 is diagnostic; W8 is exposed DEV, not confirmation. No pooled independent-bank estimate, confidence interval, significance test, or scientific interpretation is produced.

## W0 strict correctness

| State | seed0 A/4 | seed0 B/4 | seed0 truncations/8 | seed1 A/4 | seed1 B/4 | seed1 truncations/8 | seed2 A/4 | seed2 B/4 | seed2 truncations/8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NO_WRITE | 0/4 | 0/4 | 0/8 | 0/4 | 0/4 | 0/8 | 0/4 | 0/4 | 0/8 |
| A200 | 4/4 | 0/4 | 0/8 | 4/4 | 0/4 | 0/8 | 4/4 | 0/4 | 0/8 |
| B200_NEW_DOSE | 0/4 | 4/4 | 0/8 | 0/4 | 4/4 | 0/8 | 0/4 | 4/4 | 0/8 |
| B400_FIXED_WORK | 0/4 | 4/4 | 0/8 | 0/4 | 4/4 | 0/8 | 0/4 | 4/4 | 0/8 |
| REPLAY400 | 4/4 | 4/4 | 0/8 | 4/4 | 4/4 | 0/8 | 4/4 | 4/4 | 0/8 |
| CLEAN_CUM600 | 4/4 | 4/4 | 0/8 | 4/4 | 4/4 | 0/8 | 4/4 | 4/4 | 0/8 |

### W0 fixed paired contrasts

Signed correct-count differences (REPLAY400 minus control), each over the same four items; vectors retain item order. A = retention; B = acquisition. CLEAN_CUM600 is descriptive phase-boundary only.

| Contrast | Seed | A delta/4 | A paired vector | B delta/4 | B paired vector |
| --- | --- | --- | --- | --- | --- |
| REPLAY400-B200_NEW_DOSE | 0 | +4/4 | +1, +1, +1, +1 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-B200_NEW_DOSE | 1 | +4/4 | +1, +1, +1, +1 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-B200_NEW_DOSE | 2 | +4/4 | +1, +1, +1, +1 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-B400_FIXED_WORK | 0 | +4/4 | +1, +1, +1, +1 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-B400_FIXED_WORK | 1 | +4/4 | +1, +1, +1, +1 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-B400_FIXED_WORK | 2 | +4/4 | +1, +1, +1, +1 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-CLEAN_CUM600 | 0 | +0/4 | +0, +0, +0, +0 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-CLEAN_CUM600 | 1 | +0/4 | +0, +0, +0, +0 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-CLEAN_CUM600 | 2 | +0/4 | +0, +0, +0, +0 | +0/4 | +0, +0, +0, +0 |

## W8 strict correctness

| State | seed0 A/4 | seed0 B/4 | seed0 truncations/8 | seed1 A/4 | seed1 B/4 | seed1 truncations/8 | seed2 A/4 | seed2 B/4 | seed2 truncations/8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NO_WRITE | 0/4 | 0/4 | 0/8 | 0/4 | 0/4 | 0/8 | 0/4 | 0/4 | 0/8 |
| A200 | 4/4 | 0/4 | 0/8 | 4/4 | 0/4 | 0/8 | 4/4 | 0/4 | 0/8 |
| B200_NEW_DOSE | 0/4 | 4/4 | 0/8 | 0/4 | 4/4 | 0/8 | 0/4 | 4/4 | 0/8 |
| B400_FIXED_WORK | 0/4 | 4/4 | 0/8 | 0/4 | 4/4 | 0/8 | 0/4 | 4/4 | 0/8 |
| REPLAY400 | 4/4 | 4/4 | 0/8 | 4/4 | 4/4 | 0/8 | 4/4 | 4/4 | 0/8 |
| CLEAN_CUM600 | 4/4 | 4/4 | 0/8 | 4/4 | 4/4 | 0/8 | 4/4 | 4/4 | 0/8 |

### W8 fixed paired contrasts

Signed correct-count differences (REPLAY400 minus control), each over the same four items; vectors retain item order. A = retention; B = acquisition. CLEAN_CUM600 is descriptive phase-boundary only.

| Contrast | Seed | A delta/4 | A paired vector | B delta/4 | B paired vector |
| --- | --- | --- | --- | --- | --- |
| REPLAY400-B200_NEW_DOSE | 0 | +4/4 | +1, +1, +1, +1 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-B200_NEW_DOSE | 1 | +4/4 | +1, +1, +1, +1 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-B200_NEW_DOSE | 2 | +4/4 | +1, +1, +1, +1 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-B400_FIXED_WORK | 0 | +4/4 | +1, +1, +1, +1 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-B400_FIXED_WORK | 1 | +4/4 | +1, +1, +1, +1 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-B400_FIXED_WORK | 2 | +4/4 | +1, +1, +1, +1 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-CLEAN_CUM600 | 0 | +0/4 | +0, +0, +0, +0 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-CLEAN_CUM600 | 1 | +0/4 | +0, +0, +0, +0 | +0/4 | +0, +0, +0, +0 |
| REPLAY400-CLEAN_CUM600 | 2 | +0/4 | +0, +0, +0, +0 | +0/4 | +0, +0, +0, +0 |

## Physical and excluded costs

Physical totals include excluded prior failed work. Excluded work is not accepted evidence and must not be added again. Accepted work per learner: 5 fits, 1800 updates, 7200 presentations, 96 readout calls.

| Learner | Physical fits | Physical updates | Physical presentations | Physical readout_calls | Excluded fits | Excluded updates | Excluded presentations | Excluded readout_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| seed0 | 8 | 2400 | 9600 | 96 | 3 | 600 | 2400 | 0 |
| seed1 | 6 | 2000 | 8000 | 96 | 1 | 200 | 800 | 0 |
| seed2 | 6 | 2000 | 8000 | 96 | 1 | 200 | 800 | 0 |
| Learner sum | 20 | 6400 | 25600 | 288 | 5 | 1000 | 4000 | 0 |

## Elapsed seconds

Summed across learners, NOT wallclock campaign duration. Initial collections + excluded prior failures + followup = total. Nested fit/readout timings overlap these intervals and are not added again.

| Learner | Initial collections | Excluded prior failures | Followup | Total |
| --- | --- | --- | --- | --- |
| seed0 | 318.807367 | 576.152203 | 1445.287808 | 2340.247377 |
| seed1 | 319.046470 | 190.169864 | 1427.124744 | 1936.341078 |
| seed2 | 318.357225 | 191.799893 | 1425.905469 | 1936.062586 |
| Learner sum (not wallclock) | 956.211062 | 958.121959 | 4298.318021 | 6212.651042 |
