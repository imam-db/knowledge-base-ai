from __future__ import annotations

from pathlib import Path

import httpx

base = "http://127.0.0.1:8000/api/v1"
key = "dev-admin-key-change-me"
sample = Path("documents/sample_faq.docx").read_bytes()


def report(label: str, r: httpx.Response) -> None:
    print(f"--- {label} ---")
    print(r.status_code, r.text[:300])


def main() -> None:
    c = httpx.Client(timeout=120.0)
    files_docx = {
        "file": (
            "a.docx",
            sample,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }

    r = c.post(f"{base}/documents/upload", files=files_docx)
    report("401 no key", r)
    assert r.status_code == 401

    r = c.post(
        f"{base}/documents/upload",
        headers={"X-API-Key": "wrong"},
        files=files_docx,
    )
    report("401 wrong key", r)
    assert r.status_code == 401

    r = c.post(
        f"{base}/documents/upload",
        headers={"X-API-Key": key},
        files={"file": ("fake.pdf", b"HELLO NOT PDF", "application/pdf")},
    )
    report("bad format", r)
    assert r.status_code == 400
    assert "Unsupported" in r.json()["detail"]

    big = b"%PDF" + b"x" * (20 * 1024 * 1024)
    r = c.post(
        f"{base}/documents/upload",
        headers={"X-API-Key": key},
        files={"file": ("big.pdf", big, "application/pdf")},
    )
    report("too large", r)
    assert r.status_code == 400
    assert "too large" in r.json()["detail"].lower()

    upload_files = {
        "file": (
            "m6_hr_policy.docx",
            sample,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    r = c.post(
        f"{base}/documents/upload",
        headers={"X-API-Key": key},
        files=upload_files,
    )
    report("upload new", r)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["document_name"] == "m6_hr_policy.docx"
    assert body["chunks_created"] >= 1
    assert body["status"] == "ready"
    doc_id = body["document_id"]

    docs = c.get(f"{base}/documents").json()["documents"]
    names = [d["name"] for d in docs]
    print("docs:", names)
    assert "m6_hr_policy.docx" in names
    assert "sample_faq.docx" in names

    r = c.post(
        f"{base}/documents/upload",
        headers={"X-API-Key": key},
        files=upload_files,
    )
    report("replace", r)
    assert r.status_code == 200
    assert r.json()["document_id"] == doc_id
    docs2 = c.get(f"{base}/documents").json()["documents"]
    assert sum(1 for d in docs2 if d["name"] == "m6_hr_policy.docx") == 1
    print("unique m6_hr_policy count ok; total docs", len(docs2))

    ask = c.post(f"{base}/ask", json={"question": "Bagaimana cara reset password?"})
    report("ask", ask)
    assert ask.status_code == 200
    print("OK all e2e api checks")


if __name__ == "__main__":
    main()
