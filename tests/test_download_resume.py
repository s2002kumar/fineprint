"""Resumable download against a local HTTP server with Range/If-Range/ETag semantics."""

import hashlib
import http.server
import tempfile
import threading
import unittest
from pathlib import Path

from fineprint import download, ndc


class _State:
    body = b""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _etag(self):
        return '"' + hashlib.md5(_State.body).hexdigest() + '"'

    def _headers(self, status, length, extra=()):
        self.send_response(status)
        self.send_header("Content-Length", str(length))
        self.send_header("ETag", self._etag())
        self.send_header("Accept-Ranges", "bytes")
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()

    def do_HEAD(self):
        self._headers(200, len(_State.body))

    def do_GET(self):
        body, rng = _State.body, self.headers.get("Range")
        if rng and self.headers.get("If-Range") in (None, self._etag()):
            start = int(rng.split("=")[1].split("-")[0])
            self._headers(206, len(body) - start, [("Content-Range", f"bytes {start}-{len(body) - 1}/{len(body)}")])
            self.wfile.write(body[start:])
        else:
            self._headers(200, len(body))
            self.wfile.write(body)


class ResumableDownload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.srv.server_address[1]}/part.zip"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dest = Path(self.tmp.name) / "part.zip"

    def tearDown(self):
        self.tmp.cleanup()

    def test_interrupt_then_resume(self):
        _State.body = bytes(range(256)) * 80000  # ~20 MB
        md5 = hashlib.md5(_State.body).hexdigest()
        with self.assertRaises(download.DownloadInterrupted):
            download.download(self.url, self.dest, expected_md5=md5, stop_after_bytes=9 << 20)
        self.assertFalse(self.dest.exists())
        rec = download.download(self.url, self.dest, expected_md5=md5)
        self.assertTrue(rec["resumed"])
        self.assertGreater(rec["segments"][-1]["from_byte"], 0)
        self.assertEqual(rec["sha256"], hashlib.sha256(_State.body).hexdigest())
        self.assertEqual(download.download(self.url, self.dest, expected_md5=md5)["status"], "verified_existing")

    def test_changed_object_is_never_spliced(self):
        _State.body = b"A" * (12 << 20)
        with self.assertRaises(download.DownloadInterrupted):
            download.download(self.url, self.dest, stop_after_bytes=8 << 20)
        _State.body = b"B" * (12 << 20)  # release replaced while we were away
        rec = download.download(self.url, self.dest, expected_md5=hashlib.md5(_State.body).hexdigest())
        self.assertEqual(self.dest.read_bytes(), _State.body)
        self.assertEqual(rec["md5"], hashlib.md5(_State.body).hexdigest())

    def test_md5_mismatch_leaves_no_final_file(self):
        _State.body = b"C" * 1000
        with self.assertRaises(download.VerificationFailed):
            download.download(self.url, self.dest, expected_md5="0" * 32)
        self.assertFalse(self.dest.exists())


class ProductNdc(unittest.TestCase):
    def test_product_5_4_never_accepts_package_codes(self):
        self.assertEqual(ndc.to_product_5_4("0409-3308"), "00409-3308")
        self.assertEqual(ndc.to_product_5_4("12345-678"), "12345-0678")
        self.assertEqual(ndc.to_product_5_4("12345-6789"), "12345-6789")
        self.assertIsNone(ndc.to_product_5_4("0409-3308-03"))
        self.assertIsNone(ndc.to_product_5_4("04093308"))


class NoPersonalDataInRepoFixtures(unittest.TestCase):
    def test_fixtures_and_evidence_have_no_contacts(self):
        import re
        root = Path(__file__).resolve().parents[1]
        pat = re.compile(rb"<contactParty|mailto:|tel:\+?[0-9]|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.(?:com|org|net|gov|edu)\b")
        hits = [str(p) for d in ("tests/fixtures", "evidence") for p in (root / d).rglob("*") if p.is_file()
                and pat.search(p.read_bytes())]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
