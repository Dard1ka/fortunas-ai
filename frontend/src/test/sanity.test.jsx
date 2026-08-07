import { render, screen } from '@testing-library/react';

test('harness renders', () => {
  render(<p>halo</p>);
  expect(screen.getByText('halo')).toBeInTheDocument();
});
