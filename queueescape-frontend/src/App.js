import React, { useState, useEffect } from 'react';
import { Users, Clock, CheckCircle, AlertCircle, Settings, PlayCircle, CheckSquare, ArrowLeft, RefreshCw, MapPin, Link as LinkIcon } from 'lucide-react';
import './index.css';

// ==========================================
// CONFIGURATION
// ==========================================
const API_BASE_URL = "https://tbmndj28ib.execute-api.us-east-1.amazonaws.com/dev"; 

// ==========================================
// SHARED COMPONENTS
// ==========================================

// Toast Notification
const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg ${
      type === 'success' ? 'bg-teal-500' : 'bg-red-500'
    } text-white transition-all transform duration-300 ease-in-out animate-in slide-in-from-top-2`}>
      {message}
    </div>
  );
};

// ==========================================
// VIEW 1: STUDENT LANDING
// ==========================================
const StudentLanding = ({ onNavigate }) => {
  const [email, setEmail] = useState('');
  const [queueId, setQueueId] = useState('main_queue'); 
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  // Auto-fill Queue Name from URL (e.g., ?queue=Registrar)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const queueParam = params.get('queue');
    if (queueParam) {
      setQueueId(queueParam);
    }
  }, []);

  const handleJoinQueue = async (e) => {
    e.preventDefault();
    if (!queueId.trim()) {
        setToast({ message: 'Please enter a Queue Name', type: 'error' });
        return;
    }

    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/queue/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, queueId }) 
      });
      
      if (!response.ok) throw new Error('Failed to join queue');
      
      const data = await response.json();
      // Pass both ticket AND queueId to the status page
      onNavigate('status', { ticketId: data.ticketNumber, queueId: queueId });
    } catch (error) {
      setToast({ message: 'Failed to join queue. Please try again.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-teal-500 rounded-full mb-4 shadow-lg shadow-teal-200">
            <Users className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-slate-800 mb-2 tracking-tight">QueueEscape</h1>
          <p className="text-slate-600">Join the line from anywhere.</p>
        </div>

        <div className="bg-white rounded-xl shadow-xl p-8 border border-slate-100">
          <h2 className="text-2xl font-semibold text-slate-800 mb-6 border-b pb-4">Join Queue</h2>
          
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-teal-500" />
                Queue Name
              </label>
              <input
                type="text"
                value={queueId}
                onChange={(e) => setQueueId(e.target.value)}
                placeholder="e.g. Registrar, Cafeteria"
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none transition bg-slate-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Email Address <span className="text-slate-400 font-normal">(Optional)</span>
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your.email@university.edu"
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none transition bg-slate-50"
              />
            </div>

            <button
              onClick={handleJoinQueue}
              disabled={loading}
              className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-4 rounded-lg transition duration-200 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform active:scale-95"
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
          </div>
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={() => onNavigate('staff')}
            className="text-sm text-slate-500 hover:text-slate-800 hover:underline transition"
          >
            Access Staff Dashboard
          </button>
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
        // Fetch status for specific Queue ID
        const response = await fetch(`${API_BASE_URL}/queue/status/${queueId}/${ticketId}`);
        if (!response.ok) throw new Error('Failed to fetch status');
        
        const data = await response.json();
        setStatus(data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch status. The ticket might be invalid or expired.');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [ticketId, queueId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-500 font-medium animate-pulse">Locating ticket...</p>
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
            className="bg-teal-500 hover:bg-teal-600 text-white font-semibold py-3 px-6 rounded-lg transition shadow-md"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  const isBeingServed = status?.status === 'BEING_SERVED';

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => onNavigate('home')}
          className="flex items-center gap-2 text-slate-500 hover:text-slate-800 mb-8 transition font-medium"
        >
          <ArrowLeft className="w-5 h-5" />
          Leave Queue
        </button>

        <div className="text-center mb-8">
            <span className="inline-block py-1 px-4 rounded-full bg-slate-200 text-slate-700 text-sm font-bold tracking-wide mb-3">
                {queueId}
            </span>
            <h1 className="text-3xl font-bold text-slate-800">Your Status</h1>
        </div>

        <div className={`rounded-2xl shadow-xl p-8 transition-all duration-700 overflow-hidden relative ${
          isBeingServed ? 'bg-gradient-to-br from-teal-500 to-emerald-600 transform scale-105' : 'bg-white'
        }`}>
          {/* Status Card Header */}
          <div className="text-center mb-10 relative z-10">
            <p className={`text-xs font-bold uppercase tracking-widest mb-2 ${isBeingServed ? 'text-teal-100' : 'text-slate-400'}`}>
              Ticket Number
            </p>
            <div className={`text-5xl font-mono font-bold tracking-wider ${isBeingServed ? 'text-white' : 'text-slate-800'}`}>
              {ticketId}
            </div>
          </div>

          {isBeingServed ? (
            <div className="text-center relative z-10 animate-in fade-in zoom-in duration-500">
              <div className="bg-white/20 rounded-full p-4 w-24 h-24 mx-auto mb-6 flex items-center justify-center backdrop-blur-sm">
                 <CheckCircle className="w-14 h-14 text-white" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-2">It's Your Turn!</h2>
              <p className="text-teal-50 text-lg">Please proceed to the counter.</p>
            </div>
          ) : (
            <div>
              <div className="grid grid-cols-2 gap-6 mb-8">
                <div className="bg-slate-50 rounded-xl p-6 text-center border border-slate-100">
                  <Users className="w-8 h-8 text-teal-500 mx-auto mb-3" />
                  <p className="text-sm font-medium text-slate-500 mb-1">Position</p>
                  <p className="text-3xl font-bold text-slate-800">{status?.position || 0}</p>
                  <p className="text-xs text-slate-400 mt-2 font-medium">
                    {status?.position === 1 ? 'You represent next!' : 'People ahead'}
                  </p>
                </div>

                <div className="bg-slate-50 rounded-xl p-6 text-center border border-slate-100">
                  <Clock className="w-8 h-8 text-blue-500 mx-auto mb-3" />
                  <p className="text-sm font-medium text-slate-500 mb-1">Est. Wait</p>
                  <p className="text-3xl font-bold text-slate-800">{status?.estimatedWaitMinutes || 0}</p>
                  <p className="text-xs text-slate-400 mt-2 font-medium">minutes</p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mb-6">
                <div className="flex justify-between text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                  <span>In Queue</span>
                  <span>Your Turn</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-4 overflow-hidden shadow-inner">
                  <div 
                    className="bg-teal-500 h-4 rounded-full transition-all duration-1000 ease-out"
                    style={{ width: `${Math.max(5, 100 - (status?.position || 0) * 10)}%` }}
                  />
                </div>
              </div>

              {/* Dynamic Note from Backend */}
              {status?.note && (
                <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex items-start gap-3">
                   <Clock className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                   <p className="text-sm text-blue-800">{status.note}</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="text-center mt-8">
          <p className="text-sm text-slate-400 flex items-center justify-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500"></span>
            </span>
            Live updates
          </p>
        </div>
      </div>
    </div>
  );
};

// ==========================================
// VIEW 3: STAFF DASHBOARD
// ==========================================
const StaffDashboard = ({ onNavigate }) => {
  const [summary, setSummary] = useState({ tickets: [] });
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const [currentTicket, setCurrentTicket] = useState(null);
  
  // State for selecting which queue to manage
  const [activeQueueId, setActiveQueueId] = useState('main_queue'); 
  const [tempQueueInput, setTempQueueInput] = useState('main_queue');

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(fetchSummary, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, [activeQueueId]); // Refetch if queueId changes

  const fetchSummary = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/queue/staff/summary?queueId=${activeQueueId}`);
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

  const handleSwitchQueue = (e) => {
    e.preventDefault();
    if(tempQueueInput.trim()) {
        setActiveQueueId(tempQueueInput);
        setLoading(true);
        setToast({ message: `Switched to ${tempQueueInput}`, type: 'success' });
    }
  };

  const handleCallNext = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/queue/staff/next`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ queueId: activeQueueId }) 
      });
      
      if (!response.ok) throw new Error('Failed to call next');
      
      const data = await response.json();
      if(data.servedTicket) {
        setToast({ message: `Called ticket: ${data.servedTicket}`, type: 'success' });
      } else {
        setToast({ message: data.message || 'Queue is empty', type: 'success' });
      }
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
        body: JSON.stringify({ ticketNumber: currentTicket, queueId: activeQueueId })
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
        body: JSON.stringify({ peak_period: period, queueId: activeQueueId })
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
    <div className="min-h-screen bg-slate-100">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      
      {/* Top Navbar */}
      <div className="bg-white shadow-sm border-b border-slate-200 px-6 py-4 sticky top-0 z-20">
        <div className="container mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-4">
                <button
                    onClick={() => onNavigate('home')}
                    className="p-2 hover:bg-slate-100 rounded-full text-slate-500 transition"
                    title="Back to Home"
                >
                    <ArrowLeft className="w-5 h-5" />
                </button>
                <h1 className="text-2xl font-bold text-slate-800">Staff Dashboard</h1>
            </div>
            
            {/* Queue Switcher */}
            <form onSubmit={handleSwitchQueue} className="flex items-center gap-2 bg-slate-50 p-1.5 rounded-lg border border-slate-200">
                <MapPin className="w-4 h-4 text-slate-400 ml-2" />
                <input 
                    className="bg-transparent border-none focus:ring-0 text-sm font-medium text-slate-700 w-40 placeholder-slate-400 outline-none"
                    value={tempQueueInput}
                    onChange={(e) => setTempQueueInput(e.target.value)}
                    placeholder="Queue Name"
                />
                <button type="submit" className="bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold px-3 py-2 rounded-md transition shadow-sm">
                    Switch
                </button>
            </form>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex items-center justify-between">
            <div>
                <p className="text-sm font-medium text-slate-500 mb-1">Waiting in {activeQueueId}</p>
                <p className="text-3xl font-bold text-slate-800">{totalWaiting}</p>
            </div>
            <div className="bg-teal-50 rounded-full p-4">
               <Users className="w-8 h-8 text-teal-600" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex items-center justify-between">
            <div>
                <p className="text-sm font-medium text-slate-500 mb-1">Avg. Wait Time</p>
                <p className="text-3xl font-bold text-slate-800">
                  {totalWaiting > 0 ? Math.round(totalWaiting * 5) : 0}m
                </p>
            </div>
            <div className="bg-blue-50 rounded-full p-4">
               <Clock className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex items-center justify-between">
             <div>
                <p className="text-sm font-medium text-slate-500 mb-1">Now Serving</p>
                <p className="text-xl font-bold text-teal-600 truncate max-w-[140px]">{currentTicket || 'Idle'}</p>
            </div>
            <div className="bg-green-50 rounded-full p-4">
               <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column: Actions */}
            <div className="lg:col-span-1 space-y-6">
                
                {/* Main Actions */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                    <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                        <PlayCircle className="w-5 h-5 text-teal-500" />
                        Queue Actions
                    </h2>
                    <div className="space-y-3">
                        <button
                        onClick={handleCallNext}
                        className="w-full bg-teal-500 hover:bg-teal-600 text-white font-semibold py-4 rounded-lg transition shadow-md hover:shadow-lg active:scale-95 flex items-center justify-center gap-2"
                        >
                        Call Next Ticket
                        </button>
                        <button
                        onClick={handleComplete}
                        disabled={!currentTicket}
                        className="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-4 rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                        <CheckSquare className="w-5 h-5" />
                        Mark Completed
                        </button>
                    </div>
                </div>

                {/* Traffic Settings */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                    <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                        <Settings className="w-5 h-5 text-slate-500" />
                        Traffic Speed
                    </h2>
                    <div className="grid grid-cols-1 gap-3">
                        <button
                        onClick={() => handlePeakPeriod('MORNING')}
                        className="flex items-center justify-between px-4 py-3 rounded-lg border border-green-200 bg-green-50 text-green-800 hover:bg-green-100 transition group"
                        >
                        <span className="text-sm font-semibold">Morning</span>
                        <span className="text-xs bg-white/50 px-2 py-1 rounded group-hover:bg-white">Fast (5m)</span>
                        </button>
                        <button
                        onClick={() => handlePeakPeriod('AFTERNOON')}
                        className="flex items-center justify-between px-4 py-3 rounded-lg border border-yellow-200 bg-yellow-50 text-yellow-800 hover:bg-yellow-100 transition group"
                        >
                        <span className="text-sm font-semibold">Afternoon</span>
                        <span className="text-xs bg-white/50 px-2 py-1 rounded group-hover:bg-white">Normal (8m)</span>
                        </button>
                        <button
                        onClick={() => handlePeakPeriod('EVENING')}
                        className="flex items-center justify-between px-4 py-3 rounded-lg border border-red-200 bg-red-50 text-red-800 hover:bg-red-100 transition group"
                        >
                        <span className="text-sm font-semibold">Evening</span>
                        <span className="text-xs bg-white/50 px-2 py-1 rounded group-hover:bg-white">Slow (15m)</span>
                        </button>
                    </div>
                </div>
                
                {/* QR Code Helper (Visual Only) */}
                <div className="bg-slate-800 rounded-xl shadow-sm p-6 text-center text-white">
                    <LinkIcon className="w-8 h-8 mx-auto mb-2 text-teal-400" />
                    <p className="text-sm text-slate-300 mb-1">Share this queue:</p>
                    <code className="text-xs bg-black/30 px-2 py-1 rounded font-mono break-all">
                        ?queue={activeQueueId}
                    </code>
                </div>
            </div>

            {/* Right Column: Live List */}
            <div className="lg:col-span-2">
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-full min-h-[500px]">
                    <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
                        <h2 className="text-lg font-bold text-slate-800">Live Queue: {activeQueueId}</h2>
                        <button onClick={fetchSummary} className="p-2 hover:bg-white rounded-full transition text-slate-500" title="Refresh list">
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
                                        <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Ticket</th>
                                        <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                                        <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Joined</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {summary.tickets?.map((ticket, idx) => (
                                        <tr key={idx} className="hover:bg-slate-50 transition">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className="font-mono font-medium text-slate-700">{ticket.ticketNumber}</span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                                    ticket.status === 'BEING_SERVED' 
                                                    ? 'bg-green-100 text-green-800' 
                                                    : 'bg-blue-100 text-blue-800'
                                                }`}>
                                                    {ticket.status === 'BEING_SERVED' ? 'Serving' : 'Waiting'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                                                {/* Convert microsecond timestamp to readable time */}
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
// MAIN APP COMPONENT (ROUTING)
// ==========================================
export default function App() {
  const [currentView, setCurrentView] = useState('home');
  const [currentTicket, setCurrentTicket] = useState(null);
  const [currentQueueId, setCurrentQueueId] = useState('main_queue');

  const handleNavigate = (view, data = null) => {
    setCurrentView(view);
    // Handle data passing (supports simple ID string or complex object)
    if (data) {
        if(typeof data === 'string') {
            setCurrentTicket(data);
        } else {
            setCurrentTicket(data.ticketId);
            setCurrentQueueId(data.queueId);
        }
    }
  };

  return (
    <div>
      {currentView === 'home' && <StudentLanding onNavigate={handleNavigate} />}
      {currentView === 'status' && <StatusPage ticketId={currentTicket} queueId={currentQueueId} onNavigate={handleNavigate} />}
      {currentView === 'staff' && <StaffDashboard onNavigate={handleNavigate} />}
    </div>
  );
}