# Second offline inspection serialization failure — 2026-09-13 13:53 UTC

Inspector revision0d301d45 completed raw replay and lineage validation but
failed while serializing the result: native.canonical rejects Counter objects
because its finite JSON policy accepts only exact builtin types. The output
directory inspection_v2 contains a preserved empty inspection.json. No table
was printed/read; no original evidence, model call or collection was changed.

Main normalizes aggregate Counter values to ordinary dicts at replay_rows's
return boundary and adds a strict-canonical roundtrip assertion to the actual
partial replay counter test. Counts and scoring are unchanged. This is output
serialization repair, not an outcome-driven analysis change. Original frozen
finalized analyzer is not used or modified. A new output directory inspection_v3
will preserve both failed offline attempts; no numerical experiment repeats.
