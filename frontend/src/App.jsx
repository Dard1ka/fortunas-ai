import { useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import HomeScreen from './screens/HomeScreen.jsx';
import BriefingScreen from './screens/BriefingScreen.jsx';
import ResultScreen from './screens/ResultScreen.jsx';
import HistoryScreen from './screens/HistoryScreen.jsx';
import ProfileScreen from './screens/ProfileScreen.jsx';
import LoginScreen from './screens/LoginScreen.jsx';
import BottomNav from './ui/BottomNav.jsx';
import VoiceFlow from './voice/VoiceFlow.jsx';
import { api, clearToken, getToken, setPrefix } from './api/client.js';

export default function App() {
  const [showVoice, setShowVoice] = useState(false);
  const [token, setTokenState] = useState(getToken());

  // Auto-logout saat backend balas 401 (token kedaluwarsa/invalid).
  useEffect(() => {
    const onLogout = () => setTokenState('');
    window.addEventListener('auth:logout', onLogout);
    return () => window.removeEventListener('auth:logout', onLogout);
  }, []);

  // Pastikan prefix tenant tersimpan (untuk namespace riwayat) walau token lama.
  useEffect(() => {
    if (!token) return undefined;
    const ctrl = new AbortController();
    api.me(ctrl.signal).then((r) => setPrefix(r.table_prefix)).catch(() => {});
    return () => ctrl.abort();
  }, [token]);

  const handleLogout = () => {
    clearToken();
    setTokenState('');
  };

  if (!token) {
    return <LoginScreen onAuthed={() => setTokenState(getToken())} />;
  }

  return (
    <div style={{ minHeight: '100dvh', position: 'relative' }}>
      <div style={{ paddingBottom: 120 }}>
        <Routes>
          <Route path="/"         element={<HomeScreen     onVoice={() => setShowVoice(true)} />} />
          <Route path="/briefing" element={<BriefingScreen onVoice={() => setShowVoice(true)} />} />
          <Route path="/result"   element={<ResultScreen   onVoice={() => setShowVoice(true)} />} />
          <Route path="/history"  element={<HistoryScreen  onVoice={() => setShowVoice(true)} />} />
          <Route path="/me"       element={<ProfileScreen  onVoice={() => setShowVoice(true)} onLogout={handleLogout} />} />
          <Route path="*"         element={<Navigate to="/" replace />} />
        </Routes>
      </div>

      <BottomNav onVoice={() => setShowVoice(true)} />

      {showVoice && <VoiceFlow onClose={() => setShowVoice(false)} />}
    </div>
  );
}
