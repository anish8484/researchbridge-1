import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ArrowLeft, Search, Star, User } from 'lucide-react';
import { toast } from 'sonner';

const HealthExperts = ({ user }) => {
  const navigate = useNavigate();
  const [experts, setExperts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchExperts();
  }, []);

  const fetchExperts = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/patients/experts`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await res.json();
      setExperts(data);
    } catch (error) {
      toast.error('Failed to load experts');
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = async (expertId) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/favorites`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ item_type: 'expert', item_id: expertId }),
      });
      toast.success('Updated favorites');
    } catch (error) {
      toast.error('Failed to update favorites');
    }
  };

  const filteredExperts = experts.filter((e) =>
    e.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    e.specialty?.some(s => s.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div data-testid="health-experts-page" className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <Button data-testid="back-button" variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </div>

        <div>
          <h1 className="text-4xl font-bold gradient-text mb-4">Health Experts</h1>
          <div className="relative">
            <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
            <Input
              data-testid="search-experts"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search experts by name or specialty..."
              className="pl-10 glass"
            />
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">Loading experts...</div>
        ) : filteredExperts.length === 0 ? (
          <Card className="glass">
            <CardContent className="py-12 text-center">
              <p className="text-gray-600">No health experts found</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredExperts.map((expert) => (
              <Card key={expert.id} data-testid={`expert-${expert.id}`} className="glass card-hover">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-3 flex-1">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white">
                        <User className="w-6 h-6" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{expert.name}</CardTitle>
                        {expert.is_registered && (
                          <span className="text-xs text-green-600 font-semibold">Active on CuraLink</span>
                        )}
                      </div>
                    </div>
                    <Button
                      data-testid={`favorite-${expert.id}`}
                      variant="ghost"
                      size="icon"
                      onClick={() => toggleFavorite(expert.id)}
                    >
                      <Star className="w-5 h-5" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {expert.specialty && Array.isArray(expert.specialty) && expert.specialty.length > 0 && (
                    <div className="mb-3">
                      <p className="text-sm font-semibold text-gray-700 mb-1">Specialties</p>
                      <div className="flex flex-wrap gap-1">
                        {expert.specialty.map((s, i) => (
                          <span key={i} className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {expert.research_interests && Array.isArray(expert.research_interests) && expert.research_interests.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-gray-700 mb-1">Research Interests</p>
                      <div className="flex flex-wrap gap-1">
                        {expert.research_interests.map((i, idx) => (
                          <span key={idx} className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
                            {i}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default HealthExperts;
