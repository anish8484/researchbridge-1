import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ArrowLeft, Heart, FileText, Users, Star } from 'lucide-react';
import { toast } from 'sonner';

const Favorites = ({ user }) => {
  const navigate = useNavigate();
  const [favorites, setFavorites] = useState({ trials: [], publications: [], experts: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFavorites();
  }, []);

  const fetchFavorites = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/favorites`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await res.json();
      setFavorites(data);
    } catch (error) {
      toast.error('Failed to load favorites');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="favorites-page" className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <Button data-testid="back-button" variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </div>

        <div>
          <h1 className="text-4xl font-bold gradient-text mb-4">My Favorites</h1>
          <p className="text-gray-600">Items you've saved for quick access</p>
        </div>

        {loading ? (
          <div className="text-center py-12">Loading favorites...</div>
        ) : (
          <Tabs defaultValue="trials" className="space-y-6">
            <TabsList className="glass">
              <TabsTrigger value="trials" data-testid="trials-tab">
                <Heart className="w-4 h-4 mr-2" />
                Trials ({favorites.trials?.length || 0})
              </TabsTrigger>
              <TabsTrigger value="publications" data-testid="publications-tab">
                <FileText className="w-4 h-4 mr-2" />
                Publications ({favorites.publications?.length || 0})
              </TabsTrigger>
              <TabsTrigger value="experts" data-testid="experts-tab">
                <Users className="w-4 h-4 mr-2" />
                Experts ({favorites.experts?.length || 0})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="trials">
              {favorites.trials?.length === 0 ? (
                <Card className="glass">
                  <CardContent className="py-12 text-center">
                    <Star className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <p className="text-gray-600">No favorite trials yet</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-6">
                  {favorites.trials.map((trial) => (
                    <Card key={trial.id} data-testid={`fav-trial-${trial.id}`} className="glass card-hover">
                      <CardHeader>
                        <CardTitle className="text-xl">{trial.title}</CardTitle>
                        <CardDescription>
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm">
                            {trial.status}
                          </span>
                        </CardDescription>
                      </CardHeader>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="publications">
              {favorites.publications?.length === 0 ? (
                <Card className="glass">
                  <CardContent className="py-12 text-center">
                    <Star className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <p className="text-gray-600">No favorite publications yet</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-6">
                  {favorites.publications.map((pub) => (
                    <Card key={pub.id} data-testid={`fav-pub-${pub.id}`} className="glass card-hover">
                      <CardHeader>
                        <CardTitle className="text-xl">{pub.title}</CardTitle>
                        {pub.authors && (
                          <CardDescription>
                            {Array.isArray(pub.authors) ? pub.authors.slice(0, 3).join(', ') : pub.authors}
                          </CardDescription>
                        )}
                      </CardHeader>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="experts">
              {favorites.experts?.length === 0 ? (
                <Card className="glass">
                  <CardContent className="py-12 text-center">
                    <Star className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <p className="text-gray-600">No favorite experts yet</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {favorites.experts.map((expert) => (
                    <Card key={expert.id} data-testid={`fav-expert-${expert.id}`} className="glass card-hover">
                      <CardHeader>
                        <CardTitle className="text-lg">{expert.name}</CardTitle>
                        {expert.specialty && Array.isArray(expert.specialty) && (
                          <CardDescription>
                            <div className="flex flex-wrap gap-1 mt-2">
                              {expert.specialty.map((s, i) => (
                                <span key={i} className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                                  {s}
                                </span>
                              ))}
                            </div>
                          </CardDescription>
                        )}
                      </CardHeader>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  );
};

export default Favorites;
