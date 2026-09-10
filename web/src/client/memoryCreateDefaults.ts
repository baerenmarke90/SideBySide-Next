export function localCalendarDate(now: Date = new Date()): string {
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function effectiveMemoryCreateDate(
  selectedDate: string,
  now: Date = new Date(),
): string {
  return selectedDate.trim() || localCalendarDate(now);
}

function parseDateOnly(dateOnly: string): [number, number, number] {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateOnly);
  if (!match) {
    throw new Error(`Invalid calendar date: ${dateOnly}`);
  }
  return [Number(match[1]), Number(match[2]), Number(match[3])];
}

export function dateOnlyToApiDate(dateOnly: string): Date {
  const [year, month, day] = parseDateOnly(dateOnly);
  return new Date(Date.UTC(year, month - 1, day));
}

export function formatDateOnly(dateOnly: string, locale: string): string {
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(dateOnlyToApiDate(dateOnly));
}

export function prepareMemoryCreateSubmission({
  title,
  selectedDate,
  locale,
  fallbackTitle,
  now = new Date(),
}: {
  title: string;
  selectedDate: string;
  locale: string;
  fallbackTitle: (formattedDate: string) => string;
  now?: Date;
}): { title: string; happenedOn: Date; effectiveDate: string } {
  const effectiveDate = effectiveMemoryCreateDate(selectedDate, now);
  const authoredTitle = title.trim();
  return {
    title:
      authoredTitle || fallbackTitle(formatDateOnly(effectiveDate, locale)),
    happenedOn: dateOnlyToApiDate(effectiveDate),
    effectiveDate,
  };
}
