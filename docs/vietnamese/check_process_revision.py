"""Check arithmetic examples, diagram guard, code visibility and source links."""
import hashlib
import importlib.util
import json
import re
from datetime import datetime
from pathlib import Path

import fitz
import numpy as np
from reportlab.platypus import SimpleDocTemplate
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, accuracy_score

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
TEMP=ROOT/"tmp/pdfs/process-regression"


def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


if __name__=="__main__":
    TEMP.mkdir(parents=True,exist_ok=True)
    renderer=module("study_pdf_builder",HERE/"build_pdfs.py")
    validator=module("study_pdf_validator",HERE/"validate_pdfs.py")
    renderer.font_setup()
    source=HERE/"02-quy-trinh-nghien-cuu.md"
    text=source.read_text(encoding="utf-8")
    assert "```mermaid" not in text
    for target in re.findall(r'\]\(([^)]+)\)',text):
        if not re.match(r'https?://|mailto:|#',target):
            assert (HERE/target.split("#")[0]).exists(),target
    try:
        renderer.parse_markdown("```mermaid\nflowchart TD\nA-->B\n```",renderer.styles())
    except ValueError:
        pass
    else:
        raise AssertionError("Raw diagram code must be rejected.")

    # Force pagination and long-line wrapping; check actual paint order.
    lines=[f"ROW{i:03d} abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ" for i in range(90)]
    lines.insert(7,"LONG "+"abcdefghij "*25)
    probe=TEMP/"code-visibility-probe.pdf"
    SimpleDocTemplate(str(probe)).build([renderer.CodeBlock(lines,renderer.styles()["code"])])
    doc=fitz.open(probe)
    full="\n".join(p.get_text() for p in doc)
    for i in range(90):
        assert full.count(f"ROW{i:03d}")==1,i
    for page in doc:
        assert not validator.opaque_text_overpaints(page)
        for kind,bbox in page.get_bboxlog():
            if kind=="fill-text":
                assert bbox[0]>=70 and bbox[2]<=page.rect.width-70,bbox
    assert len(doc)>=2
    probe_pages=len(doc)
    doc.close()

    day=lambda value:datetime.fromisoformat(value)
    assert (day("2011-07-01")-day("2011-01-01")).days==181
    assert (day("2011-07-01")-day("2011-06-01")).days==30
    assert (day("2011-06-01")-day("2011-01-01")).days==151
    assert ((day("2011-02-01")-day("2011-01-01")).days+
            (day("2011-06-01")-day("2011-02-01")).days)/2==75.5
    labels={"A":1,"B":0,"C":1,"D":0}
    neighbors={"A":"BCE","B":"ADF","C":"AEG","D":"BFH",
               "E":"ACF","F":"EGH","G":"BDH","H":"CEG"}
    expected=[.5,.5,1,0,1,.5,0,1]
    ncr=[]
    for node in "ABCDEFGH":
        selected=[labels[x] for x in neighbors[node] if x in labels]
        ncr.append(float(np.mean(selected)) if selected else .5)
    assert ncr==expected
    y=np.array([1,0,1,0]);scores=np.array([.9,.7,.6,.2])
    assert roc_auc_score(y,scores)==.75
    assert np.isclose(average_precision_score(y,scores),5/6)
    assert f1_score(y,scores>=.5)==.8
    assert accuracy_score(y,scores>=.5)==.75
    assert np.isclose(np.sqrt((1/50+1/4)/(1/50)),np.sqrt(13.5))

    manifest=json.loads((HERE/"evidence/reproduction-manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["jobs"])==10
    assert all(j["exit_code"]==0 for j in manifest["jobs"])
    for job in manifest["jobs"]:
        assert f"{job['seconds']:.1f}".replace(".",",") in text

    result={"status":"passed","source":source.relative_to(ROOT).as_posix(),
            "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "checks":["All internal links exist","Mermaid rejected before PDF build",
                      "90 probe rows survive wrapping and page splits exactly once",
                      "No later opaque fill masks probe text","Feature dates/IPT arithmetic",
                      "Eight-node NCR example","AUC/AP/F1/accuracy example",
                      "Nadeau-Bengio SE example","Ten job durations match run manifest"],
            "probe_pages":probe_pages,"hypothetical_examples_not_new_model_runs":True}
    (HERE/"evidence/process-revision-checks.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
