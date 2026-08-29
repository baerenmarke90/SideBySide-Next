# OpenAPI Client Generation

Web and Android use the same versioned contract. This layer generates the
mechanical parts—DTOs and Web endpoint calls—from `backend/openapi.json`
instead of maintaining them manually in two places.

It explicitly generates **no** domain, UI, or state logic.

```text
FastAPI  ->  backend/openapi.json  ->  openapi-generator
                                        |-- web/src/api/generated      (TypeScript)
                                        '-- android/api/generated      (Kotlin models)
```

## Usage

```bash
tools/openapi/generate.sh           # regenerate
tools/openapi/generate.sh --check   # check for drift only (CI)
```

Docker is the only prerequisite, and the Self-Hosted stack already requires
it. No local JDK or Node installation is needed.

## Why this generator

`openapi-generator` serves TypeScript and Kotlin from one configuration.
Alternatives considered and why they do not fit here:

- **openapi-typescript + openapi-fetch** generates lean TypeScript code but does
  not cover Kotlin. Two tools would require two pins, two configuration styles,
  two license reviews, and two CI paths.
- **Kiota** (Microsoft) supports TypeScript but not Kotlin.
- **orval**, **hey-api**, and **oazapfts** are TypeScript-only.
- **swagger-codegen** is the predecessor of openapi-generator; active
  development continues in the latter.

## Story union on Kotlin

The previous generator version produced `StoryItem` as an unusable
`sealed class`: the variants did not inherit from it, and the base type required
the fields of all three variants simultaneously. Issue #119 fixed this.

OpenAPI Generator v7.24.0 now uses `generateOneOfAnyOfWrappers` and
`kotlinx.serialization` to produce a discriminator-based `sealed interface`.
The generated serializer evaluates `kind` and deserializes `MEMORY`,
`HEART_MOMENT`, and `MILESTONE` into their corresponding wrappers. This keeps
`StoryPage.items` as a `List<StoryItem>` without requiring any variant to carry
the fields of the others.

The OpenAPI contract was not the cause. The contract with
`discriminator.propertyName = kind` remains the unchanged source of truth.

## Why generated code is committed

The `backend/openapi.json` contract is already committed and checked against the
real ASGI application. Client code follows the same approach:

- A contract break is **readable** as a pull-request diff instead of appearing
  only as a failed CI step.
- Web and Android builds need neither Docker nor network access to start.
- The drift check is a comparison, not a second generation path that could
  itself diverge.

The tradeoff is a larger diff for contract changes. This is intentional: a
change to the client interface *should* be visible during review.

## Runtime dependencies

**TypeScript:** none. The `typescript-fetch` generator targets the browser Fetch
API. It creates no `package.json`, and generated files import nothing outside
their own directory—verified rather than assumed.

**Kotlin:** `kotlinx.serialization`. The models use `@Serializable` and
`@SerialName`, which require a JSON library. Of the available options,
`kotlinx.serialization` is the only one that does **not** also select an HTTP
stack for the Android client; it works with both Retrofit and Ktor. Moshi, Gson,
and Jackson would make stronger architectural choices here.

There is no Kotlin service layer. Selecting Retrofit or Ktor is an Android
client decision and can be added independently when needed.

## Licenses

`openapi-generator` is licensed under **Apache-2.0**. The tool runs only at
build time and is not distributed; Apache-2.0 imposes no conditions on the
generated output. Generated code is therefore project code under the project
license.

The container is pinned by both version **and** digest
(`tools/openapi/generator.env`). A reassigned tag therefore cannot silently
produce different client code.

## Updating

1. Enter the new tag in `generator.env`.
2. Run `docker pull openapitools/openapi-generator-cli:<tag>` and record the
   reported digest.
3. Run `tools/openapi/generate.sh`.
4. Explain the resulting diff in the pull request—a generator change modifies
   client code and is a review concern, not a formality.
