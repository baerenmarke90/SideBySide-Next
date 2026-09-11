import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import type { PrivateAreaApi } from '../api/generated/apis/PrivateAreaApi';
import de from '../i18n/locales/de';
import { PrivateAreaProductPage } from './PrivateAreaProductPage';

function renderPrivateArea(path: string) {
  return renderToStaticMarkup(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/more/private/*"
          element={
            <PrivateAreaProductPage
              api={{} as PrivateAreaApi}
              accountId="account-a"
              spaceId="space-a"
            />
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe('PrivateAreaProductPage', () => {
  it('renders the private hub instead of redirecting to notes', () => {
    const html = renderPrivateArea('/more/private');

    expect(html).toContain('private-area-reference-overview');
    expect(html).toContain('private-area-privacy-banner');
    expect(html).toContain(de.privateArea.entry.privacy);
    expect(html).toContain('href="/more/private/notes"');
    expect(html).toContain('href="/more/private/gift-ideas"');
    expect(html).toContain('href="/more/private/collections"');
    expect(html).toContain(de.privateArea.notes.intro);
    expect(html).toContain(de.privateArea.gifts.intro);
    expect(html).toContain(de.privateArea.collections.intro);
    expect(html).not.toContain('class="private-area-nav"');
  });
});
