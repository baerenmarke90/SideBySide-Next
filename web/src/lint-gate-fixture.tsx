import { useState } from 'react';

export function LintGateFixture({ enabled }: { enabled: boolean }) {
  if (enabled) {
    useState(0);
  }
  return null;
}
