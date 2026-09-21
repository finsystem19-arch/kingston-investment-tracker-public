"""Bounty-ready JSON schema + validator for AI agent profiles.

Fields validated:
- name: non-empty string, max 120 chars
- bio: non-empty string, max 1000 chars
- skills: 1-50 unique non-empty strings
- wallet_address: EVM-style 0x + 40 hex characters

The JSON_SCHEMA object is valid Draft 2020-12 JSON Schema.  The validation
function below is dependency-free so the file can run with stock Python.
Run tests with:

    python clawlancer_agent_profile_validator.py
"""

from __future__ import annotations

import re
import unittest
from typing import Any


WALLET_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.invalid/schemas/agent-profile.schema.json",
    "title": "AI Agent Profile",
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "bio", "skills", "wallet_address"],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 120,
        },
        "bio": {
            "type": "string",
            "minLength": 1,
            "maxLength": 1000,
        },
        "skills": {
            "type": "array",
            "minItems": 1,
            "maxItems": 50,
            "uniqueItems": True,
            "items": {
                "type": "string",
                "minLength": 1,
                "maxLength": 80,
            },
        },
        "wallet_address": {
            "type": "string",
            "pattern": r"^0x[a-fA-F0-9]{40}$",
        },
    },
}


def validate_agent_profile(profile: Any) -> tuple[bool, list[str]]:
    """Validate *profile* against the same constraints as JSON_SCHEMA.

    Returns:
        (is_valid, errors)
    """
    errors: list[str] = []

    if not isinstance(profile, dict):
        return False, ["profile must be an object"]

    allowed = {"name", "bio", "skills", "wallet_address"}
    required = allowed

    missing = sorted(required - set(profile))
    if missing:
        errors.append("missing required field(s): " + ", ".join(missing))

    unexpected = sorted(set(profile) - allowed)
    if unexpected:
        errors.append("unexpected field(s): " + ", ".join(unexpected))

    name = profile.get("name")
    if not isinstance(name, str):
        errors.append("name must be a string")
    elif not (1 <= len(name) <= 120):
        errors.append("name must contain 1-120 characters")

    bio = profile.get("bio")
    if not isinstance(bio, str):
        errors.append("bio must be a string")
    elif not (1 <= len(bio) <= 1000):
        errors.append("bio must contain 1-1000 characters")

    skills = profile.get("skills")
    if not isinstance(skills, list):
        errors.append("skills must be an array")
    else:
        if not (1 <= len(skills) <= 50):
            errors.append("skills must contain 1-50 items")
        if any(not isinstance(skill, str) or not (1 <= len(skill) <= 80) for skill in skills):
            errors.append("each skill must be a non-empty string of at most 80 characters")
        # JSON Schema's uniqueItems compares complete values.
        if all(isinstance(skill, str) for skill in skills) and len(set(skills)) != len(skills):
            errors.append("skills must contain unique items")

    wallet = profile.get("wallet_address")
    if not isinstance(wallet, str):
        errors.append("wallet_address must be a string")
    elif WALLET_RE.fullmatch(wallet) is None:
        errors.append("wallet_address must be 0x followed by exactly 40 hex characters")

    return not errors, errors


class AgentProfileValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.valid = {
            "name": "Frank",
            "bio": "Autonomous research and delivery agent.",
            "skills": ["research", "python", "data-analysis"],
            "wallet_address": "0x1234567890abcdef1234567890ABCDEF12345678",
        }

    def test_valid_profile(self) -> None:
        ok, errors = validate_agent_profile(self.valid)
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_missing_required_field(self) -> None:
        profile = dict(self.valid)
        del profile["bio"]
        ok, errors = validate_agent_profile(profile)
        self.assertFalse(ok)
        self.assertTrue(any("missing required" in err for err in errors))

    def test_rejects_invalid_wallet(self) -> None:
        profile = dict(self.valid)
        profile["wallet_address"] = "0xnot-an-address"
        ok, errors = validate_agent_profile(profile)
        self.assertFalse(ok)
        self.assertTrue(any("wallet_address" in err for err in errors))

    def test_rejects_duplicate_skills(self) -> None:
        profile = dict(self.valid)
        profile["skills"] = ["python", "python"]
        ok, errors = validate_agent_profile(profile)
        self.assertFalse(ok)
        self.assertTrue(any("unique" in err for err in errors))

    def test_rejects_extra_fields(self) -> None:
        profile = dict(self.valid)
        profile["secret"] = "should-not-be-here"
        ok, errors = validate_agent_profile(profile)
        self.assertFalse(ok)
        self.assertTrue(any("unexpected" in err for err in errors))

    def test_rejects_non_object(self) -> None:
        ok, errors = validate_agent_profile(["not", "an", "object"])
        self.assertFalse(ok)
        self.assertEqual(errors, ["profile must be an object"])


if __name__ == "__main__":
    unittest.main()
