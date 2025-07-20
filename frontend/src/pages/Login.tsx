import { supabase } from '@/lib/supabase';

export default function Login() {
  const signInWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({ provider: 'google' });
  };

  return (
    <div className="flex flex-col items-center justify-center h-full space-y-6">
      <h2 className="text-2xl font-semibold">Sign in to Cyber Fuzzer</h2>
      <button
        onClick={signInWithGoogle}
        className="px-6 py-3 bg-neon text-black rounded-md shadow-md hover:opacity-90"
      >
        Sign in with Google
      </button>
    </div>
  );
}