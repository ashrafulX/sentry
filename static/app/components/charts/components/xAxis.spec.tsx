import {ThemeFixture} from 'sentry-fixture/theme';
import {UserFixture} from 'sentry-fixture/user';

import type {XAxisProps} from 'sentry/components/charts/components/xAxis';
import {createXAxisOptions} from 'sentry/components/charts/components/xAxis';
import {ConfigStore} from 'sentry/stores/configStore';

const theme = ThemeFixture();

describe('Chart XAxis', () => {
  beforeEach(() => {
    const user = UserFixture();
    user.options.timezone = 'America/Los_Angeles';
    ConfigStore.set('user', user);
  });
  let axisLabelFormatter: (value: string | number, index: number) => string;
  let xAxisObj!: ReturnType<typeof createXAxisOptions>;
  const props: XAxisProps = {
    isGroupedByDate: true,
    theme,
  };
  const timestamp = 1531094400000;

  describe('axisLabel', () => {
    describe('With Period > 24h', () => {
      describe('Local timezone', () => {
        beforeEach(() => {
          xAxisObj = createXAxisOptions({
            ...props,
            period: '7d',
            utc: false,
          });

          // @ts-expect-error formatter type is missing
          axisLabelFormatter = xAxisObj.axisLabel!.formatter;
        });

        it('formats axis label for first data point', () => {
          expect(axisLabelFormatter(timestamp, 0)).toBe('Jul 8 5:00 PM');
        });

        it('formats axis label for second data point', () => {
          expect(axisLabelFormatter(timestamp, 1)).toBe('Jul 8 5:00 PM');
        });
      });

      describe('UTC', () => {
        beforeEach(() => {
          xAxisObj = createXAxisOptions({
            ...props,
            period: '7d',
            utc: true,
          });

          // @ts-expect-error formatter type is missing
          axisLabelFormatter = xAxisObj.axisLabel!.formatter;
        });

        it('formats axis label for first data point', () => {
          expect(axisLabelFormatter(timestamp, 0)).toBe('Jul 9 12:00 AM');
        });

        it('formats axis label for second data point', () => {
          expect(axisLabelFormatter(timestamp, 1)).toBe('Jul 9 12:00 AM');
        });
      });

      describe('Multiline', () => {
        beforeEach(() => {
          xAxisObj = createXAxisOptions({
            ...props,
            useMultilineDate: true,
            period: '7d',
          });

          // @ts-expect-error formatter type is missing
          axisLabelFormatter = xAxisObj.axisLabel!.formatter;
        });

        it('formats axis label for first data point', () => {
          expect(axisLabelFormatter(timestamp, 0)).toBe('Jul 8\n5:00 PM');
        });

        it('formats axis label for second data point', () => {
          expect(axisLabelFormatter(timestamp, 1)).toBe('Jul 8\n5:00 PM');
        });
      });
    });

    describe('With Period <= 24h', () => {
      describe('Local timezone', () => {
        beforeEach(() => {
          xAxisObj = createXAxisOptions({
            ...props,
            period: '24h',
            utc: false,
          });

          // @ts-expect-error formatter type is missing
          axisLabelFormatter = xAxisObj.axisLabel!.formatter;
        });

        it('formats axis label for first data point', () => {
          expect(axisLabelFormatter(timestamp, 0)).toBe('Jul 8 5:00 PM');
        });

        it('formats axis label for second data point', () => {
          expect(axisLabelFormatter(timestamp, 1)).toBe('5:00 PM');
        });
      });

      describe('UTC', () => {
        beforeEach(() => {
          xAxisObj = createXAxisOptions({
            ...props,
            period: '24h',
            utc: true,
          });

          // @ts-expect-error formatter type is missing
          axisLabelFormatter = xAxisObj.axisLabel!.formatter;
        });

        it('formats axis label for first data point', () => {
          expect(axisLabelFormatter(timestamp, 0)).toBe('Jul 9 12:00 AM');
        });

        it('formats axis label for second data point', () => {
          expect(axisLabelFormatter(timestamp, 1)).toBe('12:00 AM');
        });
      });

      describe('Multiline', () => {
        beforeEach(() => {
          xAxisObj = createXAxisOptions({
            ...props,
            useMultilineDate: true,
            period: '24h',
            utc: true,
          });

          // @ts-expect-error formatter type is missing
          axisLabelFormatter = xAxisObj.axisLabel!.formatter;
        });

        it('formats axis label for first data point', () => {
          expect(axisLabelFormatter(timestamp, 0)).toBe('Jul 9\n12:00 AM');
        });

        it('formats axis label for second data point', () => {
          expect(axisLabelFormatter(timestamp, 1)).toBe('12:00 AM');
        });
      });
    });
  });
});
