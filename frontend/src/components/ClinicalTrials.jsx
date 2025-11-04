import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ArrowLeft, Search, Star } from 'lucide-react';
import { toast } from 'sonner';

const ClinicalTrials = ({ user }) => {
  const navigate = useNavigate();
  const [trials, setTrials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchTrials();
  }, []);

  const fetchTrials = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/patients/clinical-trials`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await res.json();
      setTrials(data);
    } catch (error) {
      toast.error('Failed to load trials');
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = async (trialId) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/favorites`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ item_type: 'trial', item_id: trialId }),
      });
      toast.success('Updated favorites');
    } catch (error) {
      toast.error('Failed to update favorites');
    }
  };

  const filteredTrials = trials.filter((t) =>
    t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div data-testid="clinical-trials-page" className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <Button data-testid="back-button" variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </div>

        <div>
          <h1 className="text-4xl font-bold gradient-text mb-4">Clinical Trials</h1>
          <div className="relative">
            <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
            <Input
              data-testid="search-trials"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search trials by keywords..."
              className="pl-10 glass"
            />
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">Loading trials...</div>
        ) : filteredTrials.length === 0 ? (
          <Card className="glass">
            <CardContent className="py-12 text-center">
              <p className="text-gray-600">No clinical trials found</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6">
            {filteredTrials.map((trial) => (
              <Card key={trial.id} data-testid={`trial-${trial.id}`} className="glass card-hover">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <CardTitle className="text-xl mb-2">{trial.title}</CardTitle>
                      <CardDescription className="space-y-2">
                        {trial.nct_id && <p className="font-mono text-sm">{trial.nct_id}</p>}
                        <div className="flex gap-2 flex-wrap">
                          {trial.status && (
                            <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                              {trial.status}
                            </span>
                          )}
                          {trial.phase && (
                            <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                              {trial.phase}
                            </span>
                          )}
                          {trial.location && (
                            <span className="px-3 py-1 bg-pink-100 text-pink-700 rounded-full text-sm">
                              {trial.location}
                            </span>
                          )}
                        </div>
                      </CardDescription>
                    </div>
                    <Button
                      data-testid={`favorite-${trial.id}`}
                      variant="ghost"
                      size="icon"
                      onClick={() => toggleFavorite(trial.id)}
                    >
                      <Star className="w-5 h-5" />
                    </Button>
                  </div>
                </CardHeader>
                {trial.description && (
                  <CardContent>
                    <p className="text-gray-700 line-clamp-3">{trial.description}</p>
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ClinicalTrials;
