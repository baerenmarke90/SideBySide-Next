# Security Policy

## Reporting a vulnerability

Please do not report security vulnerabilities through public GitHub Issues.

Use GitHub's **Private Vulnerability Reporting** for this repository when available. This keeps vulnerability details private while the issue is triaged.

If Private Vulnerability Reporting is not available for your account or the repository configuration, contact the maintainers through the private security contact configured for this project rather than publishing sensitive details.

Do not include:

- passwords, tokens, API keys or secrets
- private user data
- production data
- detailed exploit instructions in public discussions

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

## Coordinated disclosure

Please allow reasonable time for investigation and remediation before publicly disclosing a vulnerability.

The project aims to balance transparency with protecting users and deployments from active exploitation.
