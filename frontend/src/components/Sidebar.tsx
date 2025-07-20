import { Link, useLocation } from 'react-router-dom';
import { Shield, Bug, Activity } from 'lucide-react';
import clsx from 'classnames';

const navItems = [
  { to: '/', label: 'Dashboard', icon: Activity },
  { to: '/fuzzer', label: 'Fuzzer', icon: Bug },
];

export default function Sidebar() {
  const { pathname } = useLocation();
  return (
    <aside className="hidden md:flex flex-col w-56 bg-neutral-950 border-r border-neutral-800 p-4 space-y-4">
      <h1 className="text-2xl font-bold text-neon mb-6">⚡ CF</h1>
      {navItems.map(({ to, label, icon: Icon }) => (
        <Link
          key={to}
          to={to}
          className={clsx(
            'flex items-center space-x-3 px-3 py-2 rounded-md hover:bg-neutral-800 transition-colors',
            pathname === to && 'bg-neutral-800 text-neon'
          )}
        >
          <Icon size={18} />
          <span>{label}</span>
        </Link>
      ))}
    </aside>
  );
}