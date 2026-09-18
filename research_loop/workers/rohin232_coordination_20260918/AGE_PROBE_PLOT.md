# First fixed-token age-probe curves — September 18, 2026

`AGE_PROBE_TOKEN_CURVES.svg` plots the immutable primary `RESULTS.json` from
`../rohin232_age_probe_20260918/`. The source hash is printed on the plot.
Each panel is one independent paired seed: three fresh development cartoons,
1024 actual generated tokens per cartoon, 3072 per panel and6144 per model.
The x-axis includes THINK and ACT tokens. Each step credits a score only
after the complete response's tokens have been charged; there is no linear
interpolation suggesting earlier discovery.

| Frozen condition | New-pixel events, seed23201 | Seed23202 | Sum of independent seed events |
| --- | ---: | ---: | ---: |
| C2 sleep51 | 24 | 16 | 40 |
| C2 sleep87 | 14 | 11 | 25 |
| Plain base | 25 | 33 | 58 |

Current C2 is lower on this provisional metric at both paired seeds. The
diagnostic does not show accumulated improvement on it. These are scoring
events in independent novelty archives, not globally unique ideas or certified
jokes. Nine of200 accepted strings were spot-reviewed as literal caption
attempts; no humor certification or causal H2 result follows. Generated-token
budgets match, but prompt-token counts and total inference compute differ.

The plotter validates both seed budgets, monotone token/event accounting,
unchanged frozen-update counts and agreement with reported totals. Three
synthetic tests and actual-data XML/curve validation pass. Optional PNG preview
was unavailable because the local Cairo system library is absent; no dependency
or environment change was made. The standalone SVG is the deliverable.

Operator-only early story source scans for the separate C2 memory questions
remain under ignored `private/`; no question answers or raw child history are
included in this plot or its input context.
