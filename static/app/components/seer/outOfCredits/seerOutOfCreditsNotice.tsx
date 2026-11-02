import {Alert} from '@sentry/scraps/alert';

import {t} from 'sentry/locale';

/**
 * What the viewer can do about running out of credits:
 *
 * - `top-up`: billing members add credits themselves.
 * - `request`: everyone else asks the billing members to add credits.
 * - `contact`: orgs that can't self-serve buy credits through their account
 *   team, so members get no button and are only told who to ask.
 */
export type SeerOutOfCreditsEscalation = 'top-up' | 'request' | 'contact';

export interface SeerOutOfCreditsNoticeProps {
  escalation: SeerOutOfCreditsEscalation;
  /**
   * Shown while a credits request is sending.
   */
  isRequestingCredits?: boolean;
  /**
   * Replaces the default headline, for example to say a run stopped part way.
   */
  message?: React.ReactNode;
  onRequestCredits?: () => void;
  /**
   * Opens the top-up modal in place.
   */
  onTopUp?: () => void;
}

const ESCALATION_DETAIL: Record<SeerOutOfCreditsEscalation, string> = {
  'top-up': t('Top up to keep using Seer.'),
  request: t('Ask someone with billing access to add more.'),
  contact: t('Ask someone with billing access in your organization to add more.'),
};

/**
 * The out-of-credits message and the one action the viewer can take. Product
 * code renders `SeerOutOfCreditsCta`, which picks the escalation for the
 * viewer; this is the presentation underneath it.
 */
export function SeerOutOfCreditsNotice({
  escalation,
  message,
  onTopUp,
  onRequestCredits,
  isRequestingCredits,
}: SeerOutOfCreditsNoticeProps) {
  return (
    <Alert
      variant="warning"
      data-test-id="seer-out-of-credits"
      trailingItems={
        <SeerOutOfCreditsAction
          escalation={escalation}
          onTopUp={onTopUp}
          onRequestCredits={onRequestCredits}
          isRequestingCredits={isRequestingCredits}
        />
      }
    >
      {message ?? t('Your organization is out of Seer credits.')}{' '}
      {ESCALATION_DETAIL[escalation]}
    </Alert>
  );
}

function SeerOutOfCreditsAction({
  escalation,
  onTopUp,
  onRequestCredits,
  isRequestingCredits,
}: Omit<SeerOutOfCreditsNoticeProps, 'message'>) {
  if (escalation === 'top-up' && onTopUp) {
    return <Alert.Button onClick={onTopUp}>{t('Top up')}</Alert.Button>;
  }

  if (escalation === 'request' && onRequestCredits) {
    return (
      <Alert.Button busy={isRequestingCredits} onClick={onRequestCredits}>
        {t('Request credits')}
      </Alert.Button>
    );
  }

  return null;
}
