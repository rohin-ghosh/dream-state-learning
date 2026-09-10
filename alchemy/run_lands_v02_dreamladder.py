"""TASK-FAMILY-SCAFFOLDED DREAM LADDER (not fully generic autonomous
dreaming — it teaches hypothesis->prediction->comparison and the memory
categories; the current ceiling/reference arm). 32B dreamer.

Generic hypothesis->prediction->revision dreaming, producing exactly the
memory kinds the gold-control contract requires:
  RECIPES : from the public workshop calibration lines
  ROLES   : from the animal x land outcome table (entities with the same
            outcome in the same place likely share a latent kind)
  PARENTS : per unresolved combined place — k candidate source sets,
            PREDICT the observed cells under each via pigment addition,
            COMPARE with public experience, retain with uncertainty.
            The two PUBLIC demo lands (known sources) are worked examples.
The public-evidence comparisons are an exact task-family gate in this
identifiable synthetic world.  This condition is therefore permanently a
ceiling/reference diagnostic, not autonomous dreaming.  Hidden parent/role
truth is used only for reporting AFTER corpus commit.  Output:
organism-format corpus arms 'dreamtext'/'dreamlora'
+ full audit (raw dream texts, per-hypothesis predictions, statuses).
Run order (Codex): 1) dreamtext -> 32B thinker; 2) freeze corpus ->
LoRA -> reads -> thinker; 3) replicate only after positives.
"""
from __future__ import annotations
import argparse, json, pathlib, re
from collections import defaultdict

from alchemy.backend import make_backend
from lands.model import WorldConfig
from lands.skins import make_skin
from lands.v02 import SemanticWorldV02, TARGET_LAND_IDS

DREAMER = "Qwen/Qwen2.5-32B-Instruct"
DREAMER_REVISION = "5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd"

RECIPES = """You are dreaming over your memories of a color workshop.
Consolidate them into durable knowledge: for each labeled color, state
exactly what pigment parts it denotes.

WORKSHOP MEMORIES:
{lines}

Output one line per label, exactly like:
RECIPE: <label> denotes <n> part(s) <pigment> [+ <n> part(s) <pigment> ...]
Only include labels the memories support."""

ROLES = """You are dreaming over your lifetime of observations, laid out
as a table (entity: place=outcome). A useful generic principle: entities
that show the SAME outcome in the SAME place likely share a latent kind,
and entities of one kind agree everywhere.

TABLE:
{table}

List EVERY pair the table supports (they agree in at least one shared
place and never disagree in any shared place) — be exhaustive, there are
usually many. Output exactly:
ROLE: In every land, the <entity A> has the same color as the <entity B>.
Check each pair against ALL shared places before writing it."""

PARENTS = """You are dreaming about a combined place whose sources are
unknown. In this world, some places' outcomes are built from other
places' outcomes by pigment addition (a public survey classifies them
together).

WORKED EXAMPLE (public knowledge — this combined place's sources are
known):
{example}

Study how each entity's outcome in the example place equals the pigment
sum of its outcomes in the source places.

NOW THE UNEXPLAINED PLACE: {target}
You know these entities were observed there: {entities}
(You do NOT get to see their outcomes there — you must PREDICT them.)

ROLE HYPOTHESES FROM YOUR EARLIER DREAMS (use these to fill in cells
where an entity was not directly seen):
{roles_block}

Those entities' outcomes in the six ordinary places:
{sources}

Your recipe knowledge:
{recipes}

Propose up to {k} DIFFERENT candidate source sets (2-5 ordinary places
each; make them genuinely different). For EACH candidate, compute the
predicted pigment sum for BOTH entities and name the resulting labels.
Show the arithmetic. End each candidate with one line, exactly:
CANDIDATE: {target} <- <place>, <place>[, <place>...] | predicted: {e1}=<label>, {e2}=<label>"""


def canonical_candidate(line, valid_lands, expected_target,
                        expected_entities):
    """Parse one candidate without repairing malformed model output.

    Parent sets are mathematical sets: unknown names, repeated parents, and
    fewer than two parents invalidate the whole proposal.  Silently deleting
    bad tokens would let malformed lines alias a valid hypothesis.
    """
    norm = re.sub(r"^[\-\*\d\.\)\s]+", "", line.strip())
    norm = norm.replace("**", "").strip()
    if not norm.startswith("CANDIDATE:"):
        return None
    match = re.fullmatch(
        r"CANDIDATE:\s*([\w-]+)\s*<-\s*([^|]+)\|\s*predicted:\s*(.+)",
        norm,
    )
    if not match:
        return None
    target = match.group(1)
    if target != expected_target:
        return None
    raw_parents = [part.strip() for part in match.group(2).split(",")]
    if (not 2 <= len(raw_parents) <= 5
            or any(not part for part in raw_parents)
            or any(part not in valid_lands for part in raw_parents)
            or len(set(raw_parents)) != len(raw_parents)):
        return None
    prediction_parts = [part.strip() for part in match.group(3).split(",")]
    parsed_predictions = []
    for part in prediction_parts:
        prediction = re.fullmatch(r"([\w-]+)\s*=\s*([\w-]+)", part)
        if prediction is None:
            return None
        parsed_predictions.append(
            (prediction.group(1), prediction.group(2).lower())
        )
    names = [name for name, _ in parsed_predictions]
    expected = list(dict.fromkeys(expected_entities))
    if (len(names) != len(set(names))
            or set(names) != set(expected)
            or len(names) != len(expected)):
        return None
    predictions = dict(parsed_predictions)
    return {
        "raw": norm,
        "target": target,
        "parents": list(sorted(raw_parents)),
        "predictions": predictions,
    }


def candidate_lines_with_budget(text, k, sample):
    """Split emitted candidate lines into eligible and overflow records."""
    eligible, overflow = [], []
    emitted_index = 0
    for line in text.splitlines():
        norm = re.sub(r"^[\-\*\d\.\)\s]+", "", line.strip())
        norm = norm.replace("**", "").strip()
        if not norm.startswith("CANDIDATE:"):
            continue
        record = {
            "sample": sample,
            "raw": norm,
            "emitted_index": emitted_index,
        }
        emitted_index += 1
        if len(eligible) < k:
            record["eligible"] = True
            record["eligible_index"] = len(eligible)
            eligible.append(record)
        else:
            record["eligible"] = False
            record["reason"] = "over_candidate_budget"
            overflow.append(record)
    return eligible, overflow


def public_role_check(entity_a, entity_b, public_lands, cells):
    """Check a proposed role pair against every jointly observed public land."""
    shared = [land for land in public_lands
              if (entity_a, land) in cells and (entity_b, land) in cells]
    passed = bool(shared) and all(
        cells[(entity_a, land)] == cells[(entity_b, land)]
        for land in shared
    )
    return shared, passed


def role_discovery_prompt(by_animal, evidence_ids, allowed_lands):
    """Build the target-blind role prompt and its exact evidence ledger.

    Role discovery uses only ordinary source-land observations. Target-land
    cells are reserved for the later blind parent-hypothesis comparison, so a
    target's verification outcomes cannot shape the role proposal frontier.
    """
    allowed = set(allowed_lands)
    table_rows = []
    used_evidence_ids = []
    for animal, memories in sorted(by_animal.items()):
        cells = [
            (land, color) for land, color in sorted(memories.items())
            if land in allowed
        ]
        if not cells:
            continue
        table_rows.append(
            f"{animal}: " + ", ".join(
                f"{land}={color}" for land, color in cells
            )
        )
        for land, _ in cells:
            used_evidence_ids.extend(evidence_ids.get((animal, land), []))
    table = "\n".join(table_rows)
    return ROLES.format(table=table), sorted(set(used_evidence_ids))


def observation_evidence_records(land, observed, evidence_ids):
    """Materialize the exact public records used by an outcome comparison."""
    records = []
    for entity, token in sorted(observed):
        for evidence_id in sorted(evidence_ids.get((entity, land), [])):
            records.append({
                "evidence_id": evidence_id,
                "entity": entity,
                "land": land,
                "observed_token": token.lower(),
            })
    return records


def _unique_records(records):
    unique = []
    seen = set()
    for record in records:
        key = tuple(record["parents"])
        if key not in seen:
            seen.add(key)
            unique.append(record)
    return unique


def parent_prefix_snapshot(scored, sample_limit):
    """Return exact proposal/accounting state through ``sample_limit``.

    Retention is append-only.  Before any supported hypothesis exists, the
    first provisional may be retained as an explicitly contradicted fallback.
    It remains inspectable if a different supported claim later appears; if
    the same parent set later becomes supported, its status is upgraded.
    """
    eligible = [
        record for record in scored if record["sample"] <= sample_limit
    ]
    proposals = _unique_records(eligible)
    supported = _unique_records([
        record for record in eligible
        if record["hits"] == record["n_obs"]
    ])
    provisional = _unique_records([
        record for record in eligible
        if record["hits"] == record["n_obs"] - 1
    ])

    retained = {}
    supported_seen = False
    fallback_chosen = False
    for sample_index in range(sample_limit + 1):
        current = [r for r in eligible if r["sample"] == sample_index]
        current_supported = _unique_records([
            r for r in current if r["hits"] == r["n_obs"]
        ])
        for record in current_supported:
            key = tuple(record["parents"])
            if key in retained:
                first_retained = retained[key]["first_retained_sample"]
                retained[key] = {
                    **record,
                    "status": "supported",
                    "first_retained_sample": first_retained,
                    "supported_sample": sample_index,
                }
            else:
                retained[key] = {
                    **record,
                    "status": "supported",
                    "first_retained_sample": sample_index,
                    "supported_sample": sample_index,
                }
        if current_supported:
            supported_seen = True
        if not supported_seen and not fallback_chosen:
            current_provisional = _unique_records([
                r for r in current if r["hits"] == r["n_obs"] - 1
            ])
            if current_provisional:
                record = current_provisional[0]
                key = tuple(record["parents"])
                retained[key] = {
                    **record,
                    "status": "contradicted",
                    "retention_reason": "legacy_fallback_before_support",
                    "first_retained_sample": sample_index,
                }
                fallback_chosen = True
    return {
        "proposals": proposals,
        "supported": supported,
        "provisional": provisional,
        "retained": list(retained.values()),
    }


def canonical_surface_role_truth(world, skin_obj):
    """Offline-only canonical role pairs for reporting/tests."""
    truth = set()
    roles = world.base.animal_roles
    for x in world.animal_ids:
        for y in world.animal_ids:
            if x < y and roles[x] == roles[y]:
                truth.add(tuple(sorted(
                    (skin_obj.animal(x), skin_obj.animal(y))
                )))
    return truth


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skin", default="aligned")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument(
        "--samples",
        type=int,
        default=1,
        help=("independent dream samples per role/parent stage; accepted "
              "claims are unioned and cumulative precision/recall is reported"),
    )
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--sample-seed", type=int, default=28001)
    a = ap.parse_args()
    if a.samples < 1:
        ap.error("--samples must be >= 1")
    if a.samples > 1 and a.temperature <= 0:
        ap.error("multi-sample runs require --temperature > 0")
    world = SemanticWorldV02(WorldConfig(seed=a.seed))
    skin_obj = make_skin(a.skin, world.animal_ids, world.source_land_ids)
    rows = list(world.render_lifetime(a.skin))
    goals = world.render_goals(a.skin)
    animals = [skin_obj.animal(x) for x in world.animal_ids]
    lands = [skin_obj.land(l) for l in world.source_land_ids]
    joined = "\n".join(rows)

    # surface names for targets and demos, by first mention
    tgt_surfaces = []
    for g in goals:
        m = re.match(r"In ([^,]+),", g["question"])
        if m and m.group(1) not in tgt_surfaces:
            tgt_surfaces.append(m.group(1))
    order = sorted((joined.find(s), s) for s in tgt_surfaces)
    tgt_by_id = dict(zip(TARGET_LAND_IDS[:len(tgt_surfaces)],
                         [s for _, s in order]))
    # demo lands: find their surface names from rows mentioning them —
    # demos are non-source, non-target lands appearing in the lifetime
    known_surf = set(lands) | set(tgt_surfaces)
    cand_names = set()
    for r in rows:
        for m in re.finditer(r"visit to(?: zone)? ([A-Z][\w-]+)", r):
            cand_names.add(m.group(1))
    demo_surfaces = sorted(cand_names - known_surf,
                           key=lambda s: joined.find(s))
    demo_ids = sorted(world.demo_parents)
    demo_by_id = dict(zip(demo_ids, demo_surfaces))
    print(f"[dl] demos: { {k: (demo_by_id.get(k), [skin_obj.land(p) for p in v]) for k, v in world.demo_parents.items()} }",
          flush=True)

    # tabulated episodic (organized memory, disclosed)
    cell = {}
    cell_evidence_ids = defaultdict(list)
    for r in rows:
        m = re.search(r"visit to(?: zone)? ([\w-]+), (?:you see the (\w+)\. "
                      r"Its coat is ([\w-]+)|entity (\w+) has state-token "
                      r"([\w-]+))", r)
        if m:
            land, an, col = m.group(1), m.group(2) or m.group(4), \
                (m.group(3) or m.group(5)).rstrip(".")
            cell[(an, land)] = col
            evidence_id = re.match(r"\[([^|\]]+)", r)
            if evidence_id:
                cell_evidence_ids[(an, land)].append(
                    evidence_id.group(1).strip()
                )
    by_animal = defaultdict(dict)
    for (an, land), col in cell.items():
        by_animal[an][land] = col

    be = make_backend("vllm", DREAMER, revision=DREAMER_REVISION,
                      enable_lora=True, max_lora_rank=64)
    audit = {"raw": [], "sampling": {
        "samples": a.samples,
        "temperature": a.temperature,
        "base_seed": a.sample_seed,
        "model": DREAMER,
        "model_revision": DREAMER_REVISION,
    }, "condition": {
        "id": "task_family_scaffolded_public_evidence_exact_gate_ceiling",
        "headline_eligible": False,
        "task_family_scaffold": True,
        "public_evidence_exact_gate": True,
        "contradicted_fallback_retention": "legacy_ablation_only",
        "offline_truth_in_cognition": False,
    }}

    def record_generation(stage, prompt, text, seed=None, **metadata):
        usage = be.last_usage[0]
        audit["raw"].append({
            "stage": stage,
            "seed": seed,
            "prompt_tokens": usage["prompt_tokens"],
            "output_tokens": usage["output_tokens"],
            "original_prompt_tokens": usage["original_prompt_tokens"],
            "prompt_truncated": usage["prompt_truncated"],
            "token_count_source": usage["source"],
            "text": text,
            **metadata,
        })

    # ---- 1. RECIPES ----
    workshop = [r for r in rows if "mixture" in r.lower()
                or "labeled" in r.lower()]
    recipe_prompt = RECIPES.format(lines="\n".join(workshop))
    out = be.generate([recipe_prompt], max_tokens=1200)[0]
    record_generation("recipes", recipe_prompt, out)
    recipes = [l.strip() for l in out.splitlines()
               if l.strip().startswith("RECIPE:")]
    print(f"[dl] recipes: {len(recipes)}", flush=True)

    # ---- 2. ROLES ----
    role_prompt, role_evidence_ids = role_discovery_prompt(
        by_animal, cell_evidence_ids, lands
    )
    audit["role_discovery_evidence"] = {
        "policy": "ordinary_source_lands_only",
        "allowed_lands": list(lands),
        "allowed_evidence_ids": role_evidence_ids,
        "excluded_target_lands": sorted(tgt_surfaces),
        "excluded_target_evidence_ids": sorted({
            evidence_id
            for (entity, land), ids in cell_evidence_ids.items()
            if land in set(tgt_surfaces)
            for evidence_id in ids
        }),
    }
    audit["compute"] = {
        "k_per_target_per_sample": a.k,
        "samples": a.samples,
        "candidate_ceiling_per_target": a.k * a.samples,
        "matched_compute_to_v4": False,
    }
    roles, n_prop, n_rej = [], 0, 0
    role_proposals = []
    role_seen, role_accept_sample, roles_by_prefix = set(), {}, []
    for sample_index in range(a.samples):
        sample_seed = a.sample_seed + sample_index
        out = be.generate(
            [role_prompt], max_tokens=2500,
            temperature=a.temperature, seed=sample_seed,
        )[0]
        record_generation(f"roles:s{sample_index}", role_prompt, out,
                          seed=sample_seed,
                          evidence_policy="ordinary_source_lands_only",
                          allowed_evidence_ids=role_evidence_ids)
        for l in out.splitlines():
            l = re.sub(r"^[\-\*\d\.\)\s]+", "", l.strip()).replace("**", "")
            if not l.startswith("ROLE:"):
                continue
            n_prop += 1
            m2 = re.search(r"the ([\w-]+) has the same color as the ([\w-]+)", l)
            if not m2:
                role_proposals.append({"sample": sample_index, "raw": l,
                                       "parsed": False,
                                       "public_check": None})
                continue
            x, y = sorted((m2.group(1), m2.group(2)))
            # HARNESS check vs PUBLIC cells: agree in every shared land.
            # This is evidence filtering, not proof of universal equivalence;
            # offline role precision below measures accidental agreements.
            shared, passed = public_role_check(x, y, lands, cell)
            role_proposals.append({
                "sample": sample_index,
                "raw": l,
                "parsed": True,
                "pair": [x, y],
                "shared_public_places": shared,
                "public_check": passed,
            })
            if passed and (x, y) not in role_seen:
                role_seen.add((x, y))
                role_accept_sample[(x, y)] = sample_index
                roles.append(f"In every land, the {x} has the same color as "
                             f"the {y}.")
            elif not passed:
                n_rej += 1
        roles_by_prefix.append(list(roles))
    print(f"[dl] roles: {n_prop} proposed, {n_rej} rejected by public "
          f"agreement check, {len(roles)} kept", flush=True)

    # ---- 3. PARENTS per target, demo as worked example ----
    ex_id = demo_ids[0]
    ex_surf = demo_by_id.get(ex_id, demo_surfaces[0] if demo_surfaces else "?")
    ex_parents = [skin_obj.land(p) for p in world.demo_parents[ex_id]]
    ex_rows = [f"{an} in {ex_surf}: {col}" + " | sources: "
               + ", ".join(f"{p}={by_animal[an].get(p, '?')}"
                           for p in ex_parents)
               for (an, land), col in sorted(cell.items()) if land == ex_surf]
    example = (f"{ex_surf} is publicly known to be fed by "
               f"{' and '.join(ex_parents)}.\n" + "\n".join(ex_rows))
    parent_lines, hyp_audit = [], []
    for target_index, (tid, tsurf) in enumerate(tgt_by_id.items()):
        observed = [(an, col) for (an, land), col in cell.items()
                    if land == tsurf]
        blind_comparison_evidence = observation_evidence_records(
            tsurf, observed, cell_evidence_ids
        )
        ents = [an for an, _ in observed]
        src_txt = "\n".join(
            f"{an}: " + ", ".join(f"{l}={by_animal[an].get(l, '(not seen; use roles)')}"
                                  for l in lands)
            for an in ents)
        raw_candidates = []
        overflow_candidates = []
        malformed_candidates = []
        scored = []
        for sample_index in range(a.samples):
            sample_seed = (a.sample_seed + 10_000
                           + target_index * a.samples + sample_index)
            prompt = PARENTS.format(
                example=example, target=tsurf, entities=", ".join(ents),
                sources=src_txt,
                roles_block="\n".join(roles_by_prefix[sample_index]) or "(none)",
                recipes="\n".join(recipes), k=a.k, e1=ents[0],
                e2=ents[1] if len(ents) > 1 else ents[0],
            )
            out = be.generate(
                [prompt], max_tokens=2800, temperature=a.temperature,
                seed=sample_seed,
            )[0]
            record_generation(
                f"parents:{tsurf}:s{sample_index}", prompt, out,
                seed=sample_seed,
                role_prefix_size=len(roles_by_prefix[sample_index]),
            )
            eligible, overflow = candidate_lines_with_budget(
                out, a.k, sample_index
            )
            raw_candidates.extend(eligible)
            overflow_candidates.extend(overflow)
            for raw_record in eligible:
                parsed = canonical_candidate(
                    raw_record["raw"], lands, tsurf, ents
                )
                if parsed is None:
                    malformed_candidates.append(raw_record)
                    continue
                obs_map = {an: col.lower() for an, col in observed}
                hits = sum(
                    1 for an, col in obs_map.items()
                    if parsed["predictions"].get(an, "") == col
                )
                scored.append({
                    **parsed,
                    "sample": sample_index,
                    "hits": hits,
                    "n_obs": len(obs_map),
                })
        # HARNESS comparison of BLIND predictions vs PUBLIC observations
        # (mechanical exact gate against public data; ceiling condition)
        snapshot = parent_prefix_snapshot(scored, a.samples - 1)
        sup = snapshot["supported"]
        keep = snapshot["retained"]
        hyp_audit.append({
            "target": tsurf,
            "blind_comparison_evidence": blind_comparison_evidence,
            "raw_candidates": raw_candidates,
            "overflow_candidates": overflow_candidates,
            "malformed_candidates": malformed_candidates,
            "scored": scored,
            "retained": keep,
        })
        for x in keep:
            ps = x["parents"]
            tag = ("" if x["status"] == "supported" else
                   " (fallback — contradicted by one public observation)")
            parent_lines.append(
                f"{tsurf}'s outcomes are built from "
                f"{', '.join(ps[:-1])} and {ps[-1]} combined.{tag}")
        print(f"[dl] {tsurf}: {len(raw_candidates)} eligible candidates + "
              f"{len(overflow_candidates)} overflow across {a.samples} samples, "
              f"{len(sup)} blind-supported, kept {len(keep)}", flush=True)

    # ---- consolidate corpus (organism format) ----
    principle = ("In this world, an animal's color in a combined land is "
                 "the paint-pigment mixture of that animal's colors in the "
                 "lands that feed that combined land (amounts add).")
    recipe_stmts = [l.replace("RECIPE:", "The color").replace(" denotes ",
                    " denotes a pigment mixture of ", 1)
                    if False else l[7:].strip() for l in recipes]
    statements = parent_lines + roles + recipe_stmts + [principle]
    episodic = [r.split("] ", 1)[1] if "] " in r else r for r in rows]

    def qa_forms(stmts):
        outl = []
        ents = animals + lands + list(tgt_by_id.values())
        for s in stmts:
            es = [e for e in ents if e in s][:2]
            key = " and ".join(es) if es else "this world"
            outl.append(f"Q: What did you conclude about {key}? A: {s}")
            outl.append(s)
        return outl

    path = f"alchemy/v2_out/organism_corpus_{a.skin}_s{a.seed}.json"
    corpus = {
        "schema_version": 1,
        "source": "run_lands_v02_dreamladder",
        "skin": a.skin,
        "seed": a.seed,
        "condition": audit["condition"],
        "dreamtext": statements + episodic,
        "dreamlora": qa_forms(statements) + episodic,
    }
    json.dump(corpus, open(path, "w"), indent=1)

    # ---- offline reporting ONLY ----
    truth = {tgt_by_id[t]: sorted(skin_obj.land(p)
                                  for p in world.target_parents[t])
             for t in tgt_by_id}
    roles_truth = canonical_surface_role_truth(world, skin_obj)
    sample_curve = []

    def claim_view(record, status=None):
        value = {
            "parents": record["parents"],
            "first_sample": record["sample"],
            "hits": record["hits"],
            "n_public_observations": record["n_obs"],
        }
        if status is not None:
            value["status"] = status
        if "first_retained_sample" in record:
            value["first_retained_sample"] = record["first_retained_sample"]
        if "supported_sample" in record:
            value["supported_sample"] = record["supported_sample"]
        if "retention_reason" in record:
            value["retention_reason"] = record["retention_reason"]
        return value

    for sample_limit in range(a.samples):
        parent_totals = {
            "raw_lines_total": 0,
            "overflow_lines_total": 0,
            "emitted_candidate_lines_total": 0,
            "parsed_total": 0,
            "malformed_total": 0,
            "unique_proposed_total": 0,
            "unique_proposed_true": 0,
            "targets_with_true_proposed": 0,
            "supported_total": 0,
            "supported_true": 0,
            "one_mismatch_total": 0,
            "one_mismatch_true": 0,
            "retained_total": 0,
            "retained_true": 0,
            "by_target": [],
        }
        for rec in hyp_audit:
            truth_key = tuple(truth.get(rec["target"], []))
            raw = [x for x in rec["raw_candidates"]
                   if x["sample"] <= sample_limit]
            malformed = [x for x in rec["malformed_candidates"]
                         if x["sample"] <= sample_limit]
            overflow = [x for x in rec["overflow_candidates"]
                        if x["sample"] <= sample_limit]
            snapshot = parent_prefix_snapshot(rec["scored"], sample_limit)
            proposed_keys = {tuple(x["parents"]) for x in snapshot["proposals"]}
            supported_keys = {tuple(x["parents"]) for x in snapshot["supported"]}
            mismatch_keys = {tuple(x["parents"]) for x in snapshot["provisional"]}
            retained_keys = {tuple(x["parents"]) for x in snapshot["retained"]}
            exact = {
                "target": rec["target"],
                "truth": list(truth_key),
                "raw_lines": len(raw),
                "overflow_lines": len(overflow),
                "emitted_candidate_lines": len(raw) + len(overflow),
                "parsed": len([x for x in rec["scored"]
                               if x["sample"] <= sample_limit]),
                "malformed": len(malformed),
                "proposed": [claim_view(x) for x in snapshot["proposals"]],
                "supported": [claim_view(x, "supported")
                              for x in snapshot["supported"]],
                "one_mismatch": [claim_view(x, "contradicted")
                                 for x in snapshot["provisional"]],
                "retained": [claim_view(x, x["status"])
                             for x in snapshot["retained"]],
            }
            parent_totals["by_target"].append(exact)
            parent_totals["raw_lines_total"] += len(raw)
            parent_totals["overflow_lines_total"] += len(overflow)
            parent_totals["emitted_candidate_lines_total"] += (
                len(raw) + len(overflow)
            )
            parent_totals["parsed_total"] += exact["parsed"]
            parent_totals["malformed_total"] += len(malformed)
            parent_totals["unique_proposed_total"] += len(proposed_keys)
            parent_totals["unique_proposed_true"] += truth_key in proposed_keys
            parent_totals["targets_with_true_proposed"] += truth_key in proposed_keys
            parent_totals["supported_total"] += len(supported_keys)
            parent_totals["supported_true"] += truth_key in supported_keys
            parent_totals["one_mismatch_total"] += len(mismatch_keys)
            parent_totals["one_mismatch_true"] += truth_key in mismatch_keys
            parent_totals["retained_total"] += len(retained_keys)
            parent_totals["retained_true"] += truth_key in retained_keys

        eligible_roles = [r for r in role_proposals
                          if r["sample"] <= sample_limit]
        parsed_role_pairs = {
            tuple(r["pair"]) for r in eligible_roles if r["parsed"]
        }
        accepted_role_pairs = {
            tuple(r["pair"]) for r in eligible_roles
            if r["parsed"] and r["public_check"]
        }
        role_report = {
            "raw_lines_total": len(eligible_roles),
            "parsed_total": sum(r["parsed"] for r in eligible_roles),
            "malformed_total": sum(not r["parsed"] for r in eligible_roles),
            "unique_proposed_total": len(parsed_role_pairs),
            "unique_proposed_true": sum(p in roles_truth
                                        for p in parsed_role_pairs),
            "accepted_total": len(accepted_role_pairs),
            "accepted_true": sum(p in roles_truth
                                 for p in accepted_role_pairs),
            "accepted": [list(p) for p in sorted(accepted_role_pairs)],
        }
        included_generation = [
            item for item in audit["raw"]
            if item["stage"] == "recipes"
            or (item["stage"].startswith("roles:s")
                and int(item["stage"].split(":s")[-1]) <= sample_limit)
            or (item["stage"].startswith("parents:")
                and int(item["stage"].rsplit(":s", 1)[-1]) <= sample_limit)
        ]
        sample_curve.append({
            "samples": sample_limit + 1,
            "parents": parent_totals,
            "roles": role_report,
            "budget": {
                "k_per_target_per_sample": a.k,
                "candidate_ceiling_per_target": a.k * (sample_limit + 1),
                "matched_compute_to_v4": False,
                "requested_parent_candidates_max": (
                    len(hyp_audit) * (sample_limit + 1) * a.k
                ),
                "actual_parent_candidate_lines": parent_totals["raw_lines_total"],
                "eligible_parent_candidate_lines": parent_totals["raw_lines_total"],
                "overflow_parent_candidate_lines": parent_totals["overflow_lines_total"],
                "emitted_parent_candidate_lines": (
                    parent_totals["emitted_candidate_lines_total"]
                ),
                "generation_calls": len(included_generation),
                "prompt_tokens": sum(x["prompt_tokens"]
                                     for x in included_generation),
                "output_tokens": sum(x["output_tokens"]
                                     for x in included_generation),
            },
        })
    final = sample_curve[-1]
    cand_recall = final["parents"]["targets_with_true_proposed"]
    sup_true = final["parents"]["supported_true"]
    sup_n = final["parents"]["supported_total"]
    retained_true = final["parents"]["retained_true"]
    retained_total = final["parents"]["retained_total"]
    role_true = final["roles"]["accepted_true"]
    role_n = final["roles"]["accepted_total"]
    role_prec = role_true / role_n if role_n else None
    role_rec = role_true / len(roles_truth) if roles_truth else None
    print(f"[dl] METRICS candidate-recall {cand_recall}/{len(truth)} | "
          f"supported-precision {sup_true}/{sup_n} | role P/R "
          f"{role_prec}/{role_rec}", flush=True)
    json.dump({"condition": audit["condition"],
               "compute": audit["compute"],
               "statements": statements, "hypotheses": hyp_audit,
               "roles": {"proposals": role_proposals,
                         "retained": roles},
               "audit": audit, "samples": a.samples,
               "sample_curve": sample_curve,
               "retained_truth_presence": f"{retained_true}/{len(truth)}",
               "retained_true": retained_true,
               "retained_total": retained_total,
               "candidate_recall": cand_recall,
               "supported_precision": f"{sup_true}/{sup_n}",
               "role_precision": role_prec, "role_recall": role_rec},
              open(f"alchemy/v2_out/dreamladder_{a.skin}_s{a.seed}.json",
                   "w"), indent=1)
    print(f"[dl] statements={len(statements)} "
          f"(parents {len(parent_lines)}, roles {len(roles)}, "
          f"recipes {len(recipe_stmts)}) | retained truth-presence "
          f"{retained_true}/{len(truth)} targets; retained claims "
          f"{retained_true}/{retained_total}", flush=True)
    print("[dl] DONE", flush=True)


if __name__ == "__main__":
    main()
