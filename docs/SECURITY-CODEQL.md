# CodeQL SAST

## Scope

SideBySide Next uses GitHub CodeQL as an additional static application security testing (SAST) gate for:

- Python backend
- JavaScript/TypeScript web application
- Kotlin/Java Android application

CodeQL complements existing dependency, secret, type, lint, integration and supply-chain checks. It does not replace them.

The workflow runs on every pull request, on pushes to `main`, and weekly on Monday at 04:23 UTC.

## Reuse-before-build

Evaluated options:

- GitHub CodeQL / GitHub Code Scanning
- standalone SAST platforms such as Semgrep or Sonar-based services
- custom scanner implementation

Decision: use GitHub CodeQL.

Reason:

- native GitHub Security integration;
- supports all required repository languages;
- no additional SAST platform, credentials or operational service required;
- results are available as native code-scanning findings and pull-request checks;
- avoids maintaining custom scanner logic.

## Analysis configuration

CodeQL Action:

- `github/codeql-action` v4.37.8
- pinned to commit `db488ddef3bf6cb639b32c2e9a7c0a7ea8271d28`

Query suite:

- built-in CodeQL default query suite

The initial gate intentionally uses the high-precision default security baseline. `security-extended` is not enabled because it intentionally broadens coverage at the cost of additional lower-precision findings; enabling it requires a separate false-positive review.

Build modes:

| Language | Mode |
| --- | --- |
| Python | `none` |
| JavaScript/TypeScript | `none` |
| Kotlin/Java | `manual` Gradle compilation |

### Android build path

Android analysis mirrors the existing Android S8 toolchain:

- JDK 17 via pinned `actions/setup-java`
- pinned `gradle/actions/setup-gradle` v6.3.0
- Android platform 37.1 and build-tools 36.0.0
- repository Gradle Wrapper only
- pinned wrapper JAR SHA-256 verification
- strict Gradle Dependency Verification

CodeQL compiles the Android sources with:

```bash
./gradlew --no-daemon --stacktrace --dependency-verification strict :app:compileDebugKotlin
```

The existing Gradle Dependency Verification, wrapper integrity checks and Android S8 gates remain active.

## Permissions

Workflow default:

- `contents: read`

CodeQL analysis job:

- `contents: read`
- `security-events: write`

No repository secrets and no additional write permissions are required.

## Generated sources and build output

For Python and JavaScript/TypeScript no-build analysis, dependency and build-output directories are ignored. The generated web API client under `web/src/api/generated/**` is excluded because it is contract-generated rather than application-owned logic.

Android uses manual compiled analysis. CodeQL therefore analyzes the Kotlin/Java source that participates in `:app:compileDebugKotlin`; generated Kotlin contract models that participate in that compilation can be included. Findings in such generated Android sources must be corrected at the generator, contract or build-input level rather than hidden with a blanket suppression.

## Findings handling

- Critical/high findings block merge until fixed or individually dismissed with evidence as a false positive or accepted risk.
- Medium findings require explicit triage and a documented fix or risk decision; they must not remain unreviewed.
- Low/note findings are triaged and may be moved to backlog with rationale.
- False positives require documented reasoning before dismissal.
- Broad ignore or suppression rules are not used merely to make CI green.

Results are available in the pull-request checks and GitHub Security > Code scanning.

## Dry-run proof

Issue #184 was validated with a temporary, isolated JavaScript fixture that was not imported or bundled by the application. It passed URL-controlled data directly into `document.body.innerHTML`.

On dry-run commit `468964b7cc706e55f8ab49e326149927ab0b54af`, GitHub Advanced Security created a separate `CodeQL` check with conclusion `failure` and the summary:

> 1 new alert including 1 high severity security vulnerability

The fixture was removed in commit `3ac6ecc1f76063ca3aee9787e0a1cde1b8bcd6c9`. The clean follow-up CodeQL check reported no new alerts in code changed by the pull request.

## Reproduction

The Android extraction/build path can be reproduced from the repository root with:

```bash
cd android
./gradlew --no-daemon --stacktrace --dependency-verification strict :app:compileDebugKotlin
```

The complete SAST analysis is defined by `.github/workflows/codeql.yml` and `.github/codeql/codeql-config.yml` and is executed by GitHub CodeQL in CI.

## Merge protection

Code scanning must be configured as a repository merge-protection rule for `main` so CodeQL security results are enforced in addition to the existing required status checks. The existing ruleset must not be weakened when this rule is enabled.

## Limitations

CodeQL is static analysis. It does not replace runtime security testing, dependency auditing, secret scanning, privacy tests, authorization/tenant-isolation tests or integration testing.
