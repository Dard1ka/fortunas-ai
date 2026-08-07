import { useEffect, useRef, useState } from 'react';

// Thin hook around the Web Speech API SpeechRecognition.
// Browser support: Chrome/Edge desktop+Android (full), Safari (partial), Firefox (none).

function getRecognitionCtor() {
  if (typeof window === 'undefined') return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

export function isSpeechRecognitionSupported() {
  return !!getRecognitionCtor();
}

export default function useSpeechRecognition({ lang = 'id-ID' } = {}) {
  const Ctor = getRecognitionCtor();
  const supported = !!Ctor;

  const recognitionRef = useRef(null);
  const finalRef = useRef('');
  const [isListening, setIsListening] = useState(false);
  const [final, setFinal] = useState('');
  const [interim, setInterim] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!supported) return undefined;
    const r = new Ctor();
    r.lang = lang;
    r.continuous = true;
    r.interimResults = true;

    r.onresult = (event) => {
      let interimChunk = '';
      let appended = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          appended += transcript;
        } else {
          interimChunk += transcript;
        }
      }
      if (appended) {
        finalRef.current = (finalRef.current + ' ' + appended).trim();
        setFinal(finalRef.current);
      }
      setInterim(interimChunk);
    };

    r.onerror = (event) => {
      setError(event.error || 'speech-error');
      setIsListening(false);
    };

    r.onend = () => {
      setIsListening(false);
      setInterim('');
    };

    recognitionRef.current = r;
    return () => {
      try { r.abort(); } catch { /* ignore */ }
      recognitionRef.current = null;
    };
  }, [Ctor, lang, supported]);

  const start = () => {
    if (!recognitionRef.current) return;
    setError(null);
    finalRef.current = '';
    setFinal('');
    setInterim('');
    try {
      recognitionRef.current.start();
      setIsListening(true);
    } catch (err) {
      setError(err?.message || 'start-failed');
      setIsListening(false);
    }
  };

  const stop = () => {
    if (!recognitionRef.current) return;
    try { recognitionRef.current.stop(); } catch { /* ignore */ }
    setIsListening(false);
  };

  const reset = () => {
    finalRef.current = '';
    setFinal('');
    setInterim('');
    setError(null);
  };

  return {
    isSupported: supported,
    isListening,
    final,
    interim,
    transcript: (final + (interim ? ' ' + interim : '')).trim(),
    error,
    start,
    stop,
    reset,
  };
}
