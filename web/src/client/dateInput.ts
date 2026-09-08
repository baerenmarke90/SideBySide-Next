import type { MouseEvent } from 'react';

export function localDateInputValue(date: Date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function openNativeDatePicker(
  event: MouseEvent<HTMLInputElement>,
): void {
  const input = event.currentTarget;
  if (typeof input.showPicker !== 'function') return;
  try {
    input.showPicker();
  } catch {
    // Some browsers reject showPicker() outside a trusted user gesture or
    // for a disabled/readonly input; the native click behavior still works.
  }
}
