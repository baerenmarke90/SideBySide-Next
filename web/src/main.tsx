import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { App } from './App';
import { DemoEntry } from './components/DemoEntry';
import { ThemeControl } from './components/ThemeControl';
import { i18n } from './i18n';
import { initializeTheme } from './theme';
import './styles.css';
import './story-media.css';
import './theme.css';
import './shell.css';
import './layout.css';
import './attachment-drafts.css';
import './demo.css';
import './components/CommentsPanel.css';
import './components/MediaGallery.css';
import './components/MemoryProductPage.css';
import './components/ProfilePage.css';
import './components/RelatedPeoplePage.css';
import './components/StoryProductPages.css';

initializeTheme();

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 15_000, retry: false } },
});

const demoMode = import.meta.env.VITE_SBS_DEMO_MODE === 'true';
const demoUrl = String(import.meta.env.VITE_SBS_DEMO_URL || '')
  .trim()
  .replace(/\/+$/, '');
const demoAuthCallback =
  window.location.pathname.replace(/\/$/, '') === '/auth/magic-link';

function RootApp() {
  if (demoMode && !demoAuthCallback) {
    return (
      <>
        <ThemeControl />
        <DemoEntry />
      </>
    );
  }

  return (
    <>
      <App />
      {!demoMode && demoUrl ? (
        <a className="demo-launch" href={demoUrl}>
          {i18n.t('demo.launch')}
        </a>
      ) : null}
    </>
  );
}

const root = document.getElementById('root');
if (!root) {
  throw new Error('Root element not found');
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <RootApp />
      </QueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
