"""Shared copy and links for Slack replies when an org runs out of Seer credits."""

from __future__ import annotations

from dataclasses import dataclass

from sentry.models.organization import Organization
from sentry.models.organizationmember import OrganizationMember

OUT_OF_CREDITS_MESSAGE = "Your organization is out of Seer credits, so Seer stopped here."
TOP_UP_PROMPT = "Add credits to continue."
REQUEST_CREDITS_PROMPT = "Ask an organization owner or billing admin to add credits."
TOP_UP_LINK_TEXT = "Add Seer credits"
REQUEST_CREDITS_LINK_TEXT = "Request Seer credits"

BILLING_SCOPE = "org:billing"


@dataclass(frozen=True)
class SeerCreditsLink:
    url: str
    text: str
    # The prompt to show next to the link (TOP_UP_PROMPT or REQUEST_CREDITS_PROMPT).
    prompt: str
    can_top_up: bool


def can_manage_billing(organization: Organization, user_id: int | None) -> bool:
    """Whether the user can add credits: the same `org:billing` scope the billing UI checks."""
    if user_id is None:
        return False
    member = OrganizationMember.objects.filter(
        organization_id=organization.id, user_id=user_id
    ).first()
    return member is not None and BILLING_SCOPE in member.get_scopes()


def get_seer_credits_link(organization: Organization, user_id: int | None) -> SeerCreditsLink:
    """The link to add credits, or to request them when the user can't manage billing.

    Slack can't open the top-up modal, and no Sentry page opens it on load, so both point at
    the billing overview, which shows the Seer wallet to billing members and lists billing admins
    to everyone else. Repoint the URLs here once dedicated pages exist.
    """
    url = organization.absolute_url(
        f"/settings/{organization.slug}/billing/overview/", query="referrer=slack-seer-credits"
    )
    if can_manage_billing(organization, user_id):
        return SeerCreditsLink(
            url=url, text=TOP_UP_LINK_TEXT, prompt=TOP_UP_PROMPT, can_top_up=True
        )
    return SeerCreditsLink(
        url=url, text=REQUEST_CREDITS_LINK_TEXT, prompt=REQUEST_CREDITS_PROMPT, can_top_up=False
    )


def format_out_of_credits_mrkdwn(link: SeerCreditsLink) -> str:
    """The full out-of-credits reply as Slack mrkdwn, with the link inline."""
    return f"{OUT_OF_CREDITS_MESSAGE} {link.prompt} <{link.url}|{link.text}>"
