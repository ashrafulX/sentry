import {Fragment} from 'react';
import {useQuery} from '@tanstack/react-query';

import {Heading} from '@sentry/scraps/text';

import {openModal, type ModalRenderProps} from 'sentry/actionCreators/modal';
import {LoadingError} from 'sentry/components/loadingError';
import {LoadingIndicator} from 'sentry/components/loadingIndicator';
import {t} from 'sentry/locale';
import type {Organization} from 'sentry/types/organization';

import {AutoTopUpModal} from 'getsentry/views/subscriptionPage/seerWallet/autoTopUpModal';
import {
  seerWalletAutoTopUpOptions,
  seerWalletBalanceOptions,
} from 'getsentry/views/subscriptionPage/seerWallet/seerWalletOptions';

interface TopUpModalOptions {
  organization: Organization;
}

/**
 * The auto top-up settings from the billing page, opened wherever Seer runs
 * out of credits. Unlike the billing page it has no wallet card behind it, so
 * it loads the wallet itself and shows the balance first.
 */
function TopUpModal(props: TopUpModalOptions & ModalRenderProps) {
  const {Header, Body, organization} = props;
  const balanceQuery = useQuery(seerWalletBalanceOptions(organization));
  const autoTopUpQuery = useQuery(seerWalletAutoTopUpOptions(organization));

  if (balanceQuery.data && autoTopUpQuery.data) {
    return (
      <AutoTopUpModal
        {...props}
        autoTopUp={autoTopUpQuery.data}
        creditPriceCents={balanceQuery.data.creditPriceCents}
        balance={balanceQuery.data.balance}
      />
    );
  }

  return (
    <Fragment>
      <Header closeButton>
        <Heading as="h2">{t('Seer credits')}</Heading>
      </Header>
      <Body>
        {balanceQuery.isError || autoTopUpQuery.isError ? (
          <LoadingError
            message={t('Unable to load your Seer credits.')}
            onRetry={() => {
              balanceQuery.refetch();
              autoTopUpQuery.refetch();
            }}
          />
        ) : (
          <LoadingIndicator />
        )}
      </Body>
    </Fragment>
  );
}

export function openSeerTopUpModal(options: TopUpModalOptions) {
  openModal(deps => <TopUpModal {...deps} {...options} />);
}
