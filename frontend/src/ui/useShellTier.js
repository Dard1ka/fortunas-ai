import { useSyncExternalStore } from 'react';
import { tierForWidth } from './shell.js';

const subscribe = (onChange) => {
  window.addEventListener('resize', onChange);
  return () => window.removeEventListener('resize', onChange);
};

export default function useShellTier() {
  return useSyncExternalStore(
    subscribe,
    () => tierForWidth(window.innerWidth),
    () => 'compact',
  );
}
