import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { act } from 'react';
import AppShell from './AppShell.jsx';

function setWidth(w) {
  Object.defineProperty(window, 'innerWidth', { configurable: true, value: w });
  act(() => window.dispatchEvent(new Event('resize')));
}

const ui = (path = '/') =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <AppShell onVoice={() => {}}>
        <p>ISI</p>
      </AppShell>
    </MemoryRouter>,
  );

test('compact (390): bottom nav ada, rail tidak', () => {
  setWidth(390);
  ui();
  expect(screen.getByTestId('bottom-nav')).toBeInTheDocument();
  expect(screen.queryByTestId('nav-rail')).not.toBeInTheDocument();
});

test('medium (800): rail ikon (76px), bottom nav hilang, konten 720', () => {
  setWidth(800);
  ui();
  expect(screen.getByTestId('nav-rail')).toHaveStyle({ width: '76px' });
  expect(screen.queryByTestId('bottom-nav')).not.toBeInTheDocument();
  expect(screen.getByTestId('shell-content')).toHaveStyle({ maxWidth: '720px' });
});

test('expanded (1024, band yang dulu bermasalah): rail 200px + konten 840', () => {
  setWidth(1024);
  ui();
  expect(screen.getByTestId('nav-rail')).toHaveStyle({ width: '200px' });
  expect(screen.getByTestId('shell-content')).toHaveStyle({ maxWidth: '840px' });
});

test('phone-only route di viewport lebar: kolom 430px, tanpa rail/bottom-nav', () => {
  setWidth(1440);
  ui('/order');
  expect(screen.getByTestId('phone-frame')).toHaveStyle({ maxWidth: '430px' });
  expect(screen.queryByTestId('nav-rail')).not.toBeInTheDocument();
  expect(screen.queryByTestId('bottom-nav')).not.toBeInTheDocument();
});
