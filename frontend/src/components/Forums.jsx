import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { ArrowLeft, MessageSquare, Plus } from 'lucide-react';
import { toast } from 'sonner';

const Forums = ({ user }) => {
  const navigate = useNavigate();
  const [forums, setForums] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [newForum, setNewForum] = useState({ category: '', title: '', description: '' });

  useEffect(() => {
    fetchForums();
  }, []);

  const fetchForums = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/forums`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await res.json();
      setForums(data);
    } catch (error) {
      toast.error('Failed to load forums');
    } finally {
      setLoading(false);
    }
  };

  const createForum = async () => {
    if (!newForum.category || !newForum.title) {
      toast.error('Please fill all required fields');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/forums`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(newForum),
      });
      toast.success('Forum created!');
      setOpenDialog(false);
      setNewForum({ category: '', title: '', description: '' });
      fetchForums();
    } catch (error) {
      toast.error('Failed to create forum');
    }
  };

  return (
    <div data-testid="forums-page" className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <Button data-testid="back-button" variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          {user.user_type === 'researcher' && (
            <Dialog open={openDialog} onOpenChange={setOpenDialog}>
              <DialogTrigger asChild>
                <Button data-testid="create-forum-btn" className="bg-gradient-to-r from-purple-500 to-pink-600">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Forum
                </Button>
              </DialogTrigger>
              <DialogContent className="glass">
                <DialogHeader>
                  <DialogTitle>Create New Forum</DialogTitle>
                  <DialogDescription>Start a new discussion topic</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="category">Category</Label>
                    <Input
                      data-testid="forum-category"
                      id="category"
                      value={newForum.category}
                      onChange={(e) => setNewForum({ ...newForum, category: e.target.value })}
                      placeholder="E.g., Cancer Research"
                    />
                  </div>
                  <div>
                    <Label htmlFor="title">Title</Label>
                    <Input
                      data-testid="forum-title"
                      id="title"
                      value={newForum.title}
                      onChange={(e) => setNewForum({ ...newForum, title: e.target.value })}
                      placeholder="Discussion title"
                    />
                  </div>
                  <div>
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      data-testid="forum-description"
                      id="description"
                      value={newForum.description}
                      onChange={(e) => setNewForum({ ...newForum, description: e.target.value })}
                      placeholder="What's this forum about?"
                      rows={3}
                    />
                  </div>
                  <Button data-testid="submit-forum" className="w-full" onClick={createForum}>
                    Create Forum
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </div>

        <div>
          <h1 className="text-4xl font-bold gradient-text mb-4">Community Forums</h1>
          <p className="text-gray-600">Connect, discuss, and share insights with the community</p>
        </div>

        {loading ? (
          <div className="text-center py-12">Loading forums...</div>
        ) : forums.length === 0 ? (
          <Card className="glass">
            <CardContent className="py-12 text-center">
              <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600">No forums yet. Be the first to create one!</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6">
            {forums.map((forum) => (
              <Card key={forum.id} data-testid={`forum-${forum.id}`} className="glass card-hover cursor-pointer">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
                          {forum.category}
                        </span>
                      </div>
                      <CardTitle className="text-xl">{forum.title}</CardTitle>
                      {forum.description && (
                        <CardDescription className="mt-2">{forum.description}</CardDescription>
                      )}
                    </div>
                    <MessageSquare className="w-6 h-6 text-purple-500" />
                  </div>
                </CardHeader>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Forums;
