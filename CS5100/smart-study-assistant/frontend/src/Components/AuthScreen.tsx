import { useState } from 'react';
import { Sparkles, Eye, EyeOff, Loader2 } from 'lucide-react';
import { toast } from 'react-hot-toast';

/**
 * AuthScreen component for authentication screens (sign-in and sign-up).
 * @param onSignIn - Callback function for sign-in action.
 * @param onSignUp - Callback function for sign-up action.
 * @returns JSX.Element
 */
export function AuthScreen({ onSignIn, onSignUp }: { onSignIn: any, onSignUp: any }) {
  const [isSignIn, setIsSignIn] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Trim input to avoid copy-paste errors
    const cleanUsername = username.trim();
    const cleanPassword = password.trim();

    try {
      const func = isSignIn ? onSignIn : onSignUp;
      const res = await func(cleanUsername, cleanPassword);

      if (res.success) {
        toast.success(isSignIn ? `Welcome back, ${res.username}!` : 'Account created!');
      } else {
        setError(res.message || 'Authentication failed');
      }
    } catch (err: any) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md bg-surface border border-neutral-800 rounded-2xl p-8 shadow-2xl animate-in zoom-in-95 duration-300">
        <div className="flex justify-center mb-6">
          <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-900/20">
            <Sparkles size={24} />
          </div>
        </div>
        <h1 className="text-2xl font-bold text-center text-white mb-2">Smart Study Assistant</h1>
        <p className="text-center text-neutral-500 mb-8">AI-powered knowledge retrieval system</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-lg text-sm flex items-center gap-2 animate-in fade-in slide-in-from-top-1">
              <div className="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0" />
              {error}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-xs font-medium text-neutral-400 uppercase tracking-wider">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-neutral-900/50 border border-neutral-800 rounded-lg px-4 py-3 text-white placeholder:text-neutral-600 focus:outline-none focus:ring-2 focus:ring-blue-600/50 transition-all"
              placeholder="Enter your username"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-neutral-400 uppercase tracking-wider">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-neutral-900/50 border border-neutral-800 rounded-lg px-4 py-3 text-white placeholder:text-neutral-600 focus:outline-none focus:ring-2 focus:ring-blue-600/50 transition-all pr-10"
                placeholder="Enter your password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-300 transition-colors"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2 mt-4 shadow-lg shadow-blue-900/20"
          >
            {loading && <Loader2 size={18} className="animate-spin" />}
            {isSignIn ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-neutral-500">
          {isSignIn ? "Don't have an account? " : "Already have an account? "}
          <button
            onClick={() => { setIsSignIn(!isSignIn); setError(''); }}
            className="text-blue-500 hover:text-blue-400 font-medium transition-colors"
          >
            {isSignIn ? 'Sign Up' : 'Sign In'}
          </button>
        </div>
      </div>
    </div>
  );
};
