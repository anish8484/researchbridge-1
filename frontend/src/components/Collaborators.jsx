import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ArrowLeft, Search, User, MessageCircle } from 'lucide-react';
import { toast } from 'sonner';

const Collaborators = ({ user }) => {
  const navigate = useNavigate();
  const [collaborators, setCollaborators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchCollaborators();
  }, []);

  const fetchCollaborators = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/researchers/collaborators`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await res.json();
      setCollaborators(data);
    } catch (error) {
      toast.error('Failed to load collaborators');
    } finally {
      setLoading(false);
    }
  };

  const sendConnectionRequest = async (collaboratorId) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/connection-requests`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ to_user: collaboratorId }),
      });
      toast.success('Connection request sent!');
    } catch (error) {
      toast.error('Failed to send request');
    }
  };

  const filteredCollaborators = collaborators.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.specialties?.some(s => s.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div data-testid="collaborators-page" className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <Button data-testid="back-button" variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </div>

        <div>
          <h1 className="text-4xl font-bold gradient-text mb-4">Potential Collaborators</h1>
          <div className="relative">
            <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
            <Input
              data-testid="search-collaborators"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name or specialty..."
              className="pl-10 glass"
            />
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">Loading collaborators...</div>
        ) : filteredCollaborators.length === 0 ? (
          <Card className="glass">
            <CardContent className="py-12 text-center">
              <p className="text-gray-600">No collaborators found</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCollaborators.map((collab) => (
              <Card key={collab.id} data-testid={`collaborator-${collab.id}`} className="glass card-hover">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-pink-500 rounded-full flex items-center justify-center text-white">
                      <User className="w-6 h-6" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{collab.name}</CardTitle>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {collab.specialties && Array.isArray(collab.specialties) && collab.specialties.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-gray-700 mb-1">Specialties</p>
                      <div className="flex flex-wrap gap-1">
                        {collab.specialties.map((s, i) => (
                          <span key={i} className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {collab.research_interests && Array.isArray(collab.research_interests) && collab.research_interests.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-gray-700 mb-1">Research Interests</p>
                      <div className="flex flex-wrap gap-1">
                        {collab.research_interests.map((i, idx) => (
                          <span key={idx} className="text-xs px-2 py-1 bg-pink-100 text-pink-700 rounded">
                            {i}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  <Button
                    data-testid={`connect-${collab.id}`}
                    className="w-full bg-gradient-to-r from-purple-500 to-pink-600"
                    onClick={() => sendConnectionRequest(collab.id)}
                  >
                    <MessageCircle className="w-4 h-4 mr-2" />
                    Connect
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Collaborators;
