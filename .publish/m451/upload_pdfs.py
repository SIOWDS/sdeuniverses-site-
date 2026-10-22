"""Publish only the three reviewed volume 451 PDFs to the existing R2 bucket."""
import base64, hashlib, json, os, urllib.request
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

ROOT = Path(__file__).parent
manifest = json.loads((ROOT / "pdf-manifest.json").read_text())
expected = {
    "books/m/451/fasheng-shicha-reader-v1.1.pdf",
    "books/m/451/fasheng-shicha-print-v1.1.pdf",
    "books/m/451/downloads/fasheng-shicha-learning-v1.1.pdf",
}
assert {x["key"] for x in manifest} == expected and len(manifest) == 3
os.environ.setdefault("AWS_REQUEST_CHECKSUM_CALCULATION", "when_required")
os.environ.setdefault("AWS_RESPONSE_CHECKSUM_VALIDATION", "when_required")
client = boto3.client("s3", endpoint_url="https://d3ea22f828ce19cf113a457ceba2c930.r2.cloudflarestorage.com", region_name="auto")
bucket = "sdeuniverses-pdf"
results = []
for item in manifest:
    req = urllib.request.Request(
        "https://api.github.com/repos/SIOWDS/sdeuniverses-site-/git/blobs/" + item["blob"],
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Accept": "application/vnd.github+json", "User-Agent": "sde-m451-publication"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        obj = json.load(response)
    assert obj["encoding"] == "base64"
    data = base64.b64decode(obj["content"])
    assert len(data) == item["bytes"]
    assert hashlib.sha256(data).hexdigest() == item["sha256"]
    assert hashlib.md5(data).hexdigest() == item["md5"]
    assert data.startswith(b"%PDF-")
    try:
        existing = client.get_object(Bucket=bucket, Key=item["key"])["Body"].read()
    except ClientError as e:
        if e.response["Error"]["Code"] not in ("NoSuchKey", "404"):
            raise
        existing = None
    if existing is not None:
        assert existing == data, "Existing object differs; refusing overwrite: " + item["key"]
    else:
        client.put_object(Bucket=bucket, Key=item["key"], Body=data,
                          ContentType="application/pdf", ContentDisposition="inline",
                          Metadata={"sha256": item["sha256"]},
                          ContentMD5=base64.b64encode(hashlib.md5(data).digest()).decode())
    verified = client.get_object(Bucket=bucket, Key=item["key"])["Body"].read()
    assert hashlib.sha256(verified).hexdigest() == item["sha256"]
    results.append({**item, "r2Verified": True})
    print("Verified", item["key"], len(verified), item["sha256"])
Path("m451-r2-result.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
