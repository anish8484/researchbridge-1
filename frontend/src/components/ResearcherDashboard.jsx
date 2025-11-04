import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Microscope, Heart, Users, MessageSquare, Star, LogOut } from 'lucide-react';
import { toast } from 'sonner';

const ResearcherDashboard = ({ user, setUser }) => {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/researchers/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await res.json();
      setDashboard(data);
    } catch (error) {
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
    navigate('/');
  };

  if (loading) {
    return <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center">Loading...</div>;
  }

  return (
    <div data-testid="researcher-dashboard" className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <nav className="px-8 py-6 flex justify-between items-center glass">
        <div className="flex items-center space-x-2">
          <Microscope className="w-8 h-8 text-purple-600" />
          <span className="text-2xl font-bold gradient-text">CuraLink</span>
        </div>
        <div className="flex items-center space-x-4">
          <Button data-testid="favorites-nav" variant="ghost" onClick={() => navigate('/favorites')}>
            <Star className="w-5 h-5 mr-2" />
            Favorites
          </Button>
          <Button data-testid="logout-button" variant="outline" onClick={handleLogout}>
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </div>
      </nav>

      <main className="container mx-auto px-8 py-12 space-y-12">
        <div className="space-y-4">
          <h1 className="text-4xl font-bold gradient-text">Researcher Dashboard</h1>
          {dashboard?.profile && (
            <div className="glass p-4 rounded-lg">
              <p className="text-gray-700">Specialties: <span className="font-semibold">{dashboard.profile.specialties?.join(', ')}</span></p>
              <p className="text-gray-600">Interests: {dashboard.profile.research_interests?.join(', ')}</p>
            </div>
          )}
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { icon: <Heart className="w-6 h-6" />, title: 'My Trials', count: dashboard?.trials?.length || 0, path: '/clinical-trials', color: 'bg-blue-500', testId: 'my-trials-card' },
            { icon: <Users className="w-6 h-6" />, title: 'Collaborators', count: 0, path: '/collaborators', color: 'bg-purple-500', testId: 'collaborators-card' },
            { icon: <MessageSquare className="w-6 h-6" />, title: 'Forums', count: dashboard?.forums?.length || 0, path: '/forums', color: 'bg-pink-500', testId: 'forums-card' },
            { icon: <Star className="w-6 h-6" />, title: 'Publications', count: 0, path: '/publications', color: 'bg-indigo-500', testId: 'publications-card' },
          ].map((item, index) => (
            <Card
              key={index}
              data-testid={item.testId}
              className="card-hover cursor-pointer glass"
              onClick={() => navigate(item.path)}
            >
              <CardContent className="pt-6">
                <div className={`${item.color} w-12 h-12 rounded-full flex items-center justify-center text-white mb-4`}>
                  {item.icon}
                </div>
                <h3 className="text-2xl font-bold">{item.count}</h3>
                <p className="text-gray-600">{item.title}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {dashboard?.trials?.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold mb-6">My Clinical Trials</h2>
            <div className="grid md:grid-cols-2 gap-6">
              {dashboard.trials.map((trial) => (
                <Card key={trial.id} data-testid={`trial-card-${trial.id}`} className="glass card-hover">
                  <CardHeader>
                    <CardTitle className="text-lg">{trial.title}</CardTitle>
                    <CardDescription>
                      <span className="inline-block px-2 py-1 bg-green-100 text-green-700 rounded text-sm">
                        {trial.status}
                      </span>
                    </CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default ResearcherDashboard;
