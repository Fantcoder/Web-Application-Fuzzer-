import { useEffect, useState } from 'react';
import io from 'socket.io-client';

const socket = io(import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000');

export default function Dashboard() {
  const [threats, setThreats] = useState<string[]>([]);

  useEffect(() => {
    socket.on('log', (data) => {
      setThreats((prev) => [data.msg, ...prev.slice(0, 49)]); // keep last 50
    });

    return () => {
      socket.off('log');
    };
  }, []);

  return (
    <div>
      <h2 className="text-xl mb-4">Real-time Threat Monitor</h2>
      <div className="h-72 overflow-y-auto bg-neutral-800 p-4 rounded-lg border border-neutral-700 space-y-2 text-sm">
        {threats.map((t, idx) => (
          <div key={idx} className="font-mono text-neon-light">
            {t}
          </div>
        ))}
        {threats.length === 0 && <p className="text-neutral-400">No events yet…</p>}
      </div>
    </div>
  );
}