import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { ArrowLeft, Send } from 'lucide-react';
import { toast } from 'sonner';

const Chat = ({ user }) => {
  const navigate = useNavigate();
  const { userId } = useParams();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMessages();
    const interval = setInterval(fetchMessages, 3000);
    return () => clearInterval(interval);
  }, [userId]);

  const fetchMessages = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/chat/messages/${userId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await res.json();
      setMessages(data);
    } catch (error) {
      // Silent error for polling
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    try {
      const token = localStorage.getItem('token');
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/chat/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ to_user: userId, message: newMessage }),
      });
      setNewMessage('');
      fetchMessages();
    } catch (error) {
      toast.error('Failed to send message');
    }
  };

  return (
    <div data-testid="chat-page" className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-8">
      <div className="max-w-4xl mx-auto">
        <Button data-testid="back-button" variant="ghost" onClick={() => navigate(-1)} className="mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>

        <Card className="glass shadow-2xl">
          <CardHeader>
            <CardTitle>Chat</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div data-testid="messages-container" className="h-96 overflow-y-auto space-y-3 p-4 bg-white/50 rounded-lg">
              {loading ? (
                <div className="text-center text-gray-500">Loading messages...</div>
              ) : messages.length === 0 ? (
                <div className="text-center text-gray-500">No messages yet. Start the conversation!</div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    data-testid={`message-${msg.id}`}
                    className={`flex ${msg.from_user === user.id ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs px-4 py-2 rounded-2xl ${
                        msg.from_user === user.id
                          ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                          : 'bg-white text-gray-800'
                      }`}
                    >
                      <p>{msg.message}</p>
                      <p className="text-xs opacity-70 mt-1">
                        {new Date(msg.created_at).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>

            <form onSubmit={sendMessage} className="flex gap-2">
              <Input
                data-testid="message-input"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type a message..."
                className="flex-1 glass"
              />
              <Button data-testid="send-message" type="submit" size="icon" className="bg-gradient-to-r from-blue-500 to-purple-600">
                <Send className="w-4 h-4" />
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Chat;
