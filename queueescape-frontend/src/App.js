import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

const LandingPage = () => <h1>Welcome to QueueEscape!</h1>;
const TicketStatus = () => <h1>Your Ticket Status</h1>;
const StaffDashboard = () => <h1>Staff Dashboard</h1>;

function App() {
  return (
    <Router>
      <Routes>
        {/* Landing page for joining the queue */}
        <Route path="/" element={<LandingPage />} />
        
        {/* Ticket status page */}
        <Route path="/ticket/:queueId/:ticketNumber" element={<TicketStatus />} />
        
        {/* Staff view */}
        <Route path="/staff" element={<StaffDashboard />} />
        
        {/* Fallback */}
        <Route path="*" element={<h1>404 - Not Found</h1>} />
      </Routes>
    </Router>
  );
}

export default App;