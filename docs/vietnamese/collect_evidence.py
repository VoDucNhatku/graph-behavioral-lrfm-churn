"""Create a public, path-independent evidence package from the actual local rerun."""
from pathlib import Path
import json
import shutil
import hashlib

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / "notes/reproduce-20261012"
PUBLIC = ROOT / "docs/vietnamese/evidence"
RESULTS = ROOT / "results/reproduction-20261012"


def save(name, value):
    (PUBLIC/name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    PUBLIC.mkdir(parents=True, exist_ok=True)
    m = json.loads((LOCAL/"run-manifest.json").read_text(encoding="utf-8"))
    assert m["status"] == "completed" and len(m["jobs"]) == 10
    assert all(j["exit_code"] == 0 for j in m["jobs"])
    fingerprint = m["fingerprint"]
    manifest = {"kind": "Public evidence of actual 2026-10-12 Windows CPU rerun",
        "status": m["status"], "started": m["started"], "finished": m["finished"],
        "git_commit": fingerprint["git_commit"], "python": fingerprint["python"],
        "platform": fingerprint["platform"], "logical_cpus": fingerprint["logical_cpus"],
        "requirements": fingerprint["requirements"], "dataset": "online_retail_II.xlsx",
        "dataset_sha256": fingerprint["dataset_sha256"], "paper_sha256": fingerprint["paper_sha256"],
        "source_sha256": fingerprint["source_sha256"],
        "dataset_unchanged": m["dataset_unchanged"], "original_sources_unchanged": m["original_sources_unchanged"],
        "tracked_files_compared_at_run": m["tracked_files_compared"],
        "jobs": [{key: job[key] for key in ["name", "script", "overrides", "started", "finished", "seconds", "exit_code", "status"]}
                 for job in m["jobs"]],
        "scope": "Unchanged source. The first repeated-CV run builds features from raw XLSX in memory; k-sweep uses its newly written cache. Not a corrected-window model run."}
    save("reproduction-manifest.json", manifest)
    for name in ["comparison.json", "uci-download-verification.json", "paper-vs-rerun.csv", "archive-vs-rerun.csv"]:
        shutil.copy2(LOCAL/name, PUBLIC/name)
    verification = json.loads((LOCAL/"notebook-verification.json").read_text(encoding="utf-8"))
    save("notebook-verification.json", verification)
    identity = json.loads((LOCAL/"github-vs-local.json").read_text(encoding="utf-8"))
    save("source-identity.json", identity)
    # The original identity file contains absolute author-supplied paths. Publish
    # only the observed facts used by the report, with the current local hash.
    save("paper-identity.json", {"paper_id": 366956, "local_pages": 12, "supplied_pages": 12,
        "text_content_render_match": True, "byte_relationship": "supplied PDF = local PDF + trailing 0x0D",
        "local_sha256": hashlib.sha256((ROOT/"paper/main.pdf").read_bytes()).hexdigest(),
        "supplied_sha256": "f7278d5662d3549f86b33ba02f0b7f7e715e8d2839ce74517747e7e01e596193",
        "provenance": "Author identified the supplied PDF as their submitted file; no fresh Confy download was performed."})
    copied = []
    for folder in ["main", "seed42"]:
        destination = RESULTS/folder
        destination.mkdir(parents=True, exist_ok=True)
        for source in sorted((LOCAL/"outputs"/folder).glob("*.csv")):
            if source.name == "feat_cache.csv" or "assignment" in source.name.lower():
                continue
            target = destination/source.name
            shutil.copy2(source, target)
            copied.append({"path": target.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    save("aggregate-output-hashes.json", copied)
    print(json.dumps({"public_evidence": PUBLIC.relative_to(ROOT).as_posix(), "aggregate_csv_files": len(copied)}, indent=2))
