import React, { useState, useEffect } from 'react';
import { Users, Clock, CheckCircle, AlertCircle, Settings, PlayCircle, CheckSquare, ArrowLeft } from 'lucide-react';
import './index.css';
const API_BASE_URL = "YOUR_API_GATEWAY_URL_HERE";

// Toast Notification Component
const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg ${
      type === 'success' ? 'bg-teal-500' : 'bg-red-500'
    } text-white`}>
      {message}
    </div>
  );
};

// Student Landing Page
const StudentLanding = ({ onNavigate }) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const handleJoinQueue = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/queue/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      
      if (!response.ok) throw new Error('Failed to join queue');
      
      const data = await response.json();
      onNavigate('status', data.ticketNumber);
    } catch (error) {
      setToast({ message: 'Failed to join queue. Please try again.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-md mx-auto">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-teal-500 rounded-full mb-4">
              <Users className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-slate-800 mb-2">QueueEscape</h1>
            <p className="text-slate-600">Join the virtual queue and track your position</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-semibold text-slate-800 mb-6">Join Queue</h2>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Email Address (Optional)
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your.email@university.edu"
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none transition"
                />
                <p className="text-xs text-slate-500 mt-2">
                  Receive updates about your queue status
                </p>
              </div>

              <button
                onClick={handleJoinQueue}
                disabled={loading}
                className="w-full bg-teal-500 hover:bg-teal-600 text-white font-semibold py-4 rounded-lg transition duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <PlayCircle className="w-5 h-5" />
                    Join Queue Now
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <h3 className="font-semibold text-blue-900 mb-1">How it works</h3>
                <p className="text-sm text-blue-800">
                  After joining, you'll receive a ticket number. Keep this page open to track your position in real-time.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 text-center">
            <button
              onClick={() => onNavigate('staff')}
              className="text-sm text-slate-600 hover:text-slate-800 underline"
            >
              Staff Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Status Page
const StatusPage = ({ ticketId, onNavigate }) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/queue/status/main_queue/${ticketId}`);
        if (!response.ok) throw new Error('Failed to fetch status');
        
        const data = await response.json();
        setStatus(data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch status. Please check your ticket number.');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [ticketId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center px-4">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-800 mb-2">Error</h2>
          <p className="text-slate-600 mb-6">{error}</p>
          <button
            onClick={() => onNavigate('home')}
            className="bg-teal-500 hover:bg-teal-600 text-white font-semibold py-3 px-6 rounded-lg transition"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  const isBeingServed = status?.status === 'BEING_SERVED';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-2xl mx-auto">
          <button
            onClick={() => onNavigate('home')}
            className="flex items-center gap-2 text-slate-600 hover:text-slate-800 mb-6 transition"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </button>

          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-slate-800 mb-2">QueueEscape</h1>
            <p className="text-slate-600">Your Queue Status</p>
          </div>

          <div className={`rounded-xl shadow-lg p-8 transition-all duration-500 ${
            isBeingServed ? 'bg-gradient-to-br from-green-400 to-green-500' : 'bg-white'
          }`}>
            <div className="text-center mb-8">
              <p className={`text-sm font-medium mb-2 ${isBeingServed ? 'text-green-100' : 'text-slate-600'}`}>
                Your Ticket Number
              </p>
              <div className={`text-4xl font-bold tracking-wider ${isBeingServed ? 'text-white' : 'text-slate-800'}`}>
                {ticketId}
              </div>
            </div>

            {isBeingServed ? (
              <div className="text-center">
                <CheckCircle className="w-20 h-20 text-white mx-auto mb-4" />
                <h2 className="text-3xl font-bold text-white mb-2">It's Your Turn!</h2>
                <p className="text-green-100 text-lg">Please proceed to the counter now</p>
              </div>
            ) : (
              <div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                  <div className="bg-slate-50 rounded-lg p-6 text-center">
                    <Users className="w-8 h-8 text-teal-500 mx-auto mb-3" />
                    <p className="text-sm text-slate-600 mb-1">Current Position</p>
                    <p className="text-3xl font-bold text-slate-800">{status?.position || 0}</p>
                    <p className="text-xs text-slate-500 mt-2">
                      {status?.position === 1 ? 'You\'re next!' : `${status?.position || 0} people ahead`}
                    </p>
                  </div>

                  <div className="bg-slate-50 rounded-lg p-6 text-center">
                    <Clock className="w-8 h-8 text-blue-500 mx-auto mb-3" />
                    <p className="text-sm text-slate-600 mb-1">Estimated Wait</p>
                    <p className="text-3xl font-bold text-slate-800">{status?.estimatedWaitMinutes || 0}</p>
                    <p className="text-xs text-slate-500 mt-2">minutes</p>
                  </div>
                </div>

                <div className="mb-6">
                  <div className="flex justify-between text-sm text-slate-600 mb-2">
                    <span>Waiting...</span>
                    <span>Your Turn</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                    <div 
                      className="bg-teal-500 h-3 rounded-full transition-all duration-500"
                      style={{ width: `${Math.max(10, 100 - (status?.position || 0) * 10)}%` }}
                    />
                  </div>
                </div>

                {status?.note && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm text-blue-800">{status.note}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="text-center mt-6">
            <p className="text-sm text-slate-500">
              <span className="inline-block w-2 h-2 bg-teal-500 rounded-full animate-pulse mr-2" />
              Auto-updating every 5 seconds
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Staff Dashboard
const StaffDashboard = ({ onNavigate }) => {
  const [summary, setSummary] = useState({ tickets: [] });
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const [currentTicket, setCurrentTicket] = useState(null);

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(fetchSummary, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchSummary = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/queue/staff/summary`);
      if (!response.ok) throw new Error('Failed to fetch summary');
      
      const data = await response.json();
      setSummary(data);
      
      const serving = data.tickets?.find(t => t.status === 'BEING_SERVED');
      setCurrentTicket(serving?.ticketNumber || null);
    } catch (error) {
      console.error('Failed to fetch summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCallNext = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/queue/staff/next`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) throw new Error('Failed to call next');
      
      const data = await response.json();
      setToast({ message: `Called ticket: ${data.ticketNumber}`, type: 'success' });
      fetchSummary();
    } catch (error) {
      setToast({ message: 'Failed to call next student', type: 'error' });
    }
  };

  const handleComplete = async () => {
    if (!currentTicket) {
      setToast({ message: 'No ticket currently being served', type: 'error' });
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/queue/staff/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticketNumber: currentTicket })
      });
      
      if (!response.ok) throw new Error('Failed to complete');
      
      setToast({ message: 'Ticket completed successfully', type: 'success' });
      fetchSummary();
    } catch (error) {
      setToast({ message: 'Failed to complete ticket', type: 'error' });
    }
  };

  const handlePeakPeriod = async (period) => {
    try {
      const response = await fetch(`${API_BASE_URL}/queue/staff/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ peak_period: period })
      });
      
      if (!response.ok) throw new Error('Failed to update settings');
      
      setToast({ message: `Traffic set to ${period.toLowerCase()}`, type: 'success' });
    } catch (error) {
      setToast({ message: 'Failed to update settings', type: 'error' });
    }
  };

  const waitingTickets = summary.tickets?.filter(t => t.status === 'WAITING') || [];
  const totalWaiting = waitingTickets.length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <button
            onClick={() => onNavigate('home')}
            className="flex items-center gap-2 text-slate-600 hover:text-slate-800 mb-4 transition"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </button>
          <h1 className="text-3xl font-bold text-slate-800 mb-2">Staff Dashboard</h1>
          <p className="text-slate-600">Manage queue and serve students</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center gap-4">
              <div className="bg-teal-100 rounded-full p-3">
                <Users className="w-6 h-6 text-teal-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Total Waiting</p>
                <p className="text-3xl font-bold text-slate-800">{totalWaiting}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center gap-4">
              <div className="bg-blue-100 rounded-full p-3">
                <Clock className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Avg. Wait Time</p>
                <p className="text-3xl font-bold text-slate-800">
                  {totalWaiting > 0 ? Math.round(totalWaiting * 3) : 0}m
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center gap-4">
              <div className="bg-green-100 rounded-full p-3">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Currently Serving</p>
                <p className="text-xl font-bold text-slate-800">{currentTicket || 'None'}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Settings className="w-5 h-5 text-slate-700" />
            <h2 className="text-xl font-semibold text-slate-800">Traffic Control</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => handlePeakPeriod('MORNING')}
              className="bg-green-100 hover:bg-green-200 text-green-800 font-medium py-3 px-4 rounded-lg transition"
            >
              Morning (Quiet)
            </button>
            <button
              onClick={() => handlePeakPeriod('AFTERNOON')}
              className="bg-yellow-100 hover:bg-yellow-200 text-yellow-800 font-medium py-3 px-4 rounded-lg transition"
            >
              Afternoon (Moderate)
            </button>
            <button
              onClick={() => handlePeakPeriod('EVENING')}
              className="bg-red-100 hover:bg-red-200 text-red-800 font-medium py-3 px-4 rounded-lg transition"
            >
              Evening (Busy)
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-slate-800 mb-4">Queue Controls</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={handleCallNext}
              className="bg-teal-500 hover:bg-teal-600 text-white font-semibold py-4 rounded-lg transition flex items-center justify-center gap-2"
            >
              <PlayCircle className="w-5 h-5" />
              Call Next Student
            </button>
            <button
              onClick={handleComplete}
              disabled={!currentTicket}
              className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-4 rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CheckSquare className="w-5 h-5" />
              Complete Current
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-slate-800">Live Queue</h2>
            <span className="text-sm text-slate-500">
              <span className="inline-block w-2 h-2 bg-teal-500 rounded-full animate-pulse mr-2" />
              Auto-updating every 10 seconds
            </span>
          </div>

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : summary.tickets?.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No tickets in queue</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">Ticket</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">Status</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">Email</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">Join Time</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.tickets?.map((ticket, idx) => (
                    <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50 transition">
                      <td className="py-4 px-4 font-mono font-semibold text-slate-800">
                        {ticket.ticketNumber}
                      </td>
                      <td className="py-4 px-4">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                          ticket.status === 'BEING_SERVED' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {ticket.status === 'BEING_SERVED' ? 'Being Served' : 'Waiting'}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-slate-600 text-sm">
                        {ticket.email || '—'}
                      </td>
                      <td className="py-4 px-4 text-slate-600 text-sm">
                        {ticket.joinTime ? new Date(ticket.joinTime).toLocaleTimeString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Main App Component
export default function App() {
  const [currentView, setCurrentView] = useState('home');
  const [currentTicket, setCurrentTicket] = useState(null);

  const handleNavigate = (view, ticketId = null) => {
    setCurrentView(view);
    if (ticketId) setCurrentTicket(ticketId);
  };

  return (
    <div>
      {currentView === 'home' && <StudentLanding onNavigate={handleNavigate} />}
      {currentView === 'status' && <StatusPage ticketId={currentTicket} onNavigate={handleNavigate} />}
      {currentView === 'staff' && <StaffDashboard onNavigate={handleNavigate} />}
    </div>
  );
}