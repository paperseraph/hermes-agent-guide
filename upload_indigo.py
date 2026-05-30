#!/usr/bin/env python3
"""Deploy indigo HTML to Cloudflare Pages hermes-handbook project."""
import json, urllib.request, hashlib, sys

TOKEN_FILE = r"C:\Users\Administrator\.cf_token_clean"
HTML_PATH = r"D:\AIMODEL\hermes\sites\indigo\index.html"
ACCOUNT = "0be7d0df18e00432f107549d2fa07886"
PROJECT = "hermes-handbook"

with open(TOKEN_FILE) as f:
    TOKEN = f.read().strip()

def call(method, path, body=None, content_type="application/json"):
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/pages/projects/{PROJECT}{path}"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if body is not None:
        headers["Content-Type"] = content_type
    if isinstance(body, str):
        body = body.encode()
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

# Step 1: Create project (if not exists)
print("1. Creating project...")
res = call("POST", "", json.dumps({"name": PROJECT, "production_branch": "main"}))
if res.get("success"):
    print(f"   Created: {PROJECT}.pages.dev")
else:
    errs = res.get("errors", [])
    if any("already exists" in str(e) for e in errs):
        print("   Project already exists.")
    else:
        print(f"   Error: {json.dumps(errs, indent=2, ensure_ascii=False)}")
        sys.exit(1)

# Step 2: Read HTML and compute hash
with open(HTML_PATH, "rb") as f:
    content = f.read()
sha = hashlib.sha256(content).hexdigest()
size = len(content)
print(f"2. HTML: {size} bytes, sha256={sha[:16]}...")

# Step 3: Build multipart body
boundary = "----CFPagesUpload"
manifest = {"/index.html": {"hash": sha, "size": size}}

body = b""
# manifest part
body += f"--{boundary}\r\n".encode()
body += b'Content-Disposition: form-data; name="manifest"\r\n'
body += b"Content-Type: application/json\r\n\r\n"
body += json.dumps(manifest).encode()
body += b"\r\n"
# file part
body += f"--{boundary}\r\n".encode()
body += b'Content-Disposition: form-data; name="/index.html"; filename="index.html"\r\n'
body += b"Content-Type: application/octet-stream\r\n\r\n"
body += content
body += b"\r\n"
body += f"--{boundary}--\r\n".encode()

# Step 4: Upload
print("3. Uploading...")
res = call("POST", "/deployments", body, content_type=f"multipart/form-data; boundary={boundary}")

if res.get("success"):
    d = res["result"]
    print(f"\nDone!")
    print(f"   URL: {d.get('url', PROJECT + '.pages.dev')}")
    print(f"   Stage: {d.get('latest_stage',{}).get('name','?')}")
else:
    print(f"\nUpload failed: {json.dumps(res.get('errors'), indent=2, ensure_ascii=False)}")
