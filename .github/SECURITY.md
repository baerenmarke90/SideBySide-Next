# Security Policy

## Reporting a vulnerability

Please do not report security vulnerabilities through public GitHub Issues.

Use GitHub's **Private Vulnerability Reporting** for this repository. This is the supported private reporting channel and keeps vulnerability details private while the report is triaged.

If GitHub does not show the **Report a vulnerability** action for this repository, Private Vulnerability Reporting is not currently available. In that case, do not publish sensitive details in a public issue or discussion. The repository maintainer must enable Private Vulnerability Reporting before a private report can be submitted through GitHub.

Do not include in public discussions:

- passwords, tokens, API keys or secrets
- private user data
- production data
- exploit details that would materially enable abuse

A useful private report should contain only the information needed to reproduce and assess the issue, for example the affected component, observed behavior, expected behavior, minimal reproduction steps and an impact assessment. Do not attach real user data or secrets when synthetic data is sufficient.

## Scope

Security reports may include issues affecting:

- authentication and authorization
- tenant isolation and privacy boundaries
- data exposure
- cryptographic handling
- dependency or supply-chain risks
- deployment and configuration security

The technical security model and application security invariants are documented separately in `docs/SECURITY.md`.

## Supported versions

The project does not currently publish production releases. Until the first stable release, security fixes are evaluated against the current `main` branch.

After releases are introduced, supported versions will be documented here.

## Response process

The maintainers will:

1. acknowledge receipt when possible;
2. validate and classify the reported issue;
3. investigate impact and affected components;
4. prepare a fix or mitigation where appropriate;
5. coordinate disclosure timing with the reporter when practical.

Reports are handled on a need-to-know basis. Security details should remain private until a fix or mitigation is available and coordinated disclosure has been agreed where practical.

## Coordinated disclosure

Please allow reasonable time for investigation and remediation before publicly disclosing a vulnerability.

The project aims to balance transparency with protecting users and deployments from active exploitation.
