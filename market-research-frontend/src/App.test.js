import { render, screen } from '@testing-library/react';
import App from './App';

test('renders main dashboard title', () => {
  render(<App />);
  const heading = screen.getByRole('heading', { name: /Market Research AI Agent/i });
  expect(heading).toBeInTheDocument();
});
