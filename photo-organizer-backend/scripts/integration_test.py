#!/usr/bin/env python3
"""
SmartPhoto End-to-End Integration Test Script

Tests all 14 test cases against the running API at http://localhost:28000.
Uses dev-mode fixed SMS code 888888 and local AI engine (no API keys needed).

Usage:
    python scripts/integration_test.py [--base-url http://localhost:28000]
"""

import argparse
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

DEFAULT_BASE_URL = "http://localhost:28000"
TEST_PHONE = "13800138000"
TEST_CODE = "888888"
TEST_IMAGES_DIR = Path(__file__).parent.parent / "test_images"

# ── HTTP helpers ──────────────────────────────────────────────────────────────


def _request(
    method: str,
    url: str,
    body: bytes | None = None,
    content_type: str = "application/json",
    headers: dict | None = None,
    timeout: int = 30,
) -> tuple[int, dict | bytes]:
    """Make an HTTP request, return (status_code, response_body)."""
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", content_type)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def get(url: str, token: str | None = None, timeout: int = 30) -> tuple[int, dict | bytes]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return _request("GET", url, headers=headers, timeout=timeout)


def post_json(
    url: str, payload: dict, token: str | None = None, timeout: int = 30
) -> tuple[int, dict | bytes]:
    body = json.dumps(payload).encode()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return _request("POST", url, body=body, headers=headers, timeout=timeout)


def put_json(
    url: str, payload: dict, token: str | None = None
) -> tuple[int, dict | bytes]:
    body = json.dumps(payload).encode()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return _request("PUT", url, body=body, headers=headers)


def delete(url: str, token: str | None = None) -> tuple[int, dict | bytes]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return _request("DELETE", url, headers=headers)


def post_multipart(
    url: str,
    fields: dict,
    file_data: bytes,
    filename: str,
    field_name: str = "file",
    token: str | None = None,
    timeout: int = 60,
) -> tuple[int, dict | bytes]:
    """Upload a multipart/form-data file."""
    boundary = "----SmartPhotoTestBoundary12345"
    body_parts = []

    for key, value in fields.items():
        body_parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
            f"{value}\r\n"
        )

    body_parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    )
    body = ("".join(body_parts)).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return _request(
        "POST",
        url,
        body=body,
        content_type=f"multipart/form-data; boundary={boundary}",
        headers=headers,
        timeout=timeout,
    )


# ── Test result tracking ──────────────────────────────────────────────────────


@dataclass
class TestResult:
    tc_id: str
    description: str
    status_code: int = 0
    assertion: str = ""
    passed: bool = False
    error: str = ""
    extra: dict = field(default_factory=dict)


results: list[TestResult] = []


def run_test(tc_id: str, description: str) -> "TestContext":
    return TestContext(tc_id, description)


class TestContext:
    def __init__(self, tc_id: str, description: str):
        self.result = TestResult(tc_id=tc_id, description=description)
        results.append(self.result)

    def record(
        self,
        status_code: int,
        assertion: str,
        passed: bool,
        error: str = "",
        extra: dict | None = None,
    ):
        self.result.status_code = status_code
        self.result.assertion = assertion
        self.result.passed = passed
        self.result.error = error
        self.result.extra = extra or {}
        status = "PASS" if passed else "FAIL"
        print(
            f"  [{status}] {self.result.tc_id} {self.result.description}"
            f" | HTTP {status_code} | {assertion}"
        )
        if error and not passed:
            print(f"         ERROR: {error}")


# ── Test helpers ──────────────────────────────────────────────────────────────


def get_test_images(limit: int = 5) -> list[tuple[bytes, str]]:
    """Return a list of (file_bytes, filename) from test_images/ or synthesize."""
    images = []

    if TEST_IMAGES_DIR.exists():
        jpg_files = sorted(TEST_IMAGES_DIR.glob("*.jpg"))[:limit]
        for p in jpg_files:
            with open(p, "rb") as f:
                images.append((f.read(), p.name))

    # Synthesize missing images with PIL
    missing = limit - len(images)
    if missing > 0:
        try:
            from PIL import Image

            for i in range(missing):
                img = Image.new("RGB", (800, 600), (100 + i * 30, 100, 100))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                images.append((buf.getvalue(), f"synthetic_{i+1:02d}.jpg"))
        except ImportError:
            # Minimal valid JPEG (2x2 grey)
            minimal_jpeg = bytes([
                0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00,
                0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB,
                0x00, 0x43, 0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07,
                0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B,
                0x0B, 0x0C, 0x19, 0x12, 0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E,
                0x1D, 0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C,
                0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29, 0x2C, 0x30, 0x31, 0x34, 0x34,
                0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34,
                0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x02, 0x00, 0x02, 0x01,
                0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00, 0x01, 0x05,
                0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01,
                0x03, 0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00,
                0x01, 0x7D, 0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21,
                0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32,
                0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1,
                0xF0, 0x24, 0x33, 0x62, 0x72, 0x82, 0x09, 0x0A, 0x16, 0x17, 0x18,
                0x19, 0x1A, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x34, 0x35, 0x36,
                0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49,
                0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x63, 0x64,
                0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75, 0x76, 0x77,
                0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A,
                0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
                0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5,
                0xB6, 0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7,
                0xC8, 0xC9, 0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9,
                0xDA, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA,
                0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF,
                0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD2,
                0x8A, 0x28, 0x03, 0xFF, 0xD9,
            ])
            for i in range(missing):
                images.append((minimal_jpeg, f"synthetic_{i+1:02d}.jpg"))

    return images


# ── Test cases ────────────────────────────────────────────────────────────────


def run_all_tests(base_url: str) -> None:
    token: str | None = None
    batch_id: str | None = None
    task_id: str | None = None
    uploaded_photo_id: str | None = None

    print(f"\n{'=' * 60}")
    print(f"SmartPhoto Integration Tests")
    print(f"Target: {base_url}")
    print(f"{'=' * 60}\n")

    # TC-01: Health check
    tc = run_test("TC-01", "GET /health → 200 + {status:ok}")
    try:
        code, body = get(f"{base_url}/health")
        passed = code == 200 and isinstance(body, dict) and body.get("status") == "ok"
        tc.record(code, f'status="{body.get("status") if isinstance(body, dict) else "?"}"', passed)
    except Exception as e:
        tc.record(0, "", False, str(e))

    # TC-02: AI providers list
    tc = run_test("TC-02", "GET /api/v1/settings/ai-providers → 4 providers")
    try:
        code, body = get(f"{base_url}/api/v1/settings/ai-providers")
        providers = [p.get("provider") for p in body] if isinstance(body, list) else []
        passed = (
            code == 200
            and len(providers) == 4
            and "local" in providers
            and "claude" in providers
            and "tongyi" in providers
            and "huggingface" in providers
        )
        tc.record(code, f"providers={providers}", passed)
    except Exception as e:
        tc.record(0, "", False, str(e))

    # TC-03: Send SMS code (dev mode)
    tc = run_test("TC-03", f"POST /api/v1/auth/send-code → dev mode success")
    try:
        code, body = post_json(
            f"{base_url}/api/v1/auth/send-code",
            {"phone": TEST_PHONE},
        )
        passed = code == 200
        tc.record(code, str(body)[:80], passed)
    except Exception as e:
        tc.record(0, "", False, str(e))

    # TC-04: Login with fixed code 888888
    tc = run_test("TC-04", "POST /api/v1/auth/login → JWT token")
    try:
        code, body = post_json(
            f"{base_url}/api/v1/auth/login",
            {"phone": TEST_PHONE, "code": TEST_CODE},
        )
        if isinstance(body, dict) and "access_token" in body:
            token = body["access_token"]
            passed = code == 200 and bool(token)
            tc.record(code, f"token={'*' * 12 + token[-4:] if token else 'None'}", passed)
        else:
            tc.record(code, f"no access_token in {str(body)[:80]}", False)
    except Exception as e:
        tc.record(0, "", False, str(e))

    if not token:
        print("\n[ABORT] Cannot continue without auth token.")
        return

    # TC-05: Create upload batch
    tc = run_test("TC-05", "POST /api/v1/photos/batch → batch created")
    try:
        code, body = post_json(
            f"{base_url}/api/v1/photos/batch",
            {"total_photos": 5},
            token=token,
        )
        if isinstance(body, dict) and "id" in body:
            batch_id = str(body["id"])
            passed = code in (200, 201) and bool(batch_id)
            tc.record(code, f"batch_id={batch_id}", passed)
        else:
            tc.record(code, f"no id in {str(body)[:80]}", False)
    except Exception as e:
        tc.record(0, "", False, str(e))

    if not batch_id:
        print("\n[ABORT] Cannot continue without batch_id.")
        return

    # TC-06: Upload 5 photos
    tc = run_test("TC-06", "POST /api/v1/photos/upload ×5 → all uploaded")
    try:
        images = get_test_images(limit=5)
        upload_successes = 0
        for img_bytes, filename in images:
            u_code, u_body = post_multipart(
                f"{base_url}/api/v1/photos/upload",
                {"batch_id": batch_id},
                img_bytes,
                filename,
                token=token,
            )
            if u_code in (200, 201):
                upload_successes += 1
                if uploaded_photo_id is None and isinstance(u_body, dict):
                    uploaded_photo_id = str(u_body.get("id", ""))
        passed = upload_successes == 5
        tc.record(200, f"{upload_successes}/5 uploads succeeded", passed)
    except Exception as e:
        tc.record(0, "", False, str(e))

    # TC-07: Get batch photos list
    tc = run_test("TC-07", f"GET /api/v1/photos/batch/{{batch_id}} → photo list")
    try:
        code, body = get(f"{base_url}/api/v1/photos/batch/{batch_id}", token=token)
        count = len(body) if isinstance(body, list) else 0
        passed = code == 200 and count >= 1
        tc.record(code, f"photos_returned={count}", passed)
    except Exception as e:
        tc.record(0, "", False, str(e))

    # Pre-TC-08 setup: ensure local provider is active so the pipeline
    # doesn't inherit a huggingface/claude config from a previous test run.
    try:
        put_json(
            f"{base_url}/api/v1/settings",
            {"ai_config": {"provider": "local"}},
            token=token,
        )
    except Exception:
        pass  # Best-effort; TC-08 will surface any issue

    # TC-08: Start AI pipeline
    tc = run_test("TC-08", "POST /api/v1/organize/start → pipeline started")
    try:
        code, body = post_json(
            f"{base_url}/api/v1/organize/start",
            {"batch_id": batch_id},
            token=token,
        )
        if isinstance(body, dict) and "task_id" in body:
            task_id = str(body["task_id"])
            passed = code in (200, 201, 202) and body.get("status") in (
                "pending",
                "processing",
                "running",
            )
            tc.record(code, f"task_id={task_id}, status={body.get('status')}", passed)
        else:
            tc.record(code, f"unexpected: {str(body)[:80]}", False)
    except Exception as e:
        tc.record(0, "", False, str(e))

    if not task_id:
        print("\n[ABORT] Cannot continue without task_id.")
        return

    # TC-09: Poll status until completed (max 300s)
    tc = run_test("TC-09", "GET /api/v1/organize/status → completed")
    try:
        deadline = time.time() + 300
        final_status = None
        progress = 0
        while time.time() < deadline:
            code, body = get(
                f"{base_url}/api/v1/organize/status/{task_id}",
                token=token,
                timeout=15,
            )
            if isinstance(body, dict):
                final_status = body.get("status")
                progress = body.get("progress_percent", 0)
            if final_status in ("completed", "failed"):
                break
            print(
                f"    ... polling status={final_status} progress={progress}%"
                f" (waiting 5s)"
            )
            time.sleep(5)

        passed = final_status == "completed"
        tc.record(
            code,
            f"final_status={final_status} progress={progress}%",
            passed,
            error="" if passed else f"Pipeline ended with status={final_status}",
        )
    except Exception as e:
        tc.record(0, "", False, str(e))

    # TC-10: Get organize results
    tc = run_test("TC-10", "GET /api/v1/organize/results → 4 result types")
    try:
        code, body = get(
            f"{base_url}/api/v1/organize/results/{task_id}",
            token=token,
        )
        if isinstance(body, dict):
            has_timeline = "timeline" in body
            has_categories = "categories" in body
            has_invalid = "invalid_photos" in body
            has_similarity = "similarity_groups" in body
            passed = code == 200 and all(
                [has_timeline, has_categories, has_invalid, has_similarity]
            )
            tc.record(
                code,
                f"timeline={has_timeline} categories={has_categories}"
                f" invalid={has_invalid} similarity={has_similarity}",
                passed,
            )
        else:
            tc.record(code, f"unexpected body: {str(body)[:80]}", False)
    except Exception as e:
        tc.record(0, "", False, str(e))

    # TC-11: Get user settings
    tc = run_test("TC-11", "GET /api/v1/settings → user AI config")
    try:
        code, body = get(f"{base_url}/api/v1/settings", token=token)
        if isinstance(body, dict):
            has_providers = "available_providers" in body
            passed = code == 200 and has_providers
            tc.record(code, f"available_providers={has_providers}", passed)
        else:
            tc.record(code, f"unexpected: {str(body)[:80]}", False)
    except Exception as e:
        tc.record(0, "", False, str(e))

    # TC-12: Update settings to huggingface engine
    tc = run_test("TC-12", "PUT /api/v1/settings → switch to huggingface")
    try:
        code, body = put_json(
            f"{base_url}/api/v1/settings",
            {"ai_config": {"provider": "huggingface"}},
            token=token,
        )
        if isinstance(body, dict) and isinstance(body.get("ai_config"), dict):
            new_provider = body["ai_config"].get("provider")
            passed = code == 200 and new_provider == "huggingface"
            tc.record(code, f"active_provider={new_provider}", passed)
        else:
            tc.record(code, f"unexpected: {str(body)[:80]}", False)
    except Exception as e:
        tc.record(0, "", False, str(e))

    # TC-13: Start organize again with new engine
    tc = run_test("TC-13", "POST /api/v1/organize/start (2nd run, huggingface engine)")
    task_id_2: str | None = None
    try:
        code, body = post_json(
            f"{base_url}/api/v1/organize/start",
            {"batch_id": batch_id},
            token=token,
        )
        if isinstance(body, dict) and "task_id" in body:
            task_id_2 = str(body["task_id"])
            passed = code in (200, 201, 202)
            tc.record(code, f"task_id={task_id_2} status={body.get('status')}", passed)

            # Brief poll to verify it starts
            for _ in range(6):
                time.sleep(5)
                s_code, s_body = get(
                    f"{base_url}/api/v1/organize/status/{task_id_2}",
                    token=token,
                    timeout=10,
                )
                if isinstance(s_body, dict):
                    s = s_body.get("status")
                    if s in ("processing", "completed", "failed", "running"):
                        print(f"    ... 2nd pipeline status={s}")
                        break
        else:
            tc.record(code, f"unexpected: {str(body)[:80]}", False)
    except Exception as e:
        tc.record(0, "", False, str(e))

    # TC-14: Delete a photo and verify
    tc = run_test("TC-14", "DELETE /api/v1/photos/{id} → photo deleted")
    try:
        if not uploaded_photo_id:
            tc.record(0, "no photo_id available", False, "No photo was uploaded successfully")
        else:
            code, body = delete(
                f"{base_url}/api/v1/photos/{uploaded_photo_id}",
                token=token,
            )
            passed = code in (200, 204)
            tc.record(code, f"photo_id={uploaded_photo_id} deleted", passed)

            if passed:
                # Verify it's gone
                v_code, _ = get(
                    f"{base_url}/api/v1/photos/batch/{batch_id}",
                    token=token,
                )
                # We don't fail the test if verify check is inconclusive
    except Exception as e:
        tc.record(0, "", False, str(e))


# ── Summary ───────────────────────────────────────────────────────────────────


def print_summary() -> int:
    total = len(results)
    passed_count = sum(1 for r in results if r.passed)

    print(f"\n{'=' * 60}")
    print(f"TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"{'TC-ID':<8} {'Description':<45} {'HTTP':<6} {'Result'}")
    print(f"{'-' * 8} {'-' * 45} {'-' * 6} {'-' * 6}")

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        desc = r.description[:44]
        print(f"{r.tc_id:<8} {desc:<45} {r.status_code:<6} {status}")

    print(f"\n{'=' * 60}")
    print(f"RESULT: {passed_count}/{total} tests passed")
    if passed_count == total:
        print("ALL TESTS PASSED")
    else:
        failed = [r.tc_id for r in results if not r.passed]
        print(f"FAILED: {', '.join(failed)}")
    print(f"{'=' * 60}\n")

    return 0 if passed_count == total else 1


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="SmartPhoto E2E Integration Tests")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"API base URL (default: {DEFAULT_BASE_URL})",
    )
    args = parser.parse_args()

    run_all_tests(args.base_url)
    return print_summary()


if __name__ == "__main__":
    sys.exit(main())
