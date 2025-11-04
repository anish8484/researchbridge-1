import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ArrowLeft, Search, Star, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';

const Publications = ({ user }) => {
  const navigate = useNavigate();
  const [publications, setPublications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchPublications();
  }, []);

  const fetchPublications = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/patients/publications`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await res.json();
      setPublications(data);
    } catch (error) {
      toast.error('Failed to load publications');
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = async (pubId) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/favorites`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ item_type: 'publication', item_id: pubId }),
      });
      toast.success('Updated favorites');
    } catch (error) {
      toast.error('Failed to update favorites');
    }
  };

  const filteredPublications = publications.filter((p) =>
    p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.abstract?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div data-testid="publications-page" className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <Button data-testid="back-button" variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </div>

        <div>
          <h1 className="text-4xl font-bold gradient-text mb-4">Publications</h1>
          <div className="relative">
            <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
            <Input
              data-testid="search-publications"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search publications..."
              className="pl-10 glass"
            />
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">Loading publications...</div>
        ) : filteredPublications.length === 0 ? (
          <Card className="glass">
            <CardContent className="py-12 text-center">
              <p className="text-gray-600">No publications found</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6">
            {filteredPublications.map((pub) => (
              <Card key={pub.id} data-testid={`publication-${pub.id}`} className="glass card-hover">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <CardTitle className="text-xl mb-2">{pub.title}</CardTitle>
                      <CardDescription>
                        {pub.authors && Array.isArray(pub.authors) && (
                          <p className="text-sm text-gray-600 mb-2">{pub.authors.slice(0, 3).join(', ')}{pub.authors.length > 3 ? ' et al.' : ''}</p>
                        )}
                        {pub.published_date && (
                          <p className="text-sm text-gray-500">{pub.published_date}</p>
                        )}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        data-testid={`favorite-${pub.id}`}
                        variant="ghost"
                        size="icon"
                        onClick={() => toggleFavorite(pub.id)}
                      >
                        <Star className="w-5 h-5" />
                      </Button>
                      {pub.url && (
                        <Button
                          data-testid={`external-link-${pub.id}`}
                          variant="ghost"
                          size="icon"
                          onClick={() => window.open(pub.url, '_blank')}
                        >
                          <ExternalLink className="w-5 h-5" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>
                {pub.abstract && (
                  <CardContent>
                    <p className="text-gray-700 line-clamp-4">{pub.abstract}</p>
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

export default Publications;
