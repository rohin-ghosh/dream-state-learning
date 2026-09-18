"""Bounded public metadata/source audit; never load weights or dataset records."""

import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[3]
GITHUB_REVISION = "7cb2419529c556fab06bf6584645d37ccaa36fc1"
REWARD_BASE_ID = "weqweasdas/RM-Mistral-7B"
REWARD_BASE_REVISION = "70e252672fdd640083505e2ca1da8547e0e6d478"
UPSTREAM_ID = "mistralai/Mistral-7B-Instruct-v0.2"
UPSTREAM_REVISION = "63a8b081895390a26e140280378bc85ec8bce07a"
PAPER_URL = "https://[REDACTED_HOST]/html/2406.10522v2"
ARTIFACTS = []
PENDING = {}
FETCHES = {}


def digest(content):
    return hashlib.sha256(content).hexdigest()


def fetch(url):
    if url in FETCHES:
        return FETCHES[url]
    parsed = urllib.parse.urlparse(url)
    allowed = (
        parsed.netloc == "arxiv.org"
        and parsed.path in {"/abs/2406.10522v2", "/html/2406.10522v2"}
    ) or (
        parsed.netloc == "api.github.com"
        and parsed.path.startswith("/repos/yguooo/cartoon-caption-generation")
    ) or (
        parsed.netloc == "raw.githubusercontent.com"
        and parsed.path.startswith(
            f"/yguooo/cartoon-caption-generation/{GITHUB_REVISION}/"
        )
        and "/examples/" not in parsed.path
    ) or (
        parsed.netloc == "huggingface.co"
        and (
            parsed.path.startswith("/api/models")
            or (
                parsed.path.startswith(
                    f"/{REWARD_BASE_ID}/resolve/{REWARD_BASE_REVISION}/"
                )
                and parsed.path.rsplit("/", 1)[-1]
                in {
                    "README.md", "config.json", "tokenizer_config.json",
                    "special_tokens_map.json", "added_tokens.json",
                    "model.safetensors.index.json",
                }
            )
        )
    )
    if parsed.scheme != "https" or not allowed:
        raise ValueError(f"Out-of-scope request: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "metadata-only-audit"})
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError("Metadata response exceeds the bounded size limit")
        record = {
            "requested_url": url,
            "resolved_url": response.url,
            "fetched_utc": datetime.now(timezone.utc).isoformat(),
            "http_status": response.status,
            "response_bytes": len(body),
            "response_sha256": digest(body),
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
        }
    FETCHES[url] = body, record
    return body, record


def json_text(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def artifact(path, text, sources, extraction, expected_git_blob=None):
    encoded = (text if text.endswith("\n") else text + "\n").encode("utf-8")
    if path in PENDING:
        raise ValueError(f"Duplicate artifact: {path}")
    PENDING[path] = encoded
    source_records = [dict(fetch(url)[1]) for url in sources]
    if expected_git_blob is not None:
        body = fetch(sources[0])[0]
        actual = hashlib.sha1(f"blob {len(body)}\0".encode() + body).hexdigest()
        if actual != expected_git_blob:
            raise ValueError(f"Git blob mismatch: {path}")
        source_records[0]["verified_git_blob_sha1"] = actual
    ARTIFACTS.append({
        "path": path,
        "artifact_bytes": len(encoded),
        "artifact_sha256": digest(encoded),
        "extraction": extraction,
        "sources": source_records,
    })


def line_excerpt(text, ranges):
    lines = text.splitlines(keepends=True)
    return "\n".join(
        f"SOURCE LINES {start}-{stop}\n" + "".join(lines[start - 1:stop])
        for start, stop in ranges
    )


def metadata_projection(metadata):
    keys = [
        "id", "sha", "author", "private", "gated", "disabled",
        "library_name", "pipeline_tag", "createdAt", "lastModified",
        "tags", "config", "safetensors", "siblings", "transformersInfo",
    ]
    result = {key: metadata[key] for key in keys if key in metadata}
    card = metadata.get("cardData", {})
    result["cardData_allowed_fields"] = {
        key: card[key] for key in ["license", "base_model", "library_name"]
        if key in card
    }
    result["omissions"] = "All widgets, examples, model-index, spaces and other fields omitted."
    return result


github_api = "https://[REDACTED_HOST]/repos/yguooo/cartoon-caption-generation"
tree_url = github_api + f"/git/trees/{GITHUB_REVISION}?recursive=1"
tree = json.loads(fetch(tree_url)[0])
assert not tree.get("truncated")
tree_entries = {entry["path"]: entry for entry in tree["tree"]}
repository = json.loads(fetch(github_api)[0])
commit_url = github_api + f"/commits/{GITHUB_REVISION}"
commit = json.loads(fetch(commit_url)[0])
artifact("evidence/github/repository.metadata.json", json_text({
    "repository": {key: repository.get(key) for key in [
        "full_name", "html_url", "default_branch", "license", "archived"
    ]},
    "commit": {"sha": commit["sha"], "committed": commit["commit"]["committer"]["date"]},
    "tree_truncated": tree["truncated"],
    "selected_tree_entries": [entry for path, entry in tree_entries.items()
        if path in {"README.md", "LICENSE"} or path.startswith("finetuning/")],
    "scope": "Filename metadata only; no examples directory or data files retrieved.",
}), [github_api, commit_url, tree_url], "Allowlisted repository, commit and source-filename metadata")
raw_base = f"https://[REDACTED_HOST]/yguooo/cartoon-caption-generation/{GITHUB_REVISION}/"
for path in ["LICENSE", "finetuning/humor_reward_modeling.py", "finetuning/custom_trainer.py"]:
    url = raw_base + path
    artifact("evidence/github/" + path.rsplit("/", 1)[-1] + ".txt",
             fetch(url)[0].decode(), [url], "Full source; terminal LF normalized only if absent",
             tree_entries[path]["sha"])
readme_url = raw_base + "README.md"
readme = fetch(readme_url)[0].decode()
reward_section = readme[readme.index("### Reward Modeling"):readme.index("### PPO")]
release_section = readme[readme.index("## Download Checkpoints"):readme.index("You can also see our sample")]
artifact("evidence/github/README.reward_release.excerpts.md", reward_section + release_section,
         [readme_url], "Only Reward Modeling and checkpoint-release introduction; examples section excluded",
         tree_entries["README.md"]["sha"])
for filename, ranges in [
    ("preprocess.py", [(52, 80), (173, 179)]),
    ("save_bon_results.py", [(12, 30), (44, 58)]),
    ("humor_ppo.py", [(139, 150), (170, 178)]),
]:
    url = raw_base + "finetuning/" + filename
    source = fetch(url)[0].decode()
    ast.parse(source)
    artifact("evidence/github/" + filename + ".excerpts.txt", line_excerpt(source, ranges),
             [url], {"original_line_ranges": ranges, "source_not_executed": True},
             tree_entries["finetuning/" + filename]["sha"])

abstract_url = "https://[REDACTED_HOST]/abs/2406.10522v2"
abstract = BeautifulSoup(fetch(abstract_url)[0], "html.parser")
citation = {"citation_author": []}
for node in abstract.select('meta[name^="citation_"]'):
    name = node.get("name")
    if name == "citation_author":
        citation[name].append(node.get("content"))
    elif name in {"citation_title", "citation_date", "citation_pdf_url", "citation_arxiv_id"}:
        citation[name] = node.get("content")
history = abstract.select_one(".submission-history")
citation["submission_history"] = history.get_text(" ", strip=True) if history else None
citation["selected_version"] = "2406.10522v2"
artifact("evidence/arxiv/version.metadata.json", json_text(citation), [abstract_url],
         "Citation meta tags and submission-history text only; no PDF retrieved")
paper = BeautifulSoup(fetch(PAPER_URL)[0], "html.parser")
paragraph_ids = ["S3.p1", "S3.p3", "S4.SS3.p3", "S4.SS3.p6", "A3.SS3.p1", "A3.SS3.p2", "A3.SS3.p3"]
paragraphs = []
for identifier in paragraph_ids:
    paragraph = paper.find(id=identifier)
    if paragraph is None:
        raise ValueError(f"Missing allowlisted methodological paragraph {identifier}")
    for excluded in paragraph.select("figure, table, img, .ltx_note, math"):
        excluded.decompose()
    paragraphs.append(identifier + "\n" + paragraph.get_text(" ", strip=True))
resource_links = sorted({node.get("href") for node in paper.find_all("a", href=True)
    if node.get("href", "").startswith(("https://[REDACTED_HOST]/", "https://[REDACTED_HOST]/yguooo/"))})
artifact("evidence/arxiv/methods.aggregate_excerpts.txt", "\n\n".join(paragraphs), [PAPER_URL],
         {"paragraph_ids": paragraph_ids, "excluded": "figures/tables/images/notes/math; all other paragraphs incl. prompt/examples appendices"})
artifact("evidence/arxiv/resource_urls.json", json_text(resource_links), [PAPER_URL],
         "Href strings only; dataset, viewer, image, Drive and example URLs were not followed")

search_queries = [
    "author=yguooo&full=true&config=true&limit=100",
    "author=jifanz&full=true&limit=100",
    "filter=arxiv:2406.10522&full=true&limit=100",
    "search=newyorker&full=true&limit=100",
    "search=new-yorker&full=true&limit=100",
    "search=humor_reward&full=true&limit=100",
]
discovery = []
search_urls = []
for query in search_queries:
    url = "https://[REDACTED_HOST]/api/models?" + query
    search_urls.append(url)
    models = json.loads(fetch(url)[0])
    discovery.append({"query": query, "returned_count": len(models), "limit": 100,
        "models": [{"id": model["id"], "sha": model.get("sha"),
            "base_model_tags": [tag for tag in model.get("tags", []) if tag.startswith("base_model:")]
        } for model in models]})
artifact("evidence/hf/discovery.metadata.json", json_text(discovery), search_urls,
         "Model IDs/revisions/base-model tags only; bounded discovery is not proof of global nonexistence")

reward_url = f"https://[REDACTED_HOST]/api/models/{REWARD_BASE_ID}/revision/{REWARD_BASE_REVISION}?blobs=true"
reward_metadata = json.loads(fetch(reward_url)[0])
assert reward_metadata["sha"] == REWARD_BASE_REVISION
artifact("evidence/hf/rm_mistral_7b/model.metadata.json", json_text(metadata_projection(reward_metadata)),
         [reward_url], "Model metadata projection; LFS hashes/sizes advertised by server, not independently hashed weights")
siblings = {entry["rfilename"]: entry for entry in reward_metadata["siblings"]}
resolve_base = f"https://[REDACTED_HOST]/{REWARD_BASE_ID}/resolve/{REWARD_BASE_REVISION}/"
for filename in ["config.json", "tokenizer_config.json", "special_tokens_map.json", "added_tokens.json", "model.safetensors.index.json"]:
    url = resolve_base + filename
    source = fetch(url)[0].decode()
    json.loads(source)
    artifact("evidence/hf/rm_mistral_7b/" + filename, source, [url],
             "Full metadata/config JSON; terminal LF normalized only if absent", siblings[filename]["blobId"])
reward_card_url = resolve_base + "README.md"
reward_card = fetch(reward_card_url)[0].decode()
artifact("evidence/hf/rm_mistral_7b/README.provenance.excerpt.md", reward_card[:reward_card.index("## Uses")],
         [reward_card_url], "Only provenance/training documentation before Uses; usage examples excluded", siblings["README.md"]["blobId"])
upstream_url = f"https://[REDACTED_HOST]/api/models/{UPSTREAM_ID}/revision/{UPSTREAM_REVISION}"
upstream = json.loads(fetch(upstream_url)[0])
assert upstream["sha"] == UPSTREAM_REVISION
artifact("evidence/hf/mistral_instruct_v0_2.metadata.json", json_text({
    key: value for key, value in metadata_projection(upstream).items() if key != "siblings"
}), [upstream_url], "Underlying base-model provenance/license metadata; widget and examples omitted")

environment_keys = ["HF_HOME", "HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "TRANSFORMERS_CACHE", "XDG_CACHE_HOME"]
cache_environment = {key: os.environ[key] for key in environment_keys if os.environ.get(key)}
cache_roots = {Path.home() / ".cache/huggingface/hub"}
if os.environ.get("XDG_CACHE_HOME"):
    cache_roots.add(Path(os.environ["XDG_CACHE_HOME"]) / "huggingface/hub")
if os.environ.get("HF_HOME"):
    cache_roots.add(Path(os.environ["HF_HOME"]) / "hub")
for key in ["HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "TRANSFORMERS_CACHE"]:
    if os.environ.get(key):
        cache_roots.add(Path(os.environ[key]))
cache_results = []
for cache_root in sorted(cache_roots):
    for model_id, revision in [(REWARD_BASE_ID, REWARD_BASE_REVISION), (UPSTREAM_ID, UPSTREAM_REVISION)]:
        snapshot = cache_root / ("models--" + model_id.replace("/", "--")) / "snapshots" / revision
        exists = snapshot.is_dir()
        filenames = sorted(entry.name for entry in os.scandir(snapshot)) if exists else []
        cache_results.append({"model_id": model_id, "revision": revision,
            "snapshot_path": str(snapshot), "snapshot_directory_present": exists,
            "filenames_only": filenames})
artifact("evidence/local_cache_filename_check.json", json_text({
    "checked_utc": datetime.now(timezone.utc).isoformat(),
    "environment_cache_overrides_only": cache_environment,
    "checks": cache_results,
    "scope": "Exact known-model snapshot directory stat and direct filenames only; no cache content, refs, blobs, private work directories or home-wide search.",
    "limitation": "No authors' humor-finetune HF ID/revision identified; these checks concern only its advertised initialization and underlying base.",
}), [], "Local filename metadata only; no model or tensor loaded")

manifest = {
    "audit_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "Public primary metadata/source inspection only; no dataset records, caption examples, weights, tokenizer vocabulary, provider inference or GPU access.",
    "pinning": {"github": GITHUB_REVISION, "arxiv": "2406.10522v2", "reward_initialization": REWARD_BASE_REVISION, "underlying_base": UPSTREAM_REVISION},
    "notes": [
        "Full HTTP documents may contain unselected sections; only named non-example excerpts/projections are retained.",
        "response_sha256 binds fetched response bytes, artifact_sha256 binds retained bytes; hashes differ for deliberate excerpts/projections or terminal LF normalization.",
        "Revision-pinned Git/HF text files additionally verify the response's Git blob SHA1 against server metadata.",
        "No claim that public availability establishes licensing, decontamination, or successful loading.",
    ],
    "artifacts": ARTIFACTS,
}
PENDING["PROVENANCE.json"] = json_text(manifest).encode()
for relative, content in PENDING.items():
    destination = ROOT / relative
    if destination.exists():
        if destination.read_bytes() == content:
            continue
        raise ValueError(f"Refusing to replace existing artifact: {relative}")
    target = destination.relative_to(WORKSPACE).as_posix()
    patch = "*** Begin Patch\n*** Add File: " + target + "\n"
    patch += "".join("+" + line + "\n" for line in content.decode().splitlines())
    patch += "*** End Patch\n"
    subprocess.run(["apply_patch", patch], cwd=WORKSPACE, check=True, capture_output=True, text=True)
    if destination.read_bytes() != content:
        raise ValueError(f"Written artifact hash mismatch: {relative}")
print(json_text({"created_files": sorted(PENDING), "retained_evidence_count": len(ARTIFACTS),
    "exact_snapshot_directories_found": sum(result["snapshot_directory_present"] for result in cache_results)}))
