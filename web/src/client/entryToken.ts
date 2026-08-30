export type SensitiveEntryToken =
  | { kind: 'recovery'; token: string }
  | { kind: 'invitation'; token: string };

export function readSensitiveEntryToken(search: string): SensitiveEntryToken | null {
  const params = new URLSearchParams(search);
  const recovery = params.get('recovery')?.trim();
  if (recovery) return { kind: 'recovery', token: recovery };

  const invitation = params.get('invite')?.trim();
  if (invitation) return { kind: 'invitation', token: invitation };

  return null;
}

export function stripSensitiveEntryTokens(
  pathname: string,
  search: string,
  hash: string,
): string {
  const params = new URLSearchParams(search);
  params.delete('recovery');
  params.delete('invite');
  const nextSearch = params.toString();
  return `${pathname}${nextSearch ? `?${nextSearch}` : ''}${hash}`;
}
