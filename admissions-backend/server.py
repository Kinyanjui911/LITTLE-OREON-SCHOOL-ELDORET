#!/usr/bin/env python3
import argparse
import json
import logging
import re
import sqlite3
from contextlib import closing
from datetime import date, datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT / "Little Oriin Website" / "LITTLE OREON SITE_FINAL"
DATABASE_PATH = Path(__file__).resolve().parent / "admissions.sqlite3"
MAX_BODY_BYTES = 16 * 1024
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^[+()\d.\-\s]{7,30}$")


def initialize_database(database_path):
    database_path = Path(database_path)
    database_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    database_path.parent.chmod(0o700)

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS admissions (
                id INTEGER PRIMARY KEY,
                learner_name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                requested_class TEXT NOT NULL,
                previous_school TEXT NOT NULL,
                guardian_name TEXT NOT NULL,
                guardian_relationship TEXT NOT NULL,
                guardian_email TEXT NOT NULL,
                guardian_phone TEXT NOT NULL,
                guardian_consent INTEGER NOT NULL CHECK (guardian_consent = 1),
                submitted_at TEXT NOT NULL
            )
            """
        )
        connection.commit()

    database_path.chmod(0o600)


def validate_admission(data):
    if not isinstance(data, dict):
        raise ValueError("Please submit a valid admission form.")

    fields = {
        "learnerName": 120,
        "dateOfBirth": 10,
        "requestedClass": 80,
        "previousSchool": 120,
        "guardianName": 120,
        "guardianRelationship": 60,
        "guardianEmail": 254,
        "guardianPhone": 30,
    }
    if set(data) != set(fields) | {"guardianConsent"}:
        raise ValueError("The admission form contains unexpected or missing fields.")

    values = {}
    for field, max_length in fields.items():
        value = data[field]
        if not isinstance(value, str):
            raise ValueError("Please check the admission form fields.")
        value = value.strip()
        if len(value) > max_length:
            raise ValueError("One or more admission form fields are too long.")
        values[field] = value

    required_fields = (
        "learnerName",
        "dateOfBirth",
        "requestedClass",
        "guardianName",
        "guardianRelationship",
        "guardianEmail",
        "guardianPhone",
    )
    if any(not values[field] for field in required_fields):
        raise ValueError("Please complete all required admission form fields.")

    try:
        parsed_date = date.fromisoformat(values["dateOfBirth"])
    except ValueError as error:
        raise ValueError("Please enter a valid learner date of birth.") from error
    if parsed_date.isoformat() != values["dateOfBirth"] or parsed_date > date.today():
        raise ValueError("Please enter a valid learner date of birth.")

    if not EMAIL_PATTERN.fullmatch(values["guardianEmail"]):
        raise ValueError("Please enter a valid guardian email address.")
    if (
        not PHONE_PATTERN.fullmatch(values["guardianPhone"])
        or not any(character.isdigit() for character in values["guardianPhone"])
    ):
        raise ValueError("Please enter a valid guardian phone number.")
    if data["guardianConsent"] is not True:
        raise ValueError("Parent or guardian consent is required.")

    return values


def save_admission(database_path, values):
    submitted_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO admissions (
                    learner_name, date_of_birth, requested_class, previous_school,
                    guardian_name, guardian_relationship, guardian_email,
                    guardian_phone, guardian_consent, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    values["learnerName"],
                    values["dateOfBirth"],
                    values["requestedClass"],
                    values["previousSchool"],
                    values["guardianName"],
                    values["guardianRelationship"],
                    values["guardianEmail"],
                    values["guardianPhone"],
                    1,
                    submitted_at,
                ),
            )


def make_handler(database_path, site_directory):
    class AdmissionsRequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(site_directory), **kwargs)

        def send_json(self, status, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path != "/api/admissions":
                self.send_json(404, {"error": "Not found."})
                return

            if self.headers.get_content_type() != "application/json":
                self.send_json(415, {"error": "Expected a JSON admission form."})
                return

            try:
                body_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_json(400, {"error": "Invalid request length."})
                return

            if body_length < 1 or body_length > MAX_BODY_BYTES:
                self.send_json(413, {"error": "Admission form submission is too large."})
                return

            try:
                data = json.loads(self.rfile.read(body_length).decode("utf-8"))
                values = validate_admission(data)
            except (UnicodeDecodeError, json.JSONDecodeError):
                self.send_json(400, {"error": "Please submit a valid admission form."})
                return
            except ValueError as error:
                self.send_json(400, {"error": str(error)})
                return

            try:
                save_admission(database_path, values)
            except sqlite3.Error:
                logging.exception("Could not save an admission submission")
                self.send_json(500, {"error": "Unable to save the admission enquiry."})
                return

            self.send_json(201, {"message": "Admission enquiry received."})

    return AdmissionsRequestHandler


def main():
    parser = argparse.ArgumentParser(description="Run the local admissions form and SQLite API.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    initialize_database(DATABASE_PATH)
    server = ThreadingHTTPServer(
        ("127.0.0.1", args.port),
        make_handler(DATABASE_PATH, SITE_DIR),
    )
    print(f"Local admissions site: http://127.0.0.1:{server.server_port}")
    print(f"Local admissions database: {DATABASE_PATH}")
    server.serve_forever()


if __name__ == "__main__":
    main()
