import pytest
import json

from unittest import mock

from django.core.urlresolvers import reverse

from taiga.github_hook.api import GitHubViewSet
from taiga.github_hook.event_hooks import PushEventHook
from taiga.github_hook.exceptions import ActionSyntaxException
from taiga.projects.issues.models import Issue

from .. import factories as f

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
    data = {"commits": [
      {"message": "test message"},
    ]}

    GitHubViewSet._validate_signature = mock.Mock(return_value=True)

    with mock.patch.object(PushEventHook, "process_event") as process_event_mock:
        response = client.post(url, json.dumps(data),
            HTTP_X_GITHUB_EVENT="push",
            content_type="application/json")

        assert process_event_mock.call_count == 1

    assert response.status_code == 200


def test_push_event_processing(client):
    issue = f.IssueFactory.create()
    closed_status = f.IssueStatusFactory(is_closed=True, project=issue.project)
    payload = {"commits": [
        {"message": """test message
            test   TG-%s-%s    #close   ok
            bye!
        """%(issue.project.slug, issue.ref)},
    ]}
    ev_hook = PushEventHook(payload)
    ev_hook.process_event()
    issue = Issue.objects.get(id=issue.id)
    assert issue.status.is_closed is True


@pytest.mark.xfail(raises=ActionSyntaxException)
def test_push_event_bad_processing(client):
        issue = f.IssueFactory.create()
        payload = {"commits": [
            {"message": """test message
                test   TG-%s-%s    #close   ok
                bye!
            """%(issue.project.slug, issue.ref)},
        ]}
        ev_hook = PushEventHook(payload)
        ev_hook.process_event()
