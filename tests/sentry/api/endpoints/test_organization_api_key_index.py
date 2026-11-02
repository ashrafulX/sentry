from django.test import override_settings
from django.urls import reverse

from sentry.testutils.cases import APITestCase
from sentry.testutils.helpers.features import with_feature
from sentry.testutils.silo import control_silo_test
from sentry.viewer_context import Actor, ActorType, ViewerContext, encode_viewer_context


@control_silo_test
class OrganizationApiKeyIndex(APITestCase):
    endpoint = "sentry-api-0-organization-api-key-index"

    def setUp(self) -> None:
        super().setUp()
        self.login_as(self.user)

    def test_org_admin_can_access(self) -> None:
        self.get_success_response(self.organization.slug)

    @override_settings(SEER_API_SHARED_SECRET="service-account-secret")
    @with_feature("organizations:service-accounts")
    def test_service_account_cannot_list_keys(self) -> None:
        service_account = self.create_service_account(
            organization=self.organization, scope_list=["org:admin"]
        )
        viewer_context = encode_viewer_context(
            ViewerContext(
                actor=Actor(type=ActorType.SERVICE_ACCOUNT, actor_id=service_account.id),
                organization_id=self.organization.id,
            ),
            key="service-account-secret",
        )

        response = self.client.get(
            reverse(self.endpoint, args=[self.organization.slug]),
            HTTP_X_VIEWER_CONTEXT=viewer_context,
        )

        assert response.status_code == 403, response.content
        assert response.data["detail"]["code"] == "user-required"

    def test_member_no_access(self) -> None:
        user = self.create_user("bar@example.com")
        self.create_member(organization=self.organization, user=user, role="member")

        self.login_as(user)
        self.get_error_response(self.organization.slug, status_code=403)

    def test_superuser_can_access(self) -> None:
        admin_user = self.create_user("admin@example.com", is_superuser=True)
        self.create_member(organization=self.organization, user=admin_user, role="admin")

        self.login_as(admin_user, superuser=True)
        self.get_success_response(self.organization.slug)
