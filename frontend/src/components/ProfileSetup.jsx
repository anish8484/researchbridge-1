import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { X } from 'lucide-react';
import { toast } from 'sonner';

const ProfileSetup = ({ user }) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  // Patient state
  const [rawInput, setRawInput] = useState('');
  const [location, setLocation] = useState('');

  // Researcher state
  const [specialties, setSpecialties] = useState([]);
  const [specialtyInput, setSpecialtyInput] = useState('');
  const [researchInterests, setResearchInterests] = useState([]);
  const [interestInput, setInterestInput] = useState('');
  const [orcid, setOrcid] = useState('');
  const [researchgate, setResearchgate] = useState('');
  const [availability, setAvailability] = useState(false);
  const [bio, setBio] = useState('');

  const addSpecialty = () => {
    if (specialtyInput.trim() && !specialties.includes(specialtyInput.trim())) {
      setSpecialties([...specialties, specialtyInput.trim()]);
      setSpecialtyInput('');
    }
  };

  const addInterest = () => {
    if (interestInput.trim() && !researchInterests.includes(interestInput.trim())) {
      setResearchInterests([...researchInterests, interestInput.trim()]);
      setInterestInput('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const endpoint = user.user_type === 'patient' ? '/api/patients/profile' : '/api/researchers/profile';
      const body = user.user_type === 'patient'
        ? { raw_input: rawInput, location }
        : { specialties, research_interests: researchInterests, orcid, researchgate, availability, bio };

      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error('Failed to create profile');

      toast.success('Profile created successfully!');
      navigate(user.user_type === 'patient' ? '/patient/dashboard' : '/researcher/dashboard');
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="profile-setup-page" className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-8">
      <div className="max-w-2xl mx-auto">
        <Card className="glass shadow-2xl">
          <CardHeader>
            <CardTitle className="text-3xl gradient-text">Set Up Your Profile</CardTitle>
            <CardDescription>
              {user.user_type === 'patient'
                ? 'Tell us about your condition to get personalized recommendations'
                : 'Share your expertise to connect with the right collaborators and patients'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {user.user_type === 'patient' ? (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="condition">What brings you here?</Label>
                    <Textarea
                      data-testid="condition-input"
                      id="condition"
                      value={rawInput}
                      onChange={(e) => setRawInput(e.target.value)}
                      placeholder="E.g., I have Brain Cancer and I'm looking for clinical trials..."
                      rows={4}
                      required
                    />
                    <p className="text-sm text-gray-500">Describe your condition in your own words</p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="location">Location (Optional)</Label>
                    <Input
                      data-testid="location-input"
                      id="location"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder="E.g., New York, USA"
                    />
                  </div>
                </>
              ) : (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="specialties">Specialties</Label>
                    <div className="flex gap-2">
                      <Input
                        data-testid="specialty-input"
                        id="specialties"
                        value={specialtyInput}
                        onChange={(e) => setSpecialtyInput(e.target.value)}
                        placeholder="E.g., Oncology"
                        onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSpecialty())}
                      />
                      <Button type="button" onClick={addSpecialty}>Add</Button>
                    </div>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {specialties.map((s) => (
                        <Badge key={s} variant="secondary" className="px-3 py-1">
                          {s}
                          <X
                            className="w-3 h-3 ml-2 cursor-pointer"
                            onClick={() => setSpecialties(specialties.filter((i) => i !== s))}
                          />
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="interests">Research Interests</Label>
                    <div className="flex gap-2">
                      <Input
                        data-testid="interest-input"
                        id="interests"
                        value={interestInput}
                        onChange={(e) => setInterestInput(e.target.value)}
                        placeholder="E.g., Immunotherapy"
                        onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addInterest())}
                      />
                      <Button type="button" onClick={addInterest}>Add</Button>
                    </div>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {researchInterests.map((i) => (
                        <Badge key={i} variant="secondary" className="px-3 py-1">
                          {i}
                          <X
                            className="w-3 h-3 ml-2 cursor-pointer"
                            onClick={() => setResearchInterests(researchInterests.filter((r) => r !== i))}
                          />
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="orcid">ORCID (Optional)</Label>
                    <Input
                      data-testid="orcid-input"
                      id="orcid"
                      value={orcid}
                      onChange={(e) => setOrcid(e.target.value)}
                      placeholder="0000-0000-0000-0000"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="researchgate">ResearchGate (Optional)</Label>
                    <Input
                      data-testid="researchgate-input"
                      id="researchgate"
                      value={researchgate}
                      onChange={(e) => setResearchgate(e.target.value)}
                      placeholder="Your ResearchGate profile URL"
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      data-testid="availability-checkbox"
                      type="checkbox"
                      id="availability"
                      checked={availability}
                      onChange={(e) => setAvailability(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <Label htmlFor="availability" className="cursor-pointer">Available for meetings</Label>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bio">Bio (Optional)</Label>
                    <Textarea
                      data-testid="bio-input"
                      id="bio"
                      value={bio}
                      onChange={(e) => setBio(e.target.value)}
                      placeholder="Tell us about your research background..."
                      rows={3}
                    />
                  </div>
                </>
              )}
              <Button
                data-testid="submit-profile"
                type="submit"
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                disabled={loading}
              >
                {loading ? 'Creating Profile...' : 'Continue'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ProfileSetup;
