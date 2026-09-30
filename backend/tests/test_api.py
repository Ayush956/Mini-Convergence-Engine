"""End-to-end tests for POST /api/reading.

These run without an OpenRouter key, so the summary comes from the template
path. That is deliberate: the suite must not depend on a network call or burn
credit from a capped key.
"""

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.engine.summary import SOURCE_TEMPLATE
from app.engine.traits import TRAITS
from app.main import app
from app.models import EARLIEST_YEAR

client = TestClient(app)

VALID = {
    "full_name": "Ayush Mishra",
    "date_of_birth": "1995-08-15",
    "time_of_birth": "10:30",
}


def post(**overrides):
    body = dict(VALID)
    body.update(overrides)
    return client.post("/api/reading", json=body)


def test_happy_path_returns_all_five_methods():
    response = post()
    assert response.status_code == 200

    body = response.json()
    assert [method["id"] for method in body["methods"]] == [
        "sun_sign",
        "chinese_zodiac",
        "life_path",
        "name_number",
        "vara",
    ]


def test_known_answers_for_the_sample_input():
    body = post().json()
    results = {method["id"]: method["result"] for method in body["methods"]}

    assert results["sun_sign"] == "Leo"
    assert results["chinese_zodiac"] == "Pig"
    assert results["life_path"] == "2"
    assert results["name_number"] == "5"
    assert results["vara"].startswith("Mangalavara")


def test_every_method_scores_every_trait():
    """The brief requires a 6x5 matrix with every score visible, so the
    response must actually contain 30 scores."""
    body = post().json()

    total = 0
    for method in body["methods"]:
        assert set(method["scores"]) == set(TRAITS), method["id"]
        for value in method["scores"].values():
            assert 0 <= value <= 10
            total += 1
    assert total == 30


def test_trait_rows_cover_the_six_dimensions_in_order():
    body = post().json()
    assert [row["trait"] for row in body["traits"]] == list(TRAITS)


def test_convergence_is_internally_consistent():
    """N must equal the number of scores at or above 7, and the confidence
    must match N. Guards against the two being computed independently."""
    body = post().json()

    for row in body["traits"]:
        expected_agreeing = sorted(
            method for method, score in row["scores"].items() if score >= 7
        )
        assert row["agreeing"] == expected_agreeing, row["trait"]
        assert row["n"] == len(expected_agreeing)
        assert abs(row["confidence"] - (1 - 1 / (2 ** row["n"]))) < 1e-9
        assert 0 <= row["n"] <= 5


def test_matrix_scores_match_the_per_method_scores():
    """The same numbers must appear in both views, or the UI would show a
    method one score in its card and a different one in the matrix."""
    body = post().json()
    per_method = {method["id"]: method["scores"] for method in body["methods"]}

    for row in body["traits"]:
        for method_id, score in row["scores"].items():
            assert per_method[method_id][row["trait"]] == score


def test_summary_falls_back_to_the_template_without_a_key():
    body = post().json()
    assert body["summary_source"] == SOURCE_TEMPLATE
    assert len(body["summary"]) > 80
    assert "Ayush Mishra" in body["summary"]


def test_methods_carry_their_reasoning():
    body = post().json()
    for method in body["methods"]:
        assert method["detail"], method["id"]
        assert method["basis"], method["id"]


def test_assumptions_always_mention_the_timezone():
    body = post().json()
    assert any("IST" in note for note in body["assumptions"])


# --------------------------------------------------------------------------
# Edge cases. The brief calls these out and grades them.
# --------------------------------------------------------------------------


def test_birth_before_sunrise_reports_the_vara_shift():
    body = post(time_of_birth="02:00").json()

    assert body["methods"][4]["result"].startswith("Somavara")
    assert any("sunrise" in note for note in body["assumptions"])


def test_birth_before_chinese_new_year_reports_the_year_boundary():
    """1 Jan 2000 is still the Rabbit, because New Year was 5 February."""
    body = post(date_of_birth="2000-01-01").json()

    results = {method["id"]: method["result"] for method in body["methods"]}
    assert results["chinese_zodiac"] == "Rabbit"
    assert any("Chinese New Year" in note for note in body["assumptions"])


def test_cusp_birth_is_flagged_in_the_assumptions():
    body = post(date_of_birth="2024-03-20", time_of_birth="08:40").json()

    results = {method["id"]: method["result"] for method in body["methods"]}
    assert results["sun_sign"] == "Aries"
    assert any("cusp" in note for note in body["assumptions"])


def test_name_with_punctuation_reports_what_was_ignored():
    body = post(full_name="O'Brien-Smith").json()
    assert any("ignored" in note for note in body["assumptions"])


def test_accented_name_is_accepted():
    response = post(full_name="José Álvarez")
    assert response.status_code == 200


def test_leap_day_birth_is_accepted():
    response = post(date_of_birth="2000-02-29")
    assert response.status_code == 200


def test_midnight_birth_is_accepted_and_shifts_the_vara():
    """15 Aug 1995 was a Tuesday, so 00:00 falls back to Monday's vara."""
    midnight = post(time_of_birth="00:00").json()
    midday = post(time_of_birth="12:00").json()

    assert midnight["methods"][4]["result"] == "Somavara (Moon)"
    assert midday["methods"][4]["result"] == "Mangalavara (Mars)"
    assert any("sunrise" in note for note in midnight["assumptions"])
    assert not any("sunrise" in note for note in midday["assumptions"])


def test_master_number_life_path_is_preserved():
    body = post(date_of_birth="1950-01-04").json()
    results = {method["id"]: method["result"] for method in body["methods"]}
    assert results["life_path"] == "11"


# --------------------------------------------------------------------------
# Invalid input: clear messages, never a crash or a raw Pydantic payload.
# --------------------------------------------------------------------------


def test_empty_name_is_rejected_with_a_readable_message():
    response = post(full_name="   ")
    assert response.status_code == 422

    body = response.json()
    assert body["message"] == "Please enter a name."
    assert body["field"] == "full_name"


def test_name_without_letters_is_rejected_with_a_readable_message():
    response = post(full_name="123 !!!")
    assert response.status_code == 422
    assert "letter" in response.json()["message"]


def test_overlong_name_is_rejected():
    response = post(full_name="A" * 200)
    assert response.status_code == 422
    assert "120" in response.json()["message"]


def test_date_before_the_supported_range_is_rejected_clearly():
    response = post(date_of_birth="1850-01-01")
    assert response.status_code == 422

    body = response.json()
    assert str(EARLIEST_YEAR) in body["message"]
    assert body["field"] == "date_of_birth"


def test_future_date_of_birth_is_rejected_clearly():
    tomorrow = date.today() + timedelta(days=1)
    response = post(date_of_birth=tomorrow.isoformat())
    assert response.status_code == 422

    body = response.json()
    assert "future" in body["message"]
    assert body["field"] == "date_of_birth"


def test_far_future_date_is_rejected_as_future_not_as_out_of_range():
    """2200 is both in the future and past the calendar table. The future
    message is the useful one, so it has to win."""
    assert "future" in post(date_of_birth="2200-01-01").json()["message"]


def test_malformed_date_is_rejected_without_a_stack_trace():
    response = post(date_of_birth="not-a-date")
    assert response.status_code == 422
    assert isinstance(response.json()["message"], str)


def test_malformed_time_is_rejected_without_a_stack_trace():
    response = post(time_of_birth="99:99")
    assert response.status_code == 422
    assert isinstance(response.json()["message"], str)


def test_missing_field_is_rejected():
    response = client.post("/api/reading", json={"full_name": "Ayush"})
    assert response.status_code == 422
    assert isinstance(response.json()["message"], str)


def test_error_shape_is_always_message_and_field():
    """The UI relies on this, so no error path may return Pydantic's default
    nested payload."""
    for body in (
        {"full_name": "  ", "date_of_birth": "1995-08-15", "time_of_birth": "10:30"},
        {"full_name": "Ayush", "date_of_birth": "1800-01-01", "time_of_birth": "10:30"},
        {"full_name": "Ayush", "date_of_birth": "bad", "time_of_birth": "10:30"},
        {},
    ):
        response = client.post("/api/reading", json=body)
        assert response.status_code == 422
        payload = response.json()
        assert set(payload) == {"message", "field"}
        assert isinstance(payload["message"], str) and payload["message"]


def test_both_ends_of_the_usable_range_work():
    """The first year we have calendar data for, and today."""
    assert post(date_of_birth="{}-06-15".format(EARLIEST_YEAR)).status_code == 200
    assert post(date_of_birth=date.today().isoformat()).status_code == 200


def test_health_still_works():
    assert client.get("/health").json() == {"status": "ok"}
