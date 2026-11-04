from __future__ import annotations

from sentry.seer.entrypoints.slack.out_of_credits import (
    OUT_OF_CREDITS_MESSAGE,
    REQUEST_CREDITS_LINK_TEXT,
    REQUEST_CREDITS_PROMPT,
    TOP_UP_LINK_TEXT,
    TOP_UP_PROMPT,
    can_manage_billing,
    format_out_of_credits_mrkdwn,
    get_seer_credits_link,
)
from sentry.testutils.cases import TestCase


class SeerCreditsLinkTest(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.organization = self.create_organization(owner=self.user)

    def _member(self, role: str) -> int:
        user = self.create_user()
        self.create_member(organization=self.organization, user=user, role=role)
        return user.id

    def test_owner_and_billing_can_manage_billing(self) -> None:
        assert can_manage_billing(self.organization, self.user.id)
        assert can_manage_billing(self.organization, self._member("billing"))

    def test_other_roles_cannot_manage_billing(self) -> None:
        for role in ("member", "admin", "manager"):
            assert not can_manage_billing(self.organization, self._member(role))

    def test_unknown_user_cannot_manage_billing(self) -> None:
        assert not can_manage_billing(self.organization, None)
        assert not can_manage_billing(self.organization, self.create_user().id)

    def test_top_up_link_for_billing_member(self) -> None:
        link = get_seer_credits_link(self.organization, self.user.id)
        assert link.can_top_up
        assert link.text == TOP_UP_LINK_TEXT
        assert link.prompt == TOP_UP_PROMPT
        assert f"/settings/{self.organization.slug}/billing/overview/" in link.url
        assert "referrer=slack-seer-credits" in link.url

    def test_request_link_for_other_member(self) -> None:
        link = get_seer_credits_link(self.organization, self._member("member"))
        assert not link.can_top_up
        assert link.text == REQUEST_CREDITS_LINK_TEXT
        assert link.prompt == REQUEST_CREDITS_PROMPT
        assert f"/settings/{self.organization.slug}/billing/overview/" in link.url

    def test_request_link_without_user(self) -> None:
        assert not get_seer_credits_link(self.organization, None).can_top_up

    def test_format_mrkdwn(self) -> None:
        link = get_seer_credits_link(self.organization, self.user.id)
        assert format_out_of_credits_mrkdwn(link) == (
            f"{OUT_OF_CREDITS_MESSAGE} {TOP_UP_PROMPT} <{link.url}|{TOP_UP_LINK_TEXT}>"
        )
