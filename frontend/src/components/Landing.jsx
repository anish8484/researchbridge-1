import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Heart, Microscope, ArrowRight } from 'lucide-react';

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div data-testid="landing-page" className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <nav className="px-8 py-6 flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <Heart className="w-8 h-8 text-purple-600" />
          <span className="text-2xl font-bold gradient-text">CuraLink</span>
        </div>
        <Button
          data-testid="signin-button"
          onClick={() => navigate('/auth')}
          variant="outline"
          className="border-purple-300 hover:bg-purple-50"
        >
          Sign In
        </Button>
      </nav>

      <main className="container mx-auto px-8 py-20">
        <div className="text-center max-w-4xl mx-auto space-y-8 animate-fade-in">
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-tight">
            Connecting <span className="gradient-text">Patients</span> &{' '}
            <span className="gradient-text">Researchers</span>
          </h1>
          <p className="text-lg sm:text-xl text-gray-600 max-w-2xl mx-auto">
            Discover relevant clinical trials, connect with health experts, and access cutting-edge
            medical research—all in one place.
          </p>

          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center pt-8">
            <Button
              data-testid="patient-cta"
              onClick={() => navigate('/auth?type=patient')}
              size="lg"
              className="btn-primary bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-8 py-6 text-lg rounded-full shadow-xl"
            >
              <Heart className="w-5 h-5 mr-2" />
              I am a Patient
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Button
              data-testid="researcher-cta"
              onClick={() => navigate('/auth?type=researcher')}
              size="lg"
              className="btn-primary bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white px-8 py-6 text-lg rounded-full shadow-xl"
            >
              <Microscope className="w-5 h-5 mr-2" />
              I am a Researcher
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mt-32 max-w-6xl mx-auto">
          {[
            {
              icon: <Heart className="w-12 h-12 text-blue-500" />,
              title: 'For Patients',
              description: 'Find clinical trials, connect with experts, and access research tailored to your condition.',
            },
            {
              icon: <Microscope className="w-12 h-12 text-purple-500" />,
              title: 'For Researchers',
              description: 'Collaborate with peers, manage trials, and engage with patients seeking your expertise.',
            },
            {
              icon: <ArrowRight className="w-12 h-12 text-pink-500" />,
              title: 'Seamless Connection',
              description: 'AI-powered recommendations ensure you find exactly what matters most to you.',
            },
          ].map((feature, index) => (
            <div
              key={index}
              className="glass p-8 rounded-2xl shadow-lg card-hover"
            >
              <div className="mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default Landing;
