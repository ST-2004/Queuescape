import { Amplify } from 'aws-amplify';
import { signUp, confirmSignUp, signIn, signOut, fetchAuthSession, getCurrentUser} from '@aws-amplify/auth';
import React, { useState, useEffect } from 'react';
import { Users, Clock, CheckCircle, AlertCircle, Settings, PlayCircle, CheckSquare, ArrowLeft, RefreshCw, MapPin, Link as LinkIcon, LogIn, Mail, Lock, UserPlus } from 'lucide-react';


Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: 'us-east-1_LSkUhawY5', // Your User Pool ID
      userPoolClientId: '6v6on9bsj9hcgopi6mrk0g1bsp', // Your Client ID
      loginWith: {
        email: true
      }
    }
  }
});

// ==========================================
// CONFIGURATION
// ==========================================
const API_BASE_URL = "https://tbmndj28ib.execute-api.us-east-1.amazonaws.com/dev";

// Traffic period definitions with service times
const TRAFFIC_PERIODS = {
  MORNING: { label: 'Morning', serviceTime: 5, startHour: 6, endHour: 12, color: 'green' },
  AFTERNOON: { label: 'Afternoon', serviceTime: 8, startHour: 12, endHour: 18, color: 'yellow' },
  EVENING: { label: 'Evening', serviceTime: 15, startHour: 18, endHour: 24, color: 'red' }
};

// const MOCK_STAFF_CREDENTIALS = { email: 'admin@queueescape.com', password: 'admin123' };

// ==========================================
// API SERVICE LAYER
// ==========================================

export function useAuthReady() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const session = await fetchAuthSession();
        if (session.tokens?.accessToken) {
          setReady(true);
        }
      } catch {
        setReady(false);
      }
    };

    checkSession();
  }, []);

  return ready;
}

async function getAuthHeader() {
  const session = await fetchAuthSession();
  const accessToken = session.tokens?.accessToken?.toString();

  if (!accessToken) {
    throw new Error('No access token found');
  }

  return {
    Authorization: `Bearer ${accessToken}`
  };
}

const apiService = {
  async joinQueue(email, queueId) {
    const response = await fetch(`${API_BASE_URL}/queue/join`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, queueId })
    });
    if (!response.ok) throw new Error('Failed to join queue');
    return response.json();
  },

  async getQueueStatus(queueId, ticketId) {
    const response = await fetch(`${API_BASE_URL}/queue/status/${queueId}/${ticketId}`);
    if (!response.ok) throw new Error('Failed to fetch status');
    return response.json();
  },

  async getStaffSummary(queueId) {
    const authHeader = await getAuthHeader();
    const response = await fetch(`${API_BASE_URL}/queue/staff/summary?queueId=${queueId}`,
      { headers: { ...authHeader } }
    );
    if (!response.ok) throw new Error('Failed to fetch summary');
    return response.json();
  },

  async callNextTicket(queueId) {
    const authHeader = await getAuthHeader();
    const response = await fetch(`${API_BASE_URL}/queue/staff/next`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' , ...authHeader },
      body: JSON.stringify({ queueId })
    });
    if (!response.ok) throw new Error('Failed to call next');
    return response.json();
  },

  async completeTicket(ticketNumber, queueId) {
    const authHeader = await getAuthHeader();
    const response = await fetch(`${API_BASE_URL}/queue/staff/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' , ...authHeader },
      body: JSON.stringify({ ticketNumber, queueId })
    });
    if (!response.ok) throw new Error('Failed to complete');
    return response.json();
  },

  async updateTrafficSettings(period, queueId) {
    const authHeader = await getAuthHeader();
    const response = await fetch(`${API_BASE_URL}/queue/staff/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' , ...authHeader },
      body: JSON.stringify({ peak_period: period, queueId })
    });
    if (!response.ok) throw new Error('Failed to update settings');
    return response.json();
  }
};

// ==========================================
// UTILITY: ETA CALCULATOR
// ==========================================
const etaCalculator = {
  calculateETA(position, selectedPeriod = 'AFTERNOON') {
    if (position <= 0) return 0;
    const currentHour = new Date().getHours();
    const currentPeriod = this.getCurrentPeriod(currentHour);
    const serviceTime = currentPeriod === selectedPeriod 
      ? TRAFFIC_PERIODS[currentPeriod].serviceTime 
      : TRAFFIC_PERIODS[selectedPeriod].serviceTime;
    return position * serviceTime;
  },

  getCurrentPeriod(hour) {
    if (hour >= 6 && hour < 12) return 'MORNING';
    if (hour >= 12 && hour < 18) return 'AFTERNOON';
    return 'EVENING';
  }
};

// ==========================================
// UTILITY: EMAIL VALIDATOR
// ==========================================
const emailValidator = {
  validate(email) {
    if (!email || email.trim() === '') {
      return { isValid: false, error: 'Email is required' };
    }
    if (!email.includes('@')) {
      return { isValid: false, error: 'Email must contain @' };
    }
    const domainRegex = /\.[a-z]{2,}$/i;
    if (!domainRegex.test(email)) {
      return { isValid: false, error: 'Email must have a valid domain (e.g., .com, .edu, .ca)' };
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return { isValid: false, error: 'Invalid email format' };
    }
    return { isValid: true, error: '' };
  }
};

// ==========================================
// UTILITY: PASSWORD VALIDATOR
// ==========================================

const passwordValidator = {
  validate(password) {
    if (!password || password.length < 8) {
      return { isValid: false, error: 'Password must be at least 8 characters' };
    }
    if (!/[A-Z]/.test(password)) {
      return { isValid: false, error: 'Password must contain an uppercase letter' };
    }
    if (!/[a-z]/.test(password)) {
      return { isValid: false, error: 'Password must contain a lowercase letter' };
    }
    if (!/[0-9]/.test(password)) {
      return { isValid: false, error: 'Password must contain a number' };
    }
    return { isValid: true, error: '' };
  }
};

// ==========================================
// SHARED: TOAST NOTIFICATION
// ==========================================
const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg ${
      type === 'success' ? 'bg-teal-500' : 'bg-red-500'
    } text-white transition-all`}>
      {message}
    </div>
  );
};

// ==========================================
// VIEW 1: CUSTOMER LANDING PAGE
// ==========================================
const CustomerLanding = ({ onNavigate }) => {
  const [email, setEmail] = useState('');
  const [queueId, setQueueId] = useState('');
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [emailError, setEmailError] = useState('');
  const [queueError, setQueueError] = useState('');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const queueParam = params.get('queue');
    if (queueParam) setQueueId(queueParam);
  }, []);

  const handleEmailChange = (e) => {
    const value = e.target.value;
    setEmail(value);
    if (value) {
      const validation = emailValidator.validate(value);
      setEmailError(validation.error);
    } else {
      setEmailError('');
    }
  };

  const handleJoinQueue = async (e) => {
    e.preventDefault();
    const emailValidation = emailValidator.validate(email);
    if (!emailValidation.isValid) {
      setEmailError(emailValidation.error);
      return;
    }
    if (!queueId.trim()) {
      setQueueError('Queue name is required');
      return;
    }

    setLoading(true);
    try {
      const data = await apiService.joinQueue(email, queueId);
      onNavigate('status', { ticketId: data.ticketNumber, queueId: queueId });
    } catch (error) {
      setToast({ message: 'Failed to join queue. Please try again.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = email && !emailError && queueId.trim();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-teal-500 rounded-full mb-4 shadow-lg">
            <Users className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-slate-800 mb-2">QueueEscape</h1>
          <p className="text-slate-600">Join the line from anywhere.</p>
        </div>

        <div className="bg-white rounded-xl shadow-xl p-8">
          <h2 className="text-2xl font-semibold text-slate-800 mb-6 border-b pb-4">Join Queue</h2>
          
          <form onSubmit={handleJoinQueue} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-teal-500" />
                Queue Name
              </label>
              <input
                type="text"
                value={queueId}
                onChange={(e) => { setQueueId(e.target.value); setQueueError(''); }}
                placeholder="e.g. Registrar, Cafeteria, Support"
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-teal-500 outline-none bg-slate-50 ${
                  queueError ? 'border-red-500' : 'border-slate-300'
                }`}
              />
              {queueError && (
                <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {queueError}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                <Mail className="w-4 h-4 text-teal-500" />
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={handleEmailChange}
                placeholder="your.email@example.com"
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-teal-500 outline-none bg-slate-50 ${
                  emailError ? 'border-red-500' : 'border-slate-300'
                }`}
              />
              {emailError && (
                <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {emailError}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !isFormValid}
              className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-4 rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
            >
              {loading ? (
                <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <PlayCircle className="w-5 h-5" />
                  Join Queue
                </>
              )}
            </button>
          </form>
          <div className="mt-8 text-center">
          <button
            onClick={() => onNavigate('staffLogin')}
            className="text-sm text-slate-500 hover:text-slate-800 hover:underline flex items-center justify-center gap-2 mx-auto"
          >
            <LogIn className="w-4 h-4" />
            Staff Login
          </button>
        </div>
        </div>
      </div>
    </div>
  );
};

// ==========================================
// VIEW 2: STATUS PAGE
// ==========================================
const StatusPage = ({ ticketId, queueId, onNavigate }) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await apiService.getQueueStatus(queueId, ticketId);
        setStatus(data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch status. The ticket might be invalid or expired.');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 60000); // 60 seconds
    return () => clearInterval(interval);
  }, [ticketId, queueId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-500 font-medium">Locating ticket...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-800 mb-2">Ticket Error</h2>
          <p className="text-slate-600 mb-6">{error}</p>
          <button
            onClick={() => onNavigate('home')}
            className="bg-teal-500 hover:bg-teal-600 text-white font-semibold py-3 px-6 rounded-lg"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  const isBeingServed = status?.status === 'BEING_SERVED';
  const estimatedWait = etaCalculator.calculateETA(status?.position || 0, 'AFTERNOON');

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => onNavigate('home')}
          className="flex items-center gap-2 text-slate-500 hover:text-slate-800 mb-8 font-medium"
        >
          <ArrowLeft className="w-5 h-5" />
          Leave Queue
        </button>

        <div className="text-center mb-8">
          <span className="inline-block py-1 px-4 rounded-full bg-slate-200 text-slate-700 text-sm font-bold mb-3">
            {queueId}
          </span>
          <h1 className="text-3xl font-bold text-slate-800">Your Status</h1>
        </div>

        <div className={`rounded-2xl shadow-xl p-8 ${
          isBeingServed ? 'bg-gradient-to-br from-teal-500 to-emerald-600' : 'bg-white'
        }`}>
          <div className="text-center mb-10">
            <p className={`text-xs font-bold uppercase mb-2 ${isBeingServed ? 'text-teal-100' : 'text-slate-400'}`}>
              Ticket Number
            </p>
            <div className={`text-5xl font-mono font-bold ${isBeingServed ? 'text-white' : 'text-slate-800'}`}>
              {ticketId}
            </div>
          </div>

          {isBeingServed ? (
            <div className="text-center">
              <div className="bg-white/20 rounded-full p-4 w-24 h-24 mx-auto mb-6 flex items-center justify-center">
                <CheckCircle className="w-14 h-14 text-white" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-2">It's Your Turn!</h2>
              <p className="text-teal-50 text-lg">Please proceed to the counter.</p>
            </div>
          ) : (
            <div>
              <div className="grid grid-cols-2 gap-6 mb-8">
                <div className="bg-slate-50 rounded-xl p-6 text-center">
                  <Users className="w-8 h-8 text-teal-500 mx-auto mb-3" />
                  <p className="text-sm font-medium text-slate-500 mb-1">Position</p>
                  <p className="text-3xl font-bold text-slate-800">{status?.position || 0}</p>
                  <p className="text-xs text-slate-400 mt-2">
                    {status?.position === 1 ? 'You are next!' : 'People ahead'}
                  </p>
                </div>

                <div className="bg-slate-50 rounded-xl p-6 text-center">
                  <Clock className="w-8 h-8 text-blue-500 mx-auto mb-3" />
                  <p className="text-sm font-medium text-slate-500 mb-1">Est. Wait</p>
                  <p className="text-3xl font-bold text-slate-800">{estimatedWait}</p>
                  <p className="text-xs text-slate-400 mt-2">minutes</p>
                </div>
              </div>

              <div className="mb-6">
                <div className="flex justify-between text-xs font-bold text-slate-400 uppercase mb-2">
                  <span>In Queue</span>
                  <span>Your Turn</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-4">
                  <div 
                    className="bg-teal-500 h-4 rounded-full transition-all duration-1000"
                    style={{ width: `${Math.max(5, 100 - (status?.position || 0) * 10)}%` }}
                  />
                </div>
              </div>

              {status?.note && (
                <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex items-start gap-3">
                  <Clock className="w-5 h-5 text-blue-600 shrink-0" />
                  <p className="text-sm text-blue-800">{status.note}</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="text-center mt-8">
          <p className="text-sm text-slate-400 flex items-center justify-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute h-full w-full rounded-full bg-teal-400 opacity-75"></span>
              <span className="relative rounded-full h-2 w-2 bg-teal-500"></span>
            </span>
            Updates every 60 seconds
          </p>
        </div>
      </div>
    </div>
  );
};

// ==========================================
// VIEW 3: STAFF SIGNUP
// ==========================================

const StaffSignup = ({ onNavigate, onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [needsVerification, setNeedsVerification] = useState(false);
  const [error, setError] = useState('');
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleEmailChange = (e) => {
    const value = e.target.value;
    setEmail(value);
    if (value) {
      const validation = emailValidator.validate(value);
      setEmailError(validation.error);
    } else {
      setEmailError('');
    }
  };

  const handlePasswordChange = (e) => {
    const value = e.target.value;
    setPassword(value);
    if (value) {
      const validation = passwordValidator.validate(value);
      setPasswordError(validation.error);
    } else {
      setPasswordError('');
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setError('');

    // Validate email
    const emailValidation = emailValidator.validate(email);
    if (!emailValidation.isValid) {
      setEmailError(emailValidation.error);
      return;
    }

    // Validate password
    const passwordValidation = passwordValidator.validate(password);
    if (!passwordValidation.isValid) {
      setPasswordError(passwordValidation.error);
      return;
    }

    // Check password match
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      const { isSignUpComplete, userId, nextStep } = await signUp({
        username: email,
        password: password,
        options: {
          userAttributes: {
            email: email
          }
        }
      });

      if (nextStep.signUpStep === 'CONFIRM_SIGN_UP') {
        setNeedsVerification(true);
        setError('');
      } else if (isSignUpComplete) {
        setError('Account created! Redirecting to login...');
        setTimeout(() => onNavigate('staffLogin'), 2000);
      }
    } catch (err) {
      setError(err.message || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { isSignUpComplete } = await confirmSignUp({
        username: email,
        confirmationCode: verificationCode
      });

      if (isSignUpComplete) {
        setError('Email verified! Redirecting to login...');
        setTimeout(() => onNavigate('staffLogin'), 2000);
      }
    } catch (err) {
      setError(err.message || 'Verification failed. Please check your code.');
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = email && !emailError && password && !passwordError && confirmPassword && password === confirmPassword;

  if (needsVerification) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-teal-500 rounded-full mb-4 shadow-lg">
              <Mail className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-slate-800 mb-2">Verify Email</h1>
            <p className="text-slate-600">Check your inbox for the verification code</p>
          </div>

          <div className="bg-white rounded-xl shadow-xl p-8">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <p className="text-sm text-blue-800">
                We sent a verification code to <strong>{email}</strong>
              </p>
            </div>

            <form onSubmit={handleVerify} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Verification Code
                </label>
                <input
                  type="text"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  placeholder="Enter 6-digit code"
                  maxLength={6}
                  required
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none bg-slate-50 text-center text-2xl font-mono tracking-widest"
                />
              </div>

              {error && (
                <div className={`border rounded-lg p-3 flex items-center gap-2 ${
                  error.includes('verified') ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                }`}>
                  {error.includes('verified') ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-red-500" />
                  )}
                  <p className={`text-sm ${error.includes('verified') ? 'text-green-700' : 'text-red-700'}`}>
                    {error}
                  </p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !verificationCode}
                className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-4 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 shadow-lg"
              >
                {loading ? (
                  <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <CheckCircle className="w-5 h-5" />
                    Verify Email
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-teal-500 rounded-full mb-4 shadow-lg">
            <UserPlus className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-slate-800 mb-2">Create Staff Account</h1>
          <p className="text-slate-600">Join the team and manage queues</p>
        </div>

        <div className="bg-white rounded-xl shadow-xl p-8">
          <form onSubmit={handleSignup} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                <Mail className="w-4 h-4 text-teal-500" />
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={handleEmailChange}
                placeholder="your.email@company.com"
                required
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-teal-500 outline-none bg-slate-50 ${
                  emailError ? 'border-red-500' : 'border-slate-300'
                }`}
              />
              {emailError && (
                <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {emailError}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                <Lock className="w-4 h-4 text-teal-500" />
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={handlePasswordChange}
                placeholder="••••••••"
                required
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-teal-500 outline-none bg-slate-50 ${
                  passwordError ? 'border-red-500' : 'border-slate-300'
                }`}
              />
              {passwordError && (
                <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {passwordError}
                </p>
              )}
              {!passwordError && password && (
                <p className="text-slate-500 text-xs mt-1">
                  Min 8 chars, with uppercase, lowercase, and number
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                <Lock className="w-4 h-4 text-teal-500" />
                Confirm Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                required
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-teal-500 outline-none bg-slate-50 ${
                  confirmPassword && password !== confirmPassword ? 'border-red-500' : 'border-slate-300'
                }`}
              />
              {confirmPassword && password !== confirmPassword && (
                <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  Passwords do not match
                </p>
              )}
            </div>

            {error && !error.includes('created') && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {error && error.includes('created') && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <p className="text-sm text-green-700">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !isFormValid}
              className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-4 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 shadow-lg"
            >
              {loading ? (
                <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <UserPlus className="w-5 h-5" />
                  Create Account
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-slate-600">
              Already have an account?{' '}
              <button
                onClick={() => onNavigate('staffLogin')}
                className="text-teal-600 hover:text-teal-700 font-semibold hover:underline"
              >
                Sign In
              </button>
            </p>
          </div>
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={() => onNavigate('home')}
            className="text-sm text-slate-500 hover:text-slate-800 hover:underline"
          >
            Back to Customer Portal
          </button>
        </div>
      </div>
    </div>
  );
};

// ==========================================
// VIEW 4: STAFF LOGIN (REPLACE ENTIRE FUNCTION)
// ==========================================
const StaffLogin = ({ onNavigate, onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { isSignedIn } = await signIn({
        username: email,
        password: password
      });

      if (isSignedIn) {
        onLogin();
        onNavigate('staff');
      }
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-slate-700 rounded-full mb-4 shadow-lg">
            <LogIn className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-slate-800 mb-2">Staff Login</h1>
          <p className="text-slate-600">Access the staff dashboard</p>
        </div>

        <div className="bg-white rounded-xl shadow-xl p-8">
          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                <Mail className="w-4 h-4 text-slate-500" />
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your.email@company.com"
                required
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-500 outline-none bg-slate-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                <Lock className="w-4 h-4 text-slate-500" />
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-500 outline-none bg-slate-50"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-slate-700 hover:bg-slate-800 text-white font-bold py-4 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 shadow-lg"
            >
              {loading ? (
                <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <LogIn className="w-5 h-5" />
                  Sign In
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-slate-600">
              Don't have an account?{' '}
              <button
                onClick={() => onNavigate('staffSignup')}
                className="text-teal-600 hover:text-teal-700 font-semibold hover:underline"
              >
                Create Account
              </button>
            </p>
          </div>
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={() => onNavigate('home')}
            className="text-sm text-slate-500 hover:text-slate-800 hover:underline"
          >
            Back to Customer Portal
          </button>
        </div>
      </div>
    </div>
  );
};

// ==========================================
// VIEW 4: STAFF DASHBOARD
// ==========================================
const StaffDashboard = ({ onNavigate, isAuthenticated }) => {
  const [summary, setSummary] = useState({ tickets: [] });
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [currentTicket, setCurrentTicket] = useState(null);
  const [activeQueueId, setActiveQueueId] = useState('');
  const [tempQueueInput, setTempQueueInput] = useState('');
  const [selectedTrafficPeriod, setSelectedTrafficPeriod] = useState('AFTERNOON');
  const [queueSelected, setQueueSelected] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      onNavigate('staffLogin');
    }
  }, [isAuthenticated, onNavigate]);

  useEffect(() => {
    if (queueSelected && activeQueueId) {
      fetchSummary();
      const interval = setInterval(fetchSummary, 60000); // 60 seconds
      return () => clearInterval(interval);
    }
  }, [activeQueueId, queueSelected]);

  const fetchSummary = async () => {
    if (!activeQueueId) return;
    try {
      const data = await apiService.getStaffSummary(activeQueueId);
      setSummary(data);
      const serving = data.tickets?.find(t => t.status === 'BEING_SERVED');
      setCurrentTicket(serving?.ticketNumber || null);
    } catch (error) {
      setToast({ message: 'Failed to load queue data', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchQueue = (e) => {
    e.preventDefault();
    if (tempQueueInput.trim()) {
      setActiveQueueId(tempQueueInput);
      setQueueSelected(true);
      setLoading(true);
      setToast({ message: `Switched to ${tempQueueInput}`, type: 'success' });
    }
  };

  const handleCallNext = async () => {
    try {
      const data = await apiService.callNextTicket(activeQueueId);
      setToast({ message: data.servedTicket ? `Called ticket: ${data.servedTicket}` : 'Queue is empty', type: 'success' });
      fetchSummary();
    } catch (error) {
      setToast({ message: 'Failed to call next customer', type: 'error' });
    }
  };

  const handleComplete = async () => {
    if (!currentTicket) {
      setToast({ message: 'No ticket currently being served', type: 'error' });
      return;
    }
    try {
      await apiService.completeTicket(currentTicket, activeQueueId);
      setToast({ message: 'Ticket completed successfully', type: 'success' });
      fetchSummary();
    } catch (error) {
      setToast({ message: 'Failed to complete ticket', type: 'error' });
    }
  };

  const handleTrafficPeriod = async (period) => {
    try {
      await apiService.updateTrafficSettings(period, activeQueueId);
      setSelectedTrafficPeriod(period);
      setToast({ message: `Traffic set to ${TRAFFIC_PERIODS[period].label}`, type: 'success' });
    } catch (error) {
      setToast({ message: 'Failed to update settings', type: 'error' });
    }
  };

  const waitingTickets = summary.tickets?.filter(t => t.status === 'WAITING') || [];
  const totalWaiting = waitingTickets.length;

  if (!queueSelected) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <Settings className="w-16 h-16 text-slate-700 mx-auto mb-4" />
            <h1 className="text-3xl font-bold text-slate-800 mb-2">Select Queue</h1>
            <p className="text-slate-600">Choose which queue to manage</p>
          </div>
          <div className="bg-white rounded-xl shadow-xl p-8">
            <form onSubmit={handleSwitchQueue} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Queue Name</label>
                <input
                  type="text"
                  value={tempQueueInput}
                  onChange={(e) => setTempQueueInput(e.target.value)}
                  placeholder="e.g. Registrar, Support, Main"
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-500 outline-none bg-slate-50"
                />
              </div>
              <button
                type="submit"
                className="w-full bg-slate-700 hover:bg-slate-800 text-white font-bold py-4 rounded-lg"
              >
                Load Queue
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      
      <div className="bg-white shadow-sm border-b px-6 py-4 sticky top-0 z-20">
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center gap-4">
            <button onClick={() => onNavigate('home')} className="p-2 hover:bg-slate-100 rounded-full">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-2xl font-bold text-slate-800">Staff Dashboard</h1>
          </div>
          
          <form onSubmit={handleSwitchQueue} className="flex items-center gap-2 bg-slate-50 p-1.5 rounded-lg border">
            <MapPin className="w-4 h-4 text-slate-400 ml-2" />
            <input 
              className="bg-transparent border-none text-sm font-medium text-slate-700 w-40 outline-none"
              value={tempQueueInput}
              onChange={(e) => setTempQueueInput(e.target.value)}
              placeholder="Queue Name"
            />
            <button type="submit" className="bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold px-3 py-2 rounded-md">
              Switch
            </button>
          </form>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border p-6 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500 mb-1">Waiting in {activeQueueId}</p>
              <p className="text-3xl font-bold text-slate-800">{totalWaiting}</p>
            </div>
            <div className="bg-teal-50 rounded-full p-4">
              <Users className="w-8 h-8 text-teal-600" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-6 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500 mb-1">Avg. Wait Time</p>
              <p className="text-3xl font-bold text-slate-800">
                {totalWaiting > 0 ? etaCalculator.calculateETA(1, selectedTrafficPeriod) : 0}m
              </p>
            </div>
            <div className="bg-blue-50 rounded-full p-4">
              <Clock className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-6 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500 mb-1">Now Serving</p>
              <p className="text-xl font-bold text-teal-600">{currentTicket || 'Idle'}</p>
            </div>
            <div className="bg-green-50 rounded-full p-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                <PlayCircle className="w-5 h-5 text-teal-500" />
                Queue Actions
              </h2>
              <div className="space-y-3">
                <button
                  onClick={handleCallNext}
                  className="w-full bg-teal-500 hover:bg-teal-600 text-white font-semibold py-4 rounded-lg"
                >
                  Call Next Ticket
                </button>
                <button
                  onClick={handleComplete}
                  disabled={!currentTicket}
                  className="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-4 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <CheckSquare className="w-5 h-5" />
                  Mark Completed
                </button>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                <Settings className="w-5 h-5 text-slate-500" />
                Traffic Speed
              </h2>
              <div className="grid grid-cols-1 gap-3">
                {Object.entries(TRAFFIC_PERIODS).map(([key, period]) => (
                  <button
                    key={key}
                    onClick={() => handleTrafficPeriod(key)}
                    className={`flex items-center justify-between px-4 py-3 rounded-lg border border-${period.color}-200 bg-${period.color}-50 text-${period.color}-800 hover:bg-${period.color}-100`}
                  >
                    <span className="text-sm font-semibold">{period.label}</span>
                    <span className="text-xs bg-white/50 px-2 py-1 rounded">{period.serviceTime}m</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-slate-800 rounded-xl shadow-sm p-6 text-center text-white">
              <LinkIcon className="w-8 h-8 mx-auto mb-2 text-teal-400" />
              <p className="text-sm text-slate-300 mb-1">Share this queue:</p>
              <code className="text-xs bg-black/30 px-2 py-1 rounded font-mono break-all">
                ?queue={activeQueueId}
              </code>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border overflow-hidden flex flex-col min-h-[500px]">
              <div className="px-6 py-4 border-b bg-slate-50 flex justify-between items-center">
                <h2 className="text-lg font-bold text-slate-800">Live Queue: {activeQueueId}</h2>
                <button onClick={fetchSummary} className="p-2 hover:bg-white rounded-full" title="Refresh">
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>

              <div className="flex-1 overflow-auto">
                {loading && summary.tickets?.length === 0 ? (
                  <div className="flex justify-center items-center h-40">
                    <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                ) : summary.tickets?.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                    <Users className="w-12 h-12 mb-2 opacity-20" />
                    <p>Queue is empty</p>
                  </div>
                ) : (
                  <table className="w-full text-left">
                    <thead className="bg-slate-50 sticky top-0">
                      <tr>
                        <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Ticket</th>
                        <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Status</th>
                        <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Joined</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {summary.tickets?.map((ticket, idx) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="px-6 py-4">
                            <span className="font-mono font-medium text-slate-700">{ticket.ticketNumber}</span>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              ticket.status === 'BEING_SERVED' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                            }`}>
                              {ticket.status === 'BEING_SERVED' ? 'Serving' : 'Waiting'}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-500">
                            {ticket.joinTime ? new Date(ticket.joinTime / 1000).toLocaleTimeString() : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ==========================================
// MAIN APP (ROUTING)
// ==========================================
export default function App() {
  const [currentView, setCurrentView] = useState('home');
  const [currentTicket, setCurrentTicket] = useState(null);
  const [currentQueueId, setCurrentQueueId] = useState('');
  const [isStaffAuthenticated, setIsStaffAuthenticated] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const session = await fetchAuthSession();
        if (session.tokens?.accessToken) {
          setIsStaffAuthenticated(true);
        }
      } catch (err) {
        setIsStaffAuthenticated(false);
      }
    };
    
    checkAuth();
  }, []);

  
  const handleNavigate = (view, data = null) => {
    setCurrentView(view);
    if (data) {
      if (typeof data === 'string') {
        setCurrentTicket(data);
      } else {
        setCurrentTicket(data.ticketId);
        setCurrentQueueId(data.queueId);
      }
    }
  };

  const handleStaffLogin = () => {
    setIsStaffAuthenticated(true);
  };

  return (
    <div>
      {currentView === 'home' && <CustomerLanding onNavigate={handleNavigate} />}
      {currentView === 'status' && <StatusPage ticketId={currentTicket} queueId={currentQueueId} onNavigate={handleNavigate} />}
      {currentView === 'staffSignup' && <StaffSignup onNavigate={handleNavigate} onLogin={handleStaffLogin} />}
      {currentView === 'staffLogin' && <StaffLogin onNavigate={handleNavigate} onLogin={handleStaffLogin} />}
      {currentView === 'staff' && <StaffDashboard onNavigate={handleNavigate} isAuthenticated={isStaffAuthenticated} />}
    </div>
  );
}