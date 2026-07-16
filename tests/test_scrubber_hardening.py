"""redact_secrets hardening: HuggingFace tokens and single base64 (non-JWT)
credential blobs leaked into a seeded store because no pattern caught them.
Plus a few common sibling provider tokens. Guards against over-redaction.
"""
from __future__ import annotations

from cdms.store import redact_secrets

# The two SHAPES that leaked from a Claude Code history seed. SYNTHETIC stand-ins
# built from repeated chars: they match the scrubber regexes (hf_ prefix + len; a
# non-dotted eyJ base64 blob >=30) but carry no real entropy, so they are not real
# credentials and do not trip upstream secret-scanning push protection. (The original
# vectors here were real leaked tokens; do NOT paste live credentials into tests.)
_HF = "hf_" + "s" * 34
_CF = "eyJ" + "S" * 60


def _redacted(secret: str, text: str) -> bool:
    """The secret substring is gone AND a redaction marker is present."""
    out = redact_secrets(text)
    return secret not in out and "[REDACTED]" in out


def test_huggingface_token_redacted():
    assert _redacted(_HF, f"hint: my token is {_HF} for the gated model")


def test_cloudflare_style_blob_redacted():
    assert _redacted(_CF, f"cloudflared.exe service install {_CF}")


def test_gitlab_npm_digitalocean_redacted():
    assert _redacted("glpat-abc123DEF456ghi789JKL", "GITLAB_TOKEN=glpat-abc123DEF456ghi789JKL")
    assert _redacted("npm_" + "a" * 36, "//registry.npmjs.org/:_authToken=npm_" + "a" * 36)
    assert _redacted("dop_v1_" + "a" * 64, "doctl auth: dop_v1_" + "a" * 64)


def test_existing_patterns_still_redacted():
    # Regression: the hardening must not weaken prior coverage.
    assert _redacted("AKIAIOSFODNN7EXAMPLE", "aws key AKIAIOSFODNN7EXAMPLE here")
    assert _redacted("sk-" + "A" * 40, "OPENAI=sk-" + "A" * 40)
    # A real three-part JWT (long segments) still goes through the JWT rule.
    jwt = "eyJ" + "a" * 20 + "." + "b" * 20 + "." + "c" * 20
    assert _redacted(jwt, f"Authorization: Bearer {jwt}")


def test_known_provider_tokens_redacted():
    hx = "0123456789abcdef"
    samples = {
        "AWS session":  "ASIA" + "ABCDEFGHIJ012345",            # ASIA + 16 [0-9A-Z]
        "Google OAuth": "ya29." + "a" * 40,
        "SendGrid":     "SG." + "a" * 22 + "." + "b" * 43,
        "Twilio SK":    "SK" + hx * 2,                          # SK + 32 hex
        "Mailgun":      "key-" + hx * 2,
        "Shopify":      "shpat_" + "a" * 32,
        "Square":       "sq0atp-" + "a" * 30,
        "Databricks":   "dapi" + hx * 3,                        # dapi + 48 hex
        "Notion":       "secret_" + "a" * 43,
        "Notion ntn":   "ntn_" + "a" * 45,
        "Supabase":     "sbp_" + "a" * 40,
        "Postman":      "PMAK-" + "0" * 24 + "-" + "1" * 34,
        "Doppler":      "dp.pt." + "a" * 44,
        "Linear":       "lin_api_" + "a" * 44,
        "Grafana":      "glc_" + "a" * 30,
        "Telegram":     "1234567890:AA" + "b" * 33,
    }
    for name, tok in samples.items():
        assert _redacted(tok, f"the {name} key is {tok} keep it safe"), name


def test_no_over_redaction():
    # A bare prefix / lookalike without a real token body must survive untouched.
    for benign in ("the hf_ prefix appears in docs",
                   "base64 fragment eyJshort here",        # < 30 chars after eyJ
                   "we merged the PR and ran the tests",
                   "ratio was 3:2 and the build was green",
                   "press the SK key on the keyboard",     # SK not + 32 hex
                   "the secret_config flag is set",        # secret_ but short
                   "store the api-key-value in env",       # key- but not 32 hex
                   "ya29 is a nice sequence",              # ya29 without .token
                   "at 12:34 the job ran",                 # time, not a Telegram token
                   "record 12345:abc in the log"):         # short id:val, not a token
        assert redact_secrets(benign) == benign, benign


def test_telegram_hardening_previously_leaking():
    # Red-team found the old `\d{8,10}:AA...{33}\b` rule LEAKED real tokens: the auth
    # part is arbitrary base64url (not always "AA"), bot ids exceed 10 digits, and the
    # exact {33}+\b failed on tokens ending in "-". The current rule catches all three.
    for tok in ("1234567890:BB" + "c" * 33,        # non-AA auth prefix
                "12345678901:AA" + "b" * 33,        # 11-digit bot id
                "1234567890:AA" + "b" * 32 + "-"):  # base64url ending in "-"
        assert _redacted(tok, f"bot token {tok} keep secret"), tok


def test_accepted_over_redaction_is_pinned():
    # DELIBERATE, security-conservative over-redaction (docs/DEVIATIONS.md O2). These
    # are NOT secrets but ARE redacted by prefix+shape rules. Pinned as known current
    # behavior so a future rule change is a conscious edit, not an accident.
    sourcemap = "data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoib3V0LmpzIn0="
    # Built from pieces / low entropy: match the scrubber's shape rules but are
    # obviously synthetic (no real secret literal committed to source).
    for benign_but_redacted in (
            sourcemap,                                       # inline JS sourcemap (base64 JSON)
            "ETag: key-" + "0" * 32,                         # key-<32hex> cache key (not Mailgun)
            "hash SK" + "0" * 32 + " here",                  # SK<32hex> (not a Twilio secret)
    ):
        assert "[REDACTED]" in redact_secrets(benign_but_redacted), benign_but_redacted


def test_true_non_secrets_survive():
    # Guard the OTHER direction: common high-entropy dev artifacts that must NOT trip.
    for safe in ("commit 9c18a1baed6c5f43e7cf5be3f5abc1234567890a",   # 40-hex git SHA
                 "id 684874ca-f9cc-4faa-a123-4567890abcde",           # UUID
                 "img data:image/png;base64,iVBORw0KGgoAAAANSUhEUg"): # PNG data URI
        assert redact_secrets(safe) == safe, safe


def test_redaction_is_idempotent():
    # _brief (seed) then _clip (ingest) can redact twice; the sentinel must not re-match.
    text = f"hf token {'a' * 34} and blob eyJ{'x' * 40} and key AKIAIOSFODNN7EXAMPLE"
    once = redact_secrets(text)
    assert redact_secrets(once) == once
