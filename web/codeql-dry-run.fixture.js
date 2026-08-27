// TEMPORARY CodeQL dry-run fixture for Issue #184.
// This file is intentionally not imported or bundled and must be removed before merge.
const dryRunInput = new URLSearchParams(window.location.search).get("html");
document.body.innerHTML = dryRunInput;
