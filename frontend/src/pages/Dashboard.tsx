import { useEffect, useState } from 'react';
import io from 'socket.io-client';
import MetricCard from '@/components/MetricCard';
import { Bug, ShieldAlert, Activity } from 'lucide-react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const socket = io(import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000');

export default function Dashboard() {
  const [stats, setStats] = useState({ total: 0, malicious: 0, suspicious: 0, safe: 0 });
  const [threats, setThreats] = useState<string[]>([]);

  useEffect(() => {
    socket.on('log', (data) => {
      setThreats((prev) => [data.msg, ...prev.slice(0, 49)]);
      // crude parsing for demo – increment counters based on keywords
      const lower = data.msg.toLowerCase();
      setStats((s) => ({
        total: s.total + 1,
        malicious: s.malicious + (lower.includes('malicious') ? 1 : 0),
        suspicious: s.suspicious + (lower.includes('suspicious') ? 1 : 0),
        safe: s.safe + (lower.includes('safe') ? 1 : 0),
      }));
    });
    return () => {
      socket.off('log');
    };
  }, []);

  const chartData = {
    labels: ['Malicious', 'Suspicious', 'Safe'],
    datasets: [
      {
        label: 'Findings',
        data: [stats.malicious, stats.suspicious, stats.safe],
        backgroundColor: ['#ef4444', '#f59e0b', '#22c55e'],
      },
    ],
  };

  return (
    <div className="space-y-8">
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Total" value={stats.total} icon={<Activity />} />
        <MetricCard title="Malicious" value={stats.malicious} icon={<ShieldAlert />} className="border-red-600" />
        <MetricCard title="Suspicious" value={stats.suspicious} icon={<Bug />} className="border-yellow-500" />
        <MetricCard title="Safe" value={stats.safe} icon={<Bug />} className="border-green-500" />
      </div>

      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
        <h3 className="mb-4 text-lg font-semibold">Risk Distribution</h3>
        <Bar data={chartData} />
      </div>

      <div>
        <h3 className="text-lg mb-2 font-semibold">Live Event Stream</h3>
        <div className="h-72 overflow-y-auto bg-neutral-900 border border-neutral-800 p-4 rounded-lg space-y-2 text-sm">
          {threats.map((t, idx) => (
            <div key={idx} className="font-mono text-neon-light">
              {t}
            </div>
          ))}
          {threats.length === 0 && <p className="text-neutral-400">No events yet…</p>}
        </div>
      </div>
    </div>
  );
}