"""Small durable JapanFold client: inputs, idempotency, status and owned artifacts."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import uuid
import zipfile
import io

BASE = "https://api.japanfold.aiand.com"


def utc():
    return datetime.now(timezone.utc).isoformat()


def api(path, payload=None, idempotency=None, raw=False, timeout=55):
    key = os.environ["JAPANFOLD_API_KEY"]
    headers = {"Authorization": "Bearer " + key, "X-JapanFold-Client": "skill"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if idempotency:
        headers["Idempotency-Key"] = idempotency
    req = Request(BASE + path, data=None if payload is None else json.dumps(payload).encode(), headers=headers)
    with urlopen(req, timeout=timeout) as response:
        body = response.read()
        return body if raw else json.loads(body)


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["submit", "status", "fetch", "metadata"])
    parser.add_argument("directory", type=Path)
    parser.add_argument("--wait", type=int, default=0, choices=range(0,46))
    args = parser.parse_args()
    root = args.directory.resolve()
    root.mkdir(parents=True, exist_ok=True)
    if args.action == "metadata":
        models = api("/v1/models")
        write(root / "models.json", models)
        credits = api("/v1/credits")
        write(root / "credits.json", {k:v for k,v in credits.items() if k in ("balance", "currency", "balance_micros")})
        print(json.dumps({"balance":credits.get("balance"),"currency":credits.get("currency")}))
        return
    if args.action == "submit":
        request_path = root / "request.json"
        digest = hashlib.sha256(request_path.read_bytes()).hexdigest()
        receipt = root / "submission.json"
        if receipt.exists():
            saved = json.loads(receipt.read_text())
            if saved["request_sha256"] != digest:
                raise ValueError("Changed request requires a new logical run directory")
            if saved.get("job_id"):
                print(json.dumps(saved))
                return
        else:
            saved = {"request_sha256":digest,"idempotency_key":str(uuid.uuid4()),"created_utc":utc()}
            write(receipt,saved)
        try:
            response = api("/v1/designs" if json.loads(request_path.read_text()).get("protocol") else "/v1/predictions",
                           json.loads(request_path.read_text()),saved["idempotency_key"])
        except HTTPError as error:
            # No secrets are sent back into logs. The public request error is retained.
            body = error.read().decode(errors="replace")
            write(root / "submit_error.json", {"status":error.code,"response":body,"utc":utc()})
            raise SystemExit(f"HTTP {error.code}; see submit_error.json")
        write(root / "submit_response.json",response)
        if not response.get("id"):
            raise ValueError("Missing job id; inspect response instead of submitting another job")
        saved.update(job_id=response["id"],status=response.get("status"),submitted_utc=utc())
        write(receipt,saved)
        write(root / "job.json",response)
        print(json.dumps(saved))
        return
    saved = json.loads((root / "submission.json").read_text())
    job_id = saved["job_id"]
    job = api(f"/v1/jobs/{job_id}" + (f"?wait={args.wait}" if args.wait else ""), timeout=55)
    write(root / "job.json",job)
    print(json.dumps({k:job.get(k) for k in ["id","status","stage","progress","done","total","queue","error","partial"]}),flush=True)
    if args.action != "fetch" or job.get("status") != "succeeded":
        return
    results = api(f"/v1/jobs/{job_id}/results")
    write(root / "results.json", results)
    archive_path = root / "artifacts.zip"
    if not archive_path.exists():
        content = api(f"/v1/jobs/{job_id}/archive",raw=True,timeout=55)
        archive_path.write_bytes(content)
    content = archive_path.read_bytes()
    destination = root / "artifacts"
    destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        if sum(member.file_size for member in archive.infolist()) > 640_000_000:
            raise ValueError("Archive exceeds documented output allowance")
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if not target.is_relative_to(destination.resolve()) or (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Unsafe artifact path or symlink")
        archive.extractall(destination)
    write(root / "download_receipt.json", {"job_id":job_id,"utc":utc(),
        "archive_sha256":hashlib.sha256(content).hexdigest(),
        "artifacts":[{"path":str(p.relative_to(destination)),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                       "bytes":p.stat().st_size} for p in sorted(destination.rglob('*')) if p.is_file()]})
    try:
        write(root / "usage.json", api(f"/v1/jobs/{job_id}/usage"))
    except HTTPError as error:
        write(root / "usage_pending.json",{"status":error.code,"utc":utc()})
    print("Downloaded and hashed artifacts",flush=True)


if __name__ == "__main__":
    main()
