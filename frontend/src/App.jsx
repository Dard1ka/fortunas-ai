import { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import HomeScreen from './screens/HomeScreen.jsx';
import BriefingScreen from './screens/BriefingScreen.jsx';
import ResultScreen from './screens/ResultScreen.jsx';
import HistoryScreen from './screens/HistoryScreen.jsx';
import ProfileScreen from './screens/ProfileScreen.jsx';
import BottomNav from './ui/BottomNav.jsx';
import VoiceFlow from './voice/VoiceFlow.jsx';

export default function App() {
  const [showVoice, setShowVoice] = useState(false);

  return (
    <div style={{ minHeight: '100dvh', position: 'relative' }}>
      <div style={{ paddingBottom: 120 }}>
        <Routes>
          <Route path="/"         element={<HomeScreen     onVoice={() => setShowVoice(true)} />} />
          <Route path="/briefing" element={<BriefingScreen onVoice={() => setShowVoice(true)} />} />
          <Route path="/result"   element={<ResultScreen   onVoice={() => setShowVoice(true)} />} />
          <Route path="/history"  element={<HistoryScreen  onVoice={() => setShowVoice(true)} />} />
          <Route path="/me"       element={<ProfileScreen  onVoice={() => setShowVoice(true)} />} />
          <Route path="*"         element={<Navigate to="/" replace />} />
        </Routes>
      </div>

      <BottomNav onVoice={() => setShowVoice(true)} />

      {showVoice && <VoiceFlow onClose={() => setShowVoice(false)} />}
    </div>
  );
}
