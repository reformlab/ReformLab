import { useCallback, useEffect, useRef } from 'react';
import { driver, type DriveStep } from 'driver.js';
import 'driver.js/dist/driver.css';
import styles from './DomainModelTour.module.css';

const tourSteps: DriveStep[] = [
  {
    element: '[aria-label="Population \u2014 click to learn more"]',
    popover: {
      title: 'Population',
      description:
        'A dataset of representative households — income, housing, vehicles, energy use, and demographics. This is one of two inputs to the simulation pipeline.',
      side: 'right',
    },
  },
  {
    element: '[aria-label="Policy \u2014 click to learn more"]',
    popover: {
      title: 'Policy',
      description:
        'The reform being evaluated — tax rates, exemptions, thresholds, and redistribution rules. Policies are composed into portfolios for comparison.',
      side: 'right',
    },
  },
  {
    element: '[aria-label="Orchestrator \u2014 click to learn more"]',
    popover: {
      title: 'Orchestrator',
      description:
        'The core of ReformLab. It runs your simulation year by year, feeding households through computation, behavioral response, and state transition steps.',
    },
  },
  {
    element: '[aria-label="Engine \u2014 click to learn more"]',
    popover: {
      title: 'Engine',
      description:
        'The computation backend that calculates household-level taxes and benefits. Default: OpenFisca France. Swappable via the adapter protocol.',
    },
  },
  {
    element: '[aria-label="Results \u2014 click to learn more"]',
    popover: {
      title: 'Results',
      description:
        'Raw simulation output — a household-by-year panel dataset with every computed variable. Stored as Parquet, cached in memory.',
    },
  },
  {
    element: '[aria-label="Indicators \u2014 click to learn more"]',
    popover: {
      title: 'Indicators',
      description:
        'Analytics computed from results — distributional, fiscal, geographic, and welfare metrics. The final output users interact with.',
      side: 'left',
    },
  },
];

export default function DomainModelTour() {
  const driverRef = useRef<ReturnType<typeof driver> | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    return () => {
      driverRef.current?.destroy();
    };
  }, []);

  const startTour = useCallback(() => {
    driverRef.current?.destroy();
    const driverInstance = driver({
      showProgress: true,
      progressText: 'Step {{current}} of {{total}}',
      showButtons: ['next', 'previous', 'close'],
      allowKeyboardControl: true,
      allowClose: true,
      steps: tourSteps,
      popoverClass: 'reformlab-tour-popover',
      onDestroyed: () => {
        driverRef.current = null;
        buttonRef.current?.focus();
      },
    });
    driverRef.current = driverInstance;
    driverInstance.drive();
  }, []);

  return (
    <button ref={buttonRef} type="button" className={styles.tourButton} onClick={startTour}>
      Take the tour
    </button>
  );
}
