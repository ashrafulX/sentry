import {OrganizationFixture} from 'sentry-fixture/organization';

import {SubscriptionFixture} from 'getsentry-test/fixtures/subscription';
import {
  act,
  render,
  renderGlobalModal,
  screen,
  userEvent,
  waitFor,
} from 'sentry-test/reactTestingLibrary';

import {SubscriptionStore} from 'getsentry/stores/subscriptionStore';

import {SeerOutOfCreditsCta} from './seerOutOfCreditsCta';

describe('SeerOutOfCreditsCta', () => {
  beforeEach(() => {
    MockApiClient.clearMockResponses();
  });

  it('lets billing members top up in a modal', async () => {
    const organization = OrganizationFixture({access: ['org:read', 'org:billing']});
    act(() =>
      SubscriptionStore.set(organization.slug, SubscriptionFixture({organization}))
    );
    MockApiClient.addMockResponse({
      url: `/customers/${organization.slug}/seer-wallet/`,
      body: {
        balance: 0,
        creditPriceCents: 1,
        included: {total: 500, remaining: 0, resetsAt: null},
        purchased: {total: 0, remaining: 0, expiresAt: null},
      },
    });
    MockApiClient.addMockResponse({
      url: `/customers/${organization.slug}/seer-wallet/auto-top-up/`,
      body: {
        enabled: false,
        thresholdCredits: 500,
        topUpCredits: 1000,
        dailySpendCapCents: 7500,
      },
    });

    render(<SeerOutOfCreditsCta />, {organization});
    renderGlobalModal({organization});

    expect(
      screen.getByText(/Your organization is out of Seer credits/)
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', {name: 'Top up'}));
    expect(await screen.findByText('0 credits')).toBeInTheDocument();
    expect(screen.getByRole('checkbox', {name: 'Auto top-up'})).toBeInTheDocument();
    expect(
      screen.queryByRole('button', {name: 'Request credits'})
    ).not.toBeInTheDocument();
  });

  it('lets other members of self-serve orgs request credits', async () => {
    const organization = OrganizationFixture({access: ['org:read']});
    act(() =>
      SubscriptionStore.set(
        organization.slug,
        SubscriptionFixture({organization, canSelfServe: true})
      )
    );
    const request = MockApiClient.addMockResponse({
      url: `/organizations/${organization.slug}/event-limit-increase-request/`,
      method: 'POST',
    });

    render(<SeerOutOfCreditsCta />, {organization});

    expect(screen.queryByRole('button', {name: 'Top up'})).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', {name: 'Request credits'}));

    await waitFor(() =>
      expect(request).toHaveBeenCalledWith(
        `/organizations/${organization.slug}/event-limit-increase-request/`,
        expect.objectContaining({data: expect.objectContaining({types: ['seerAutofix']})})
      )
    );
  });

  it('offers no request to members of orgs that cannot self-serve', () => {
    const organization = OrganizationFixture({access: ['org:read']});
    act(() =>
      SubscriptionStore.set(
        organization.slug,
        SubscriptionFixture({organization, canSelfServe: false})
      )
    );

    render(<SeerOutOfCreditsCta />, {organization});

    expect(
      screen.getByText(/Ask someone with billing access in your organization/)
    ).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('replaces the headline with a custom message', () => {
    const organization = OrganizationFixture({access: ['org:read', 'org:billing']});
    act(() =>
      SubscriptionStore.set(organization.slug, SubscriptionFixture({organization}))
    );

    render(<SeerOutOfCreditsCta message="Seer stopped part way." />, {organization});

    expect(screen.getByText(/Seer stopped part way\./)).toBeInTheDocument();
    expect(
      screen.queryByText(/Your organization is out of Seer credits/)
    ).not.toBeInTheDocument();
  });
});
