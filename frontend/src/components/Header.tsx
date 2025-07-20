import { Sun, Moon, LogOut } from 'lucide-react';
import { supabase } from '@/lib/supabase';
import { useState } from 'react';

export default function Header() {
  const [dark, setDark] = useState(true);

  const toggleTheme = () => {
    setDark(!dark);
    document.documentElement.classList.toggle('dark', !dark);
  };

  const signOut = async () => {
    await supabase.auth.signOut();
    window.location.href = '/login';
  };

  const Icon = dark ? Sun : Moon;

  return (
    <header className="flex items-center justify-end h-14 px-4 border-b border-neutral-800 bg-neutral-900 sticky top-0 z-10">
      <button onClick={toggleTheme} className="p-2 hover:text-neon">
        <Icon size={18} />
      </button>
      <button onClick={signOut} className="p-2 hover:text-red-400">
        <LogOut size={18} />
      </button>
    </header>
  );
}