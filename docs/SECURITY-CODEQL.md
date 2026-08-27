# CodeQL SAST

## Scope

SideBySide Next uses GitHub CodeQL as an additional static application security testing (SAST) gate for:

- Python backend
- JavaScript/TypeScript web application
- Kotlin/Java Android application

CodeQL complements existing dependency, secret, type, lint, integration and supply-chain checks. It does not replace them.

## Reuse-before-build

Evaluated options:

- GitHub CodeQL / GitHub Code Scanning
- standalone SAST platforms
- custom scanner implementation

Decision: use GitHub CodeQL.

Reason:

- native GitHub Security integration;
- supports all required repository languages;
- no additional service, credentials or data export;
- results are available as security findings.

No custom scanner logic is maintained.

## Analysis configuration

Query suite:

- `security-queries` baseline

The initial gate intentionally uses the precise security query set. Additional query suites require a separate false-positive review.

Build modes:

| Language | Mode |
| --- | --- |
| Python | none |
| JavaScript/TypeScript | none |
| Kotlin/Java | manual Gradle compilation |

Android analysis uses the repository Gradle wrapper only:

```bash
./gradlew --dependency-verification strict :app:compileDebugKotlin
```

The existing Gradle Dependency Verification and wrapper integrity checks remain active.

## Findings handling

- Findings are reviewed based on severity and exploitability.
- Security findings are fixed or explicitly risk-accepted with justification.
- False positives require documented reasoning before dismissal.
- Broad ignore rules are not used to make CI green.

## Limitations

CodeQL is a static analysis tool. It does not replace runtime security testing, dependency auditing, privacy tests or tenant isolation tests.

Generated sources and build output are excluded where they do not represent application-owned security logic.
