import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { Brand } from './Brand';

describe('Brand', () => {
  it('renders an accessible product link with a decorative mark', () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <Brand to="/story" ariaLabel="Open SideBySide Story" />
      </MemoryRouter>,
    );

    expect(html).toContain('href="/story"');
    expect(html).toContain('aria-label="Open SideBySide Story"');
    expect(html).toContain('aria-hidden="true"');
    expect(html).toContain('<svg');
    expect(html).toContain('SideBySide');
  });

  it('renders a non-link wordmark for entry surfaces', () => {
    const html = renderToStaticMarkup(<Brand suffix={<span>Next</span>} />);

    expect(html).not.toContain('<a');
    expect(html).toContain('SideBySide');
    expect(html).toContain('Next');
  });
});
