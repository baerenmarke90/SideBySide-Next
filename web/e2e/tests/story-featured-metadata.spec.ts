import { readFile } from 'node:fs/promises';
import { expect, type Page, test } from '@playwright/test';

const LONG_AUTHOR_NAME =
  'AlexandraMargaretheVonWinterbergMitAussergewoehnlichLangemProfilnamen';

async function renderMetadataFixture(
  page: Page,
  width: number,
  colorScheme: 'light' | 'dark',
): Promise<void> {
  const baseCss = await readFile(
    new URL('../../src/components/StoryProductPages.css', import.meta.url),
    'utf8',
  );
  const metadataCss = await readFile(
    new URL('../../src/components/StoryMomentMetadata.css', import.meta.url),
    'utf8',
  );

  await page.emulateMedia({ colorScheme });
  await page.setViewportSize({ width, height: 900 });
  await page.setContent(`
    <main>
      <article class="fixture-card">
        <div class="momente-hero-meta">
          <time datetime="2026-09-05">5. September 2026</time>
          <span class="momente-author-meta">
            <span class="person-identity" aria-hidden="true">
              <span class="person-identity-avatar-small">A</span>
            </span>
            <span>von ${LONG_AUTHOR_NAME}</span>
          </span>
        </div>
      </article>
      <article class="fixture-card">
        <div class="momente-tapestry-meta">
          <time datetime="2026-09-05">5. September 2026</time>
          <span class="momente-author-meta">
            <span class="person-identity" aria-hidden="true">
              <span class="person-identity-avatar-small">A</span>
            </span>
            <span>von ${LONG_AUTHOR_NAME}</span>
          </span>
        </div>
      </article>
    </main>
  `);
  await page.addStyleTag({ content: baseCss });
  await page.addStyleTag({ content: metadataCss });
  await page.addStyleTag({
    content: `
      :root {
        --space-2: 0.5rem;
        --space-3: 0.75rem;
        --color-text-secondary: #5e5466;
      }
      * { box-sizing: border-box; }
      html, body { margin: 0; }
      .fixture-card {
        width: calc(100vw - 40px);
        margin: 20px;
        padding: 20px;
      }
    `,
  });
}

async function expectMetadataContract(
  page: Page,
  selector: string,
): Promise<void> {
  const metadata = page.locator(selector);
  await expect(metadata).toBeVisible();

  const geometry = await metadata.evaluate((node) => {
    const row = node as HTMLElement;
    const date = row.querySelector(':scope > time') as HTMLElement | null;
    const author = row.querySelector(
      ':scope > .momente-author-meta',
    ) as HTMLElement | null;
    const authorLabel = author?.querySelector(
      'span:last-child',
    ) as HTMLElement | null;
    if (!date || !author || !authorLabel) {
      throw new Error('Expected date and author metadata');
    }

    const rowRect = row.getBoundingClientRect();
    const dateRect = date.getBoundingClientRect();
    const authorRect = author.getBoundingClientRect();
    return {
      justifyContent: getComputedStyle(row).justifyContent,
      rowLeft: rowRect.left,
      rowRight: rowRect.right,
      dateLeft: dateRect.left,
      dateRight: dateRect.right,
      authorLeft: authorRect.left,
      authorRight: authorRect.right,
      rowClientWidth: row.clientWidth,
      rowScrollWidth: row.scrollWidth,
      authorClientWidth: author.clientWidth,
      authorScrollWidth: author.scrollWidth,
      authorLabelClientWidth: authorLabel.clientWidth,
      authorLabelScrollWidth: authorLabel.scrollWidth,
    };
  });

  expect(geometry.justifyContent).toBe('space-between');
  expect(Math.abs(geometry.dateLeft - geometry.rowLeft)).toBeLessThanOrEqual(1);
  expect(Math.abs(geometry.rowRight - geometry.authorRight)).toBeLessThanOrEqual(
    1,
  );
  expect(geometry.authorLeft).toBeGreaterThanOrEqual(geometry.dateRight);
  expect(geometry.rowScrollWidth).toBeLessThanOrEqual(
    geometry.rowClientWidth + 1,
  );
  expect(geometry.authorScrollWidth).toBeLessThanOrEqual(
    geometry.authorClientWidth + 1,
  );
  expect(geometry.authorLabelScrollWidth).toBeLessThanOrEqual(
    geometry.authorLabelClientWidth + 1,
  );
}

test('Featured Moment metadata follows the shared date-left author-right contract', async ({
  page,
}) => {
  for (const colorScheme of ['light', 'dark'] as const) {
    for (const width of [390, 320]) {
      await renderMetadataFixture(page, width, colorScheme);

      const heroMetadata = page.locator('.momente-hero-meta');
      await expect(heroMetadata).toContainText(LONG_AUTHOR_NAME);
      expect(
        await heroMetadata.locator(':scope > *').evaluateAll((nodes) =>
          nodes.map((node) => node.tagName.toLowerCase()),
        ),
      ).toEqual(['time', 'span']);

      await expectMetadataContract(page, '.momente-hero-meta');
      await expectMetadataContract(page, '.momente-tapestry-meta');

      const viewport = await page.evaluate(() => ({
        clientWidth: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
      }));
      expect(viewport.scrollWidth).toBeLessThanOrEqual(viewport.clientWidth);
    }
  }
});
