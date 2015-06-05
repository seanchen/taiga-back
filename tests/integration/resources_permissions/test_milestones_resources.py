from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.projects.milestones.serializers import MilestoneSerializer
from taiga.projects.milestones.models import Milestone
from taiga.permissions.permissions import MEMBERS_PERMISSIONS, ANON_PERMISSIONS, USER_PERMISSIONS

from tests import factories as f
from tests.utils import helper_test_http_method, disconnect_signals, reconnect_signals

import pytest
pytestmark = pytest.mark.django_db


def setup_module(module):
    disconnect_signals()


def teardown_module(module):
    reconnect_signals()


@pytest.fixture
def data():
    m = type("Models", (object,), {})

    m.registered_user = f.UserFactory.create()
    m.project_member_with_perms = f.UserFactory.create()
    m.project_member_without_perms = f.UserFactory.create()
    m.project_owner = f.UserFactory.create()
    m.other_user = f.UserFactory.create()

    m.public_project = f.ProjectFactory(is_private=False,
                                        anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                        public_permissions=list(map(lambda x: x[0], USER_PERMISSIONS)),
                                        owner=m.project_owner)
    m.private_project1 = f.ProjectFactory(is_private=True,
                                          anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                          public_permissions=list(map(lambda x: x[0], USER_PERMISSIONS)),
                                          owner=m.project_owner)
    m.private_project2 = f.ProjectFactory(is_private=True,
                                          anon_permissions=[],
                                          public_permissions=[],
                                          owner=m.project_owner)

    m.public_membership = f.MembershipFactory(project=m.public_project,
                                              user=m.project_member_with_perms,
                                              role__project=m.public_project,
                                              role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    m.private_membership1 = f.MembershipFactory(project=m.private_project1,
                                                user=m.project_member_with_perms,
                                                role__project=m.private_project1,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=m.private_project1,
                        user=m.project_member_without_perms,
                        role__project=m.private_project1,
                        role__permissions=[])
    m.private_membership2 = f.MembershipFactory(project=m.private_project2,
                                                user=m.project_member_with_perms,
                                                role__project=m.private_project2,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=m.private_project2,
                        user=m.project_member_without_perms,
                        role__project=m.private_project2,
                        role__permissions=[])

    f.MembershipFactory(project=m.public_project,
                        user=m.project_owner,
                        is_owner=True)

    f.MembershipFactory(project=m.private_project1,
                        user=m.project_owner,
                        is_owner=True)

    f.MembershipFactory(project=m.private_project2,
                        user=m.project_owner,
                        is_owner=True)

    m.public_milestone = f.MilestoneFactory(project=m.public_project)
    m.private_milestone1 = f.MilestoneFactory(project=m.private_project1)
    m.private_milestone2 = f.MilestoneFactory(project=m.private_project2)

    return m


def test_milestone_retrieve(client, data):
    public_url = reverse('milestones-detail', kwargs={"pk": data.public_milestone.pk})
    private_url1 = reverse('milestones-detail', kwargs={"pk": data.private_milestone1.pk})
    private_url2 = reverse('milestones-detail', kwargs={"pk": data.private_milestone2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private_url1, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private_url2, None, users)
    assert results == [401, 403, 403, 200, 200]


def test_milestone_update(client, data):
    public_url = reverse('milestones-detail', kwargs={"pk": data.public_milestone.pk})
    private_url1 = reverse('milestones-detail', kwargs={"pk": data.private_milestone1.pk})
    private_url2 = reverse('milestones-detail', kwargs={"pk": data.private_milestone2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    milestone_data = MilestoneSerializer(data.public_milestone).data
    milestone_data["name"] = "test"
    milestone_data = json.dumps(milestone_data)
    results = helper_test_http_method(client, 'put', public_url, milestone_data, users)
    assert results == [401, 403, 403, 200, 200]

    milestone_data = MilestoneSerializer(data.private_milestone1).data
    milestone_data["name"] = "test"
    milestone_data = json.dumps(milestone_data)
    results = helper_test_http_method(client, 'put', private_url1, milestone_data, users)
    assert results == [401, 403, 403, 200, 200]

    milestone_data = MilestoneSerializer(data.private_milestone2).data
    milestone_data["name"] = "test"
    milestone_data = json.dumps(milestone_data)
    results = helper_test_http_method(client, 'put', private_url2, milestone_data, users)
    assert results == [401, 403, 403, 200, 200]


def test_milestone_delete(client, data):
    public_url = reverse('milestones-detail', kwargs={"pk": data.public_milestone.pk})
    private_url1 = reverse('milestones-detail', kwargs={"pk": data.private_milestone1.pk})
    private_url2 = reverse('milestones-detail', kwargs={"pk": data.private_milestone2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
    ]
    results = helper_test_http_method(client, 'delete', public_url, None, users)
    assert results == [401, 403, 403, 204]
    results = helper_test_http_method(client, 'delete', private_url1, None, users)
    assert results == [401, 403, 403, 204]
    results = helper_test_http_method(client, 'delete', private_url2, None, users)
    assert results == [401, 403, 403, 204]


def test_milestone_list(client, data):
    url = reverse('milestones-list')

    response = client.get(url)
    milestones_data = json.loads(response.content.decode('utf-8'))
    assert len(milestones_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)

    response = client.get(url)
    milestones_data = json.loads(response.content.decode('utf-8'))
    assert len(milestones_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)

    response = client.get(url)
    milestones_data = json.loads(response.content.decode('utf-8'))
    assert len(milestones_data) == 3
    assert response.status_code == 200

    client.login(data.project_owner)

    response = client.get(url)
    milestones_data = json.loads(response.content.decode('utf-8'))
    assert len(milestones_data) == 3
    assert response.status_code == 200


def test_milestone_create(client, data):
    url = reverse('milestones-list')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    create_data = json.dumps({
        "name": "test",
        "estimated_start": "2014-12-10",
        "estimated_finish": "2014-12-24",
        "project": data.public_project.pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users,
                                      lambda: Milestone.objects.all().delete())
    assert results == [401, 403, 403, 201, 201]

    create_data = json.dumps({
        "name": "test",
        "estimated_start": "2014-12-10",
        "estimated_finish": "2014-12-24",
        "project": data.private_project1.pk,
    })

    results = helper_test_http_method(client, 'post', url, create_data, users,
                                      lambda: Milestone.objects.all().delete())
    assert results == [401, 403, 403, 201, 201]

    create_data = json.dumps({
        "name": "test",
        "estimated_start": "2014-12-10",
        "estimated_finish": "2014-12-24",
        "project": data.private_project2.pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users, lambda: Milestone.objects.all().delete())
    assert results == [401, 403, 403, 201, 201]


def test_milestone_patch(client, data):
    public_url = reverse('milestones-detail', kwargs={"pk": data.public_milestone.pk})
    private_url1 = reverse('milestones-detail', kwargs={"pk": data.private_milestone1.pk})
    private_url2 = reverse('milestones-detail', kwargs={"pk": data.private_milestone2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    patch_data = json.dumps({"name": "test"})
    results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
    assert results == [401, 403, 403, 200, 200]

    patch_data = json.dumps({"name": "test"})
    results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
    assert results == [401, 403, 403, 200, 200]

    patch_data = json.dumps({"name": "test"})
    results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
    assert results == [401, 403, 403, 200, 200]


def test_milestone_action_stats(client, data):
    public_url = reverse('milestones-stats', kwargs={"pk": data.public_milestone.pk})
    private_url1 = reverse('milestones-stats', kwargs={"pk": data.private_milestone1.pk})
    private_url2 = reverse('milestones-stats', kwargs={"pk": data.private_milestone2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [200, 200, 200, 200, 200]

    results = helper_test_http_method(client, 'get', private_url1, None, users)
    assert results == [200, 200, 200, 200, 200]

    results = helper_test_http_method(client, 'get', private_url2, None, users)
    assert results == [401, 403, 403, 200, 200]
