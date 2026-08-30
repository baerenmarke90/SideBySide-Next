import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { App } from './App';
import './i18n';
import { initializeTheme } from './theme';
import './styles.css';
import './story-media.css';
import './theme.css';
import './attachment-drafts.css';

initializeTheme();

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 15_000, retry: false } },
});

const root = document.getElementById('root');
if (!root) {
  throw new Error('Root element not found');
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
