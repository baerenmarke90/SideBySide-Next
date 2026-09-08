import { expect, test } from '@playwright/test';

test('document reflows at 390px with 200 percent layout zoom', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');

  await page.locator('html').evaluate((element) => {
    element.style.zoom = '2';
  });

  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));

  expect(dimensions.clientWidth).toBe(390);
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
});
