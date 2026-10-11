import { useState } from 'react';
import { getApiBaseUrl } from './config';

const views = {
  Documents: 'Coming later: upload documents and manage your local document library (TASK-014 and later).',
  Chat: 'Coming later: ask questions and receive answers grounded in your documents. Questions and answers are not yet implemented.',
  Diagnostics: 'Coming later: inspect retrieval results and the evidence used for answers.',
};
type View = keyof typeof views;

export function App() {
  const [view, setView] = useState<View>('Documents');
  let configError: string | undefined;
  try {
    getApiBaseUrl();
  } catch (error) {
    configError = error instanceof Error ? error.message : 'Invalid API configuration.';
  }

  return (
    <div className="shell">
      <a className="skip-link" href="#content">Skip to content</a>
      <header>
        <h1>Local RAG</h1>
        <nav aria-label="Main navigation">
          {(Object.keys(views) as View[]).map((destination) => (
            <button key={destination} type="button" aria-current={view === destination ? 'page' : undefined}
              onClick={() => setView(destination)}>{destination}</button>
          ))}
        </nav>
      </header>
      <main id="content" tabIndex={-1}>
        {configError ? (
          <section role="alert">
            <h2>API configuration error</h2>
            <p>{configError}</p>
            <p>Update the frontend environment configuration and restart Vite.</p>
          </section>
        ) : (
          <section aria-labelledby="view-title">
            <h2 id="view-title">{view}</h2>
            <p>{views[view]}</p>
          </section>
        )}
      </main>
    </div>
  );
}
