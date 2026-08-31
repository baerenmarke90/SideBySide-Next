import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { Brand, PRODUCT_NAME } from './Brand';

describe('Brand', () => {
  it('renders the canonical accessible product link with a decorative mark', () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <Brand to="/story" ariaLabel="Open SidebySide Story" />
      </MemoryRouter>,
    );

    expect(PRODUCT_NAME).toBe('SidebySide');
    expect(html).toContain('href="/story"');
    expect(html).toContain('aria-label="Open SidebySide Story"');
    expect(html).toContain('aria-hidden="true"');
    expect(html).toContain('<svg');
    expect(html).toContain('SidebySide');
    expect(html).not.toContain('SideBySide');
  });

  it('does not render the retired product suffix on entry surfaces', () => {
    const html = renderToStaticMarkup(<Brand suffix={<span>Next</span>} />);

    expect(html).not.toContain('<a');
    expect(html).toContain('SidebySide');
    expect(html).not.toContain('Next');
  });
});
