import { useEffect, useRef, useState } from 'react';
import io from 'socket.io-client';

const socket = io(import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000');

export default function Fuzzer() {
  const [url, setUrl] = useState('http://localhost:8080');
  const [wordlist, setWordlist] = useState<File | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const logEndRef = useRef<HTMLDivElement | null>(null);

  const startFuzz = async () => {
    let wordlistFilePath = 'xss.txt'; // default placeholder

    if (wordlist) {
      // Upload wordlist to backend – not implemented yet
      alert('Custom wordlist upload not yet wired');
    }

    await fetch(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000'}/api/fuzz`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_url: url, wordlist_file: wordlistFilePath, headless: true }),
    });
  };

  useEffect(() => {
    socket.on('log', (data) => {
      setLogs((prev) => [...prev, data.msg]);
    });
    return () => {
      socket.off('log');
    };
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Web Application Fuzzer</h2>

      <div className="space-y-4 max-w-xl">
        <label className="block">
          <span className="text-sm text-neutral-400">Target URL</span>
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="w-full bg-neutral-800 border border-neutral-700 p-2 rounded-md"
            placeholder="http://localhost:8080"
          />
        </label>

        <label className="block">
          <span className="text-sm text-neutral-400">Custom payload wordlist (optional)</span>
          <input type="file" accept=".txt" onChange={(e) => setWordlist(e.target.files?.[0] || null)} />
        </label>

        <button onClick={startFuzz} className="px-6 py-2 bg-neon text-black rounded-md shadow hover:opacity-90">
          Start Fuzzing
        </button>
      </div>

      <div className="bg-neutral-800 border border-neutral-700 rounded-md p-4 h-96 overflow-y-auto font-mono text-sm">
        {logs.map((l, i) => (
          <div key={i}>{l}</div>
        ))}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}