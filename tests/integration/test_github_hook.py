import pytest
import json

from unittest import mock

from django.core.urlresolvers import reverse

from taiga.github_hook.api import GitHubViewSet
from taiga.github_hook.event_hooks import PushEventHook

pytestmark = pytest.mark.django_db


def test_bad_signature(client):
    url = reverse("github-hook-list")
    data = {}
    response = client.post(url, json.dumps(data), content_type="application/json")
    response_content = json.loads(response.content.decode("utf-8"))
    assert response.status_code == 401
    assert "Bad signature" in response_content["_error_message"]


def test_ok_signature(client):
    url = reverse("github-hook-list")
    data = {"test:": "data"}
    response = client.post(url, json.dumps(data),
        HTTP_X_HUB_SIGNATURE="sha1=3c8e83fdaa266f81c036ea0b71e98eb5e054581a",
        content_type="application/json")

    assert response.status_code == 200


def test_push_event_detected(client):
    url = reverse("github-hook-list")
    data = {"commits:": [
      {"message": "test message"},
    ]}

    GitHubViewSet._validate_signature = mock.Mock(return_value=True)

    with mock.patch.object(PushEventHook, "process_event") as process_event_mock:
        response = client.post(url, json.dumps(data),
            HTTP_X_GITHUB_EVENT="push",
            content_type="application/json")

        # mock.assert_called_once_with(json.dumps(data))
        assert process_event_mock.call_count == 1

    assert response.status_code == 200
