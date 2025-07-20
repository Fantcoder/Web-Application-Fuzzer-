import { Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Fuzzer from './pages/Fuzzer';
import Login from './pages/Login';
import { supabase } from './lib/supabase';
import Sidebar from './components/Sidebar';
import Header from './components/Header';

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const session = supabase.auth.session();
  if (!session) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <div className="flex bg-neutral-900 text-gray-100 min-h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="p-6 flex-1 overflow-y-auto">
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
    </div>
  );
}