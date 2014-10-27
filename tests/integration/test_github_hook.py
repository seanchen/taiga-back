import pytest
import json

from unittest import mock

from django.core.urlresolvers import reverse

from taiga.github_hook.api import GitHubViewSet
from taiga.github_hook import event_hooks
from taiga.github_hook.exceptions import ActionSyntaxException
from taiga.projects.issues.models import Issue
from taiga.projects.tasks.models import Task
from taiga.projects.userstories.models import UserStory

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_bad_signature(client):
    project=f.ProjectFactory()
    url = reverse("github-hook-list")
    url = "%s?project=%s"%(url, project.id)
    data = {}
    response = client.post(url, json.dumps(data),
        HTTP_X_HUB_SIGNATURE="sha1=badbadbad",
        content_type="application/json")
    response_content = json.loads(response.content.decode("utf-8"))
    assert response.status_code == 401
    assert "Bad signature" in response_content["_error_message"]


def test_ok_signature(client):
    project=f.ProjectFactory()
    github_hook_attributes = f.GitHubHookAttributesFactory(project=project,
        secret="tpnIwJDz4e")
    url = reverse("github-hook-list")
    url = "%s?project=%s"%(url, project.id)
    data = {"test:": "data"}
    response = client.post(url, json.dumps(data),
        HTTP_X_HUB_SIGNATURE="sha1=3c8e83fdaa266f81c036ea0b71e98eb5e054581a",
        content_type="application/json")

    assert response.status_code == 200


def test_push_event_detected(client):
    project=f.ProjectFactory()
    url = reverse("github-hook-list")
    url = "%s?project=%s"%(url, project.id)
    data = {"commits": [
      {"message": "test message"},
    ]}

    GitHubViewSet._validate_signature = mock.Mock(return_value=True)

    with mock.patch.object(event_hooks.PushEventHook, "process_event") as process_event_mock:
        response = client.post(url, json.dumps(data),
            HTTP_X_GITHUB_EVENT="push",
            content_type="application/json")

        assert process_event_mock.call_count == 1

    assert response.status_code == 200


def test_push_event_issue_processing(client):
    creation_status = f.IssueStatusFactory()
    new_status = f.IssueStatusFactory(project=creation_status.project)
    issue = f.IssueFactory.create(status=creation_status, project=creation_status.project)
    payload = {"commits": [
        {"message": """test message
            test   TG-%s    #%s   ok
            bye!
        """%(issue.ref, new_status.slug)},
    ]}
    ev_hook = event_hooks.PushEventHook(issue.project, payload)
    ev_hook.process_event()
    issue = Issue.objects.get(id=issue.id)
    assert issue.status.id == new_status.id


def test_push_event_task_processing(client):
    creation_status = f.TaskStatusFactory()
    new_status = f.TaskStatusFactory(project=creation_status.project)
    task = f.TaskFactory.create(status=creation_status, project=creation_status.project)
    payload = {"commits": [
        {"message": """test message
            test   TG-%s    #%s   ok
            bye!
        """%(task.ref, new_status.slug)},
    ]}
    ev_hook = event_hooks.PushEventHook(task.project, payload)
    ev_hook.process_event()
    task = Task.objects.get(id=task.id)
    assert task.status.id == new_status.id


def test_push_event_user_story_processing(client):
    creation_status = f.UserStoryStatusFactory()
    new_status = f.UserStoryStatusFactory(project=creation_status.project)
    user_story = f.UserStoryFactory.create(status=creation_status, project=creation_status.project)
    payload = {"commits": [
        {"message": """test message
            test   TG-%s    #%s   ok
            bye!
        """%(user_story.ref, new_status.slug)},
    ]}
    ev_hook = event_hooks.PushEventHook(user_story.project, payload)
    ev_hook.process_event()
    user_story = UserStory.objects.get(id=user_story.id)
    assert user_story.status.id == new_status.id


def test_push_event_bad_processing_non_existing_ref(client):
    issue_status = f.IssueStatusFactory()
    payload = {"commits": [
        {"message": """test message
            test   TG-6666666    #%s   ok
            bye!
        """%(issue_status.slug)},
    ]}
    ev_hook = event_hooks.PushEventHook(issue_status.project, payload)
    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "The referenced element doesn't exist"


def test_push_event_bad_processing_non_existing_status(client):
    issue = f.IssueFactory.create()
    payload = {"commits": [
        {"message": """test message
            test   TG-%s    #non-existing-slug   ok
            bye!
        """%(issue.ref)},
    ]}
    ev_hook = event_hooks.PushEventHook(issue.project, payload)
    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "The status doesn't exist"

def test_issues_event_opened_issue(client):
    issue = f.IssueFactory.create()
    issue.project.default_issue_status = issue.status
    issue.project.default_issue_type = issue.type
    issue.project.default_severity = issue.severity
    issue.project.default_priority = issue.priority
    issue.project.save()

    payload = {
        "action": "opened",
        "issue": {
            "title": "test-title",
            "body": "test-body",
            "number": 10,
        },
        "assignee": {},
        "label": {},
    }
    ev_hook = event_hooks.IssuesEventHook(issue.project, payload)
    ev_hook.process_event()

    assert Issue.objects.count() == 2

def test_issues_event_other_than_opened_issue(client):
    issue = f.IssueFactory.create()
    issue.project.default_issue_status = issue.status
    issue.project.default_issue_type = issue.type
    issue.project.default_severity = issue.severity
    issue.project.default_priority = issue.priority
    issue.project.save()

    payload = {
        "action": "closed",
        "issue": {
            "title": "test-title",
            "body": "test-body",
            "number": 10,
        },
        "assignee": {},
        "label": {},
    }
    ev_hook = event_hooks.IssuesEventHook(issue.project, payload)
    ev_hook.process_event()

    assert Issue.objects.count() == 1

def test_issues_event_bad_issue(client):
    issue = f.IssueFactory.create()
    issue.project.default_issue_status = issue.status
    issue.project.default_issue_type = issue.type
    issue.project.default_severity = issue.severity
    issue.project.default_priority = issue.priority
    issue.project.save()

    payload = {
        "action": "opened",
        "issue": {},
        "assignee": {},
        "label": {},
    }
    ev_hook = event_hooks.IssuesEventHook(issue.project, payload)

    with pytest.raises(ActionSyntaxException) as excinfo:
        ev_hook.process_event()

    assert str(excinfo.value) == "Invalid issue information"

    assert Issue.objects.count() == 1
