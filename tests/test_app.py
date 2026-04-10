import pytest

from src.app import activities


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code in {307, 308}
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    assert len(payload) == 9
    assert "Chess Club" in payload
    assert set(payload["Chess Club"].keys()) == {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }


def test_signup_successfully_registers_participant(client):
    email = "new.student@mergington.edu"

    response = client.post(f"/activities/Chess Club/signup?email={email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities["Chess Club"]["participants"]


def test_signup_rejects_unknown_activity(client):
    response = client.post("/activities/Unknown Activity/signup?email=test@mergington.edu")

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant(client):
    existing = activities["Chess Club"]["participants"][0]

    response = client.post(f"/activities/Chess Club/signup?email={existing}")

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_signup_currently_allows_empty_email(client):
    response = client.post("/activities/Chess Club/signup?email=")

    assert response.status_code == 200
    assert "" in activities["Chess Club"]["participants"]


def test_signup_activity_name_is_case_sensitive(client):
    response = client.post("/activities/chess%20club/signup?email=test@mergington.edu")

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_successfully_removes_participant(client):
    email = activities["Chess Club"]["participants"][0]

    response = client.delete(f"/activities/Chess Club/signup?email={email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete("/activities/Unknown Activity/signup?email=test@mergington.edu")

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_non_registered_participant(client):
    response = client.delete("/activities/Chess Club/signup?email=not.registered@mergington.edu")

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}


@pytest.mark.gap
@pytest.mark.xfail(reason="API does not enforce max participant capacity yet", strict=False)
def test_signup_should_reject_when_activity_is_full(client):
    activity = activities["Chess Club"]
    needed = activity["max_participants"] - len(activity["participants"])

    for i in range(needed):
        response = client.post(f"/activities/Chess Club/signup?email=fill{i}@mergington.edu")
        assert response.status_code == 200

    overflow_response = client.post("/activities/Chess Club/signup?email=overflow@mergington.edu")

    assert overflow_response.status_code == 400


@pytest.mark.gap
@pytest.mark.xfail(reason="API does not validate email format yet", strict=False)
def test_signup_should_reject_invalid_email_format(client):
    response = client.post("/activities/Chess Club/signup?email=not-an-email")

    assert response.status_code in {400, 422}
