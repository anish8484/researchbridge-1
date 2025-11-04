import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import '@/App.css';
import Landing from './components/Landing';
import Auth from './components/Auth';
import PatientDashboard from './components/PatientDashboard';
import ResearcherDashboard from './components/ResearcherDashboard';
import ProfileSetup from './components/ProfileSetup';
import ClinicalTrials from './components/ClinicalTrials';
import Publications from './components/Publications';
import HealthExperts from './components/HealthExperts';
import Collaborators from './components/Collaborators';
import Forums from './components/Forums';
import Favorites from './components/Favorites';
import Chat from './components/Chat';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.json())
        .then(data => {
          setUser(data);
          setLoading(false);
        })
        .catch(() => {
          localStorage.removeItem('token');
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-purple-50"><div className="text-xl">Loading...</div></div>;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={user ? <Navigate to={user.user_type === 'patient' ? '/patient/dashboard' : '/researcher/dashboard'} /> : <Landing />} />
        <Route path="/auth" element={user ? <Navigate to="/" /> : <Auth setUser={setUser} />} />
        <Route path="/profile-setup" element={user ? <ProfileSetup user={user} /> : <Navigate to="/auth" />} />
        <Route path="/patient/dashboard" element={user && user.user_type === 'patient' ? <PatientDashboard user={user} setUser={setUser} /> : <Navigate to="/" />} />
        <Route path="/researcher/dashboard" element={user && user.user_type === 'researcher' ? <ResearcherDashboard user={user} setUser={setUser} /> : <Navigate to="/" />} />
        <Route path="/clinical-trials" element={user ? <ClinicalTrials user={user} /> : <Navigate to="/" />} />
        <Route path="/publications" element={user ? <Publications user={user} /> : <Navigate to="/" />} />
        <Route path="/health-experts" element={user && user.user_type === 'patient' ? <HealthExperts user={user} /> : <Navigate to="/" />} />
        <Route path="/collaborators" element={user && user.user_type === 'researcher' ? <Collaborators user={user} /> : <Navigate to="/" />} />
        <Route path="/forums" element={user ? <Forums user={user} /> : <Navigate to="/" />} />
        <Route path="/favorites" element={user ? <Favorites user={user} /> : <Navigate to="/" />} />
        <Route path="/chat/:userId" element={user ? <Chat user={user} /> : <Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
