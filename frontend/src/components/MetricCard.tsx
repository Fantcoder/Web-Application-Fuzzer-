import { useEffect, useState } from 'react';
import CountUp from 'react-countup';
import clsx from 'classnames';

interface Props {
  title: string;
  value: number;
  icon?: React.ReactNode;
  className?: string;
}

export default function MetricCard({ title, value, icon, className }: Props) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    setDisplay(value);
  }, [value]);

  return (
    <div className={clsx('bg-neutral-900 border border-neutral-800 rounded-lg p-4 flex items-center space-x-4', className)}>
      {icon && <div className="text-neon">{icon}</div>}
      <div>
        <p className="text-sm uppercase text-neutral-400">{title}</p>
        <h3 className="text-2xl font-bold">
          <CountUp end={display} duration={1} />
        </h3>
      </div>
    </div>
  );
}