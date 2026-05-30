#!/usr/bin/env python3
"""Deploy hero-remix to Cloudflare Pages."""
import json, urllib.request, hashlib, os

TOKEN = open(r"C:\Users\Administrator\.cf_token_clean").read().strip()
ACCOUNT = "0be7d0df18e00432f107549d2fa07886"
PROJECT = "hermes-handbook"
HTML_PATH = r"D:\AIMODEL\hermes\sites\indigo\index.html"

# Step 1: Create project
print("Creating project...")
req = urllib.request.Request(
    f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/pages/projects",
    data=json.dumps({"name": PROJECT, "production_branch": "main"}).encode(),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    method="POST"
)
try:
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read())
except urllib.error.HTTPError as e:
    res = json.loads(e.read())

if res.get("success"):
    print("  Created:", res["result"]["subdomain"] + ".pages.dev")
else:
    errs = res.get("errors", [])
    if any("already exists" in str(e) for e in errs):
        print("  Project already exists, continuing...")
    else:
        print("  Error:", json.dumps(errs, indent=2, ensure_ascii=False))
        exit(1)

# Step 2: Upload HTML
print("Uploading index.html...")
with open(HTML_PATH, "rb") as f:
    content = f.read()

sha = hashlib.sha256(content).hexdigest()
size = len(content)

boundary = "----CFPages"
body = b""
body += f"--{boundary}\r\n".encode()
body += b'Content-Disposition: form-data; name="manifest"\r\n'
body += b"Content-Type: application/json\r\n\r\n"
body += json.dumps({"/index.html": {"hash": sha, "size": size}}).encode()
body += b"\r\n"
body += f"--{boundary}\r\n".encode()
body += b'Content-Disposition: form-data; name="/index.html"; filename="index.html"\r\n'
body += b"Content-Type: application/octet-stream\r\n\r\n"
body += content
body += b"\r\n"
body += f"--{boundary}--\r\n".encode()

url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/pages/projects/{PROJECT}/deployments"
req = urllib.request.Request(
    url, data=body, method="POST",
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    }
)
try:
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read())
except urllib.error.HTTPError as e:
    res = json.loads(e.read())

if res.get("success"):
    d = res["result"]
    print(f"\nDeployed!")
    print(f"  URL: {d.get('url', 'https://hermes-handbook.pages.dev')}")
    print(f"  Stage: {d.get('latest_stage', {}).get('name', '?')}")
else:
    print("Error:", json.dumps(res.get("errors"), indent=2, ensure_ascii=False))
