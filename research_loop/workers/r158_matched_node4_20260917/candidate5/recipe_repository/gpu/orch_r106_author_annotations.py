"""Main's full-output R106 audit, bound to immutable native text hashes."""

import argparse
import json
from pathlib import Path


CATEGORY_CODES = dict(D='direct_computation', G='restated_givens',
                      C='checks_verification', J='judgments_asides',
                      M='meta_comments', F='final_answer')

FIXED = [
    ('5754becbb27cbf5cc10d6fa2411e258b3d11eee813ee7d44651230bd14768ab2', 'DDGDDF'),
    ('6d24cf954b094a76185334130ce99090d367b0cc46d20f01bc7fd9a58f7287ab', 'DDDDF'),
    ('cf37d74b4f7ab4c3c92ea35491784c6f07018afd285c05d0e7c648c2fec7874c', 'DDDDDDDDF'),
    ('749fe97b1fdcf51f15486d7b36db3ee75d24b47a1154ffe9d11157dee18801e5', 'DDDDFF'),
    ('227e5ee5686b738ad9d435e25e2f3304dd2abf9d70b8e002a2141a44a02984c1', 'DDDDDDDDGDFF'),
    ('91dbb7e2e0dc47e8f9b97fce16765715ae44bc58a5ded36b085cab68472a9efd', 'DDDDGDDDDDDFF'),
    ('77838fbe923eac623bf91fdf6994dba8df263331ce70689c5318ff8e0b8aebde', 'DDDDDDDDDDDDDDDDFF'),
    ('281cfb433ccb903f3aef029d29b0b3f9667aaf619d2cd29f367e95bbc9e2693d', 'DDDDDDFF'),
    ('b96c98aeb2dd83de0c71ec4b5c732e9263a1777420e4dfd1c601dd4b0b1b9c63', 'DDDDDDDGD DDFF'.replace(' ', '')),
    ('998846e4523977c9b7a48a846779e8cda9cc8283df8bc95788ec0926a83593fa', 'DDDGDDDDDDF'),
    ('2f77eba9963eabc8de94c0f87e453eed40adf1910290c4624cef565d3d2ab0e4', 'DDDDGDDDDDDDDDF'),
    ('189dcb28ccf5e210d3f2cee8a1972a93d2a3774993fae01de5529e8759d13a55', 'DDDDDDFF'),
]

TARGETED = [
    ('9a72635e88c223c58fcd04828e9d9c039fab52bb51d78328a5ec50b78f8502a1', 19,
     {'G': [1, 2, 4], 'C': [14, 15, 16, 17], 'F': [13, 18]},
     [(12, 14, 18, 'verification', 'Substitutes both bedroom sizes and recovers total before final answer.')]),
    ('4c330df3fc68938dd9be7fa299bc9be854bbff561ee3c30714f360fe5cf267e8', 15,
     {'J': [0, 5, 12, 13], 'G': [2], 'F': [14]},
     [(4, 5, 6, 'premise_judgment', 'Questions the stated angle total and resumes an altered equation.'),
      (11, 12, 14, 'feasibility_judgment', 'Notices zero angle is impossible but returns zero anyway; incoherent resolution.')]),
    ('a9e0fa3724f961c64f5495b301bbb6bf96448c789ec9d4c270c899080036a1dc', 20,
     {'G': [1, 3], 'C': [17, 18], 'F': [16, 19]},
     [(15, 17, 19, 'verification', 'Checks future ages 26 and 13, then returns answer.')]),
    ('2903847ce7807fccc1d1d9fa1fb3cccfc339bab8263c7e8b664b4c2959492035', 14,
     {'G': [3], 'C': [11, 12], 'F': [10, 13]},
     [(9, 11, 13, 'verification', 'Reconstructs all three ages and checks their sum before answer.')]),
    ('888445fda75008f09909fe674242d42d0f621aa0f9953df76c4c73e696f7f223', 17,
     {'G': [0, 1, 2], 'C': [11, 12, 13, 14], 'F': [15, 16]},
     [(10, 11, 15, 'failed_verification', 'Checks ages but falsely asserts 26 is double 11; still a departure/return, not useful verification.')]),
    ('9a3cfac2b67be989861b1f08c19c18b32db2046aae1618ac419bf98059481cb6', 22,
     {'G': [1, 2, 3, 4, 5], 'C': [15, 16, 17, 18, 19], 'F': [14, 20, 21]},
     [(13, 15, 20, 'verification', 'Reconstructs second bedroom and verifies total before answer.')]),
    ('39a4964c341a1d4389e94289ddb985fc407a6acfcc8c0a3a12ab9eb1fa0a8315', 16,
     {'G': [1, 3], 'C': [13, 14], 'F': [12, 15]},
     [(11, 13, 15, 'verification', 'Checks future ages and returns answer.')]),
    ('fd19acd4b8e7cd8f400471c4db8799df8cd13f435b1b38fce57acedcdba16a51', 22,
     {'G': [1, 2, 3, 4, 5], 'C': [15, 16, 17, 18, 19], 'F': [14, 20, 21]},
     [(13, 15, 20, 'verification', 'Reconstructs second bedroom and verifies total before answer.')]),
    ('b86fec91311deb38a3c291c9edeef1e55d43d54ece150a3746741fc11cf6b54e', 12,
     {'G': [1, 2, 3], 'J': [5, 6, 7, 8, 10], 'F': [11]},
     [(4, 5, 9, 'premise_judgment', 'Questions geometry/premise and returns to a changed-total calculation.'),
      (9, 10, 11, 'premise_judgment', 'Flags impossible premise again then emits answer.')]),
    ('155069419bc39e355c0f2ee1485dfc28d032c54630d713475f4ffe6e4b1f7357', 21,
     {'G': [1, 3], 'C': [17, 18], 'F': [16, 19, 20]},
     [(15, 17, 19, 'verification', 'Checks future ages 26 and 13 before answer.')]),
    ('2881d020998721f0e6418a3c08475c69f2504ac4a332929d141f865c0236c5cc', 18,
     {'G': [0, 1], 'M': [10, 11], 'J': [13, 14, 15], 'F': [16, 17]},
     [(9, 10, 12, 'self_review', 'Questions negative result and re-evaluates setup, then resumes same equation.'),
      (12, 13, 16, 'premise_judgment', 'Loops over interpretation then concludes impossibility, yet emits 4; repetitive and inconsistent.')]),
]


def annotations():
    result = {}
    for text_hash, codes in FIXED:
        result[text_hash] = dict(text_sha256=text_hash, sample='fixed_first4',
            labels=[CATEGORY_CODES[code] for code in codes], worked_methods=1,
            departures_and_returns=[])
    for text_hash, count, overrides, branches in TARGETED:
        labels = ['direct_computation'] * count
        for code, positions in overrides.items():
            for position in positions:
                labels[position] = CATEGORY_CODES[code]
        result[text_hash] = dict(text_sha256=text_hash, sample='marker_selected',
            labels=labels, worked_methods=1,
            departures_and_returns=[{'main': main, 'departure': departure, 'return': resume,
                                    'kind': kind, 'reason': reason,
                                    'return_phase': 'terminal_check_or_aside'
                                    if labels[resume] == 'final_answer' else 'mid_solution'}
                                   for main, departure, resume, kind, reason in branches])
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    with options.output.open('x') as destination:
        json.dump(annotations(), destination, indent=2, sort_keys=True)
        destination.write('\n')
