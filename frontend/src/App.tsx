import { useEffect, useState } from 'react';
import { Routes, Route, Navigate, Link } from 'react-router-dom';
import { createClient } from '@supabase/supabase-js';
import Dashboard from './pages/Dashboard';
import Fuzzer from './pages/Fuzzer';
import Login from './pages/Login';
import { supabase } from './lib/supabase';
import clsx from 'classnames';

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const session = supabase.auth.session();
  if (!session) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  return (
    <div className="min-h-screen bg-neutral-900 text-gray-100">
      <header className="border-b border-neutral-700 p-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-neon">⚡ Cyber Fuzzer</h1>
        <nav className="space-x-4">
          <Link className="hover:text-neon" to="/">Dashboard</Link>
          <Link className="hover:text-neon" to="/fuzzer">Fuzzer</Link>
        </nav>
      </header>

      <main className="p-6">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/fuzzer"
            element={
              <ProtectedRoute>
                <Fuzzer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </div>
  );
}