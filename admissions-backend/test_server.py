import json
import sqlite3
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server import initialize_database, make_handler


class AdmissionsApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database_path = self.root / "admissions.sqlite3"
        self.site_directory = self.root / "site"
        self.site_directory.mkdir()
        (self.site_directory / "index.html").write_text("test page", encoding="utf-8")
        initialize_database(self.database_path)

        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            make_handler(self.database_path, self.site_directory),
        )
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp_dir.cleanup()

    def post(self, payload):
        request = Request(
            f"{self.base_url}/api/admissions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            response = urlopen(request)
        except HTTPError as error:
            with error:
                return error.code, json.loads(error.read())
        with response:
            return response.status, json.loads(response.read())

    def valid_payload(self):
        return {
            "learnerName": "Example Learner",
            "dateOfBirth": "2018-01-15",
            "requestedClass": "Grade 1",
            "previousSchool": "",
            "guardianName": "Example Guardian",
            "guardianRelationship": "Parent",
            "guardianEmail": "guardian@example.com",
            "guardianPhone": "+254 700 000 000",
            "guardianConsent": True,
        }

    def submission_count(self):
        with sqlite3.connect(self.database_path) as connection:
            return connection.execute("SELECT COUNT(*) FROM admissions").fetchone()[0]

    def test_valid_submission_is_stored(self):
        status, response = self.post(self.valid_payload())

        self.assertEqual(status, 201)
        self.assertEqual(response["message"], "Admission enquiry received.")
        self.assertEqual(self.submission_count(), 1)

    def test_invalid_consent_is_not_stored(self):
        payload = self.valid_payload()
        payload["guardianConsent"] = False

        status, response = self.post(payload)

        self.assertEqual(status, 400)
        self.assertIn("consent", response["error"].lower())
        self.assertEqual(self.submission_count(), 0)

    def test_future_date_of_birth_is_not_stored(self):
        payload = self.valid_payload()
        payload["dateOfBirth"] = "2999-01-01"

        status, _ = self.post(payload)

        self.assertEqual(status, 400)
        self.assertEqual(self.submission_count(), 0)

    def test_database_has_no_public_read_endpoint(self):
        with self.assertRaises(HTTPError) as raised:
            urlopen(f"{self.base_url}/api/admissions")

        self.assertEqual(raised.exception.code, 404)
        raised.exception.close()


if __name__ == "__main__":
    unittest.main()
