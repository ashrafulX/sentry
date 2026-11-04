from __future__ import annotations

from unittest.mock import patch

from sentry.seer.entrypoints.slack.out_of_credits import (
    OUT_OF_CREDITS_MESSAGE,
    OUT_OF_CREDITS_NOT_STARTED_MESSAGE,
    REQUEST_CREDITS_LINK_TEXT,
    REQUEST_CREDITS_PROMPT,
    TOP_UP_LINK_TEXT,
    TOP_UP_PROMPT,
    can_manage_billing,
    format_out_of_credits_mrkdwn,
    get_seer_credits_link,
)
from sentry.testutils.cases import TestCase

# org:billing is a getsentry scope, so stub member scopes rather than rely on its roles.
GET_SCOPES = "sentry.seer.entrypoints.slack.out_of_credits.OrganizationMember.get_scopes"
BILLING_SCOPES = frozenset({"org:read", "org:billing"})
NON_BILLING_SCOPES = frozenset({"org:read", "org:write"})


class SeerCreditsLinkTest(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.organization = self.create_organization(owner=self.user)

    @patch(GET_SCOPES, return_value=BILLING_SCOPES)
    def test_billing_scope_can_manage_billing(self, _: object) -> None:
        assert can_manage_billing(self.organization, self.user.id)

    @patch(GET_SCOPES, return_value=NON_BILLING_SCOPES)
    def test_without_billing_scope_cannot_manage_billing(self, _: object) -> None:
        assert not can_manage_billing(self.organization, self.user.id)

    def test_unknown_user_cannot_manage_billing(self) -> None:
        assert not can_manage_billing(self.organization, None)
        assert not can_manage_billing(self.organization, self.create_user().id)

    @patch(GET_SCOPES, return_value=BILLING_SCOPES)
    def test_top_up_link_for_billing_member(self, _: object) -> None:
        link = get_seer_credits_link(self.organization, self.user.id)
        assert link.can_top_up
        assert link.text == TOP_UP_LINK_TEXT
        assert link.prompt == TOP_UP_PROMPT
        assert f"/settings/{self.organization.slug}/billing/overview/" in link.url
        assert "referrer=slack-seer-credits" in link.url

    @patch(GET_SCOPES, return_value=NON_BILLING_SCOPES)
    def test_request_link_for_other_member(self, _: object) -> None:
        link = get_seer_credits_link(self.organization, self.user.id)
        assert not link.can_top_up
        assert link.text == REQUEST_CREDITS_LINK_TEXT
        assert link.prompt == REQUEST_CREDITS_PROMPT
        assert f"/settings/{self.organization.slug}/billing/overview/" in link.url

    def test_request_link_without_user(self) -> None:
        assert not get_seer_credits_link(self.organization, None).can_top_up

    @patch(GET_SCOPES, return_value=BILLING_SCOPES)
    def test_format_mrkdwn(self, _: object) -> None:
        link = get_seer_credits_link(self.organization, self.user.id)
        assert format_out_of_credits_mrkdwn(link) == (
            f"{OUT_OF_CREDITS_MESSAGE} {TOP_UP_PROMPT} <{link.url}|{TOP_UP_LINK_TEXT}>"
        )

    @patch(GET_SCOPES, return_value=NON_BILLING_SCOPES)
    def test_format_mrkdwn_not_started_message(self, _: object) -> None:
        link = get_seer_credits_link(self.organization, self.user.id)
        assert format_out_of_credits_mrkdwn(link, message=OUT_OF_CREDITS_NOT_STARTED_MESSAGE) == (
            f"{OUT_OF_CREDITS_NOT_STARTED_MESSAGE} {REQUEST_CREDITS_PROMPT} "
            f"<{link.url}|{REQUEST_CREDITS_LINK_TEXT}>"
        )
