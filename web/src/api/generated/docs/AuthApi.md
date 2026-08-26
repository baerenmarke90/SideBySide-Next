# AuthApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**changePasswordApiV1AuthPasswordPost**](AuthApi.md#changepasswordapiv1authpasswordpost) | **POST** /api/v1/auth/password | Change Password |
| [**completeOidcApiV1AuthOidcConnectionIdCallbackPost**](AuthApi.md#completeoidcapiv1authoidcconnectionidcallbackpost) | **POST** /api/v1/auth/oidc/{connectionId}/callback | Complete Oidc |
| [**confirmEmailApiV1AuthEmailVerificationConfirmPost**](AuthApi.md#confirmemailapiv1authemailverificationconfirmpost) | **POST** /api/v1/auth/email/verification/confirm | Confirm Email |
| [**consumeMagicLinkApiV1AuthMagicLinkConsumePost**](AuthApi.md#consumemagiclinkapiv1authmagiclinkconsumepost) | **POST** /api/v1/auth/magic-link/consume | Consume Magic Link |
| [**consumeRecoveryApiV1AuthRecoveryConsumePost**](AuthApi.md#consumerecoveryapiv1authrecoveryconsumepost) | **POST** /api/v1/auth/recovery/consume | Consume Recovery |
| [**finishPasskeyAuthenticationApiV1AuthPasskeysAuthenticationFinishPost**](AuthApi.md#finishpasskeyauthenticationapiv1authpasskeysauthenticationfinishpost) | **POST** /api/v1/auth/passkeys/authentication/finish | Finish Passkey Authentication |
| [**finishPasskeyRegistrationApiV1AuthPasskeysRegistrationFinishPost**](AuthApi.md#finishpasskeyregistrationapiv1authpasskeysregistrationfinishpost) | **POST** /api/v1/auth/passkeys/registration/finish | Finish Passkey Registration |
| [**linkOidcApiV1AuthOidcConnectionIdLinkPost**](AuthApi.md#linkoidcapiv1authoidcconnectionidlinkpost) | **POST** /api/v1/auth/oidc/{connectionId}/link | Link Oidc |
| [**meApiV1AuthMeGet**](AuthApi.md#meapiv1authmeget) | **GET** /api/v1/auth/me | Me |
| [**refreshApiV1AuthRefreshPost**](AuthApi.md#refreshapiv1authrefreshpost) | **POST** /api/v1/auth/refresh | Refresh |
| [**registerApiV1AuthRegisterPost**](AuthApi.md#registerapiv1authregisterpost) | **POST** /api/v1/auth/register | Register |
| [**requestEmailVerificationApiV1AuthEmailVerificationRequestPost**](AuthApi.md#requestemailverificationapiv1authemailverificationrequestpost) | **POST** /api/v1/auth/email/verification/request | Request Email Verification |
| [**requestMagicLinkApiV1AuthMagicLinkRequestPost**](AuthApi.md#requestmagiclinkapiv1authmagiclinkrequestpost) | **POST** /api/v1/auth/magic-link/request | Request Magic Link |
| [**requestRecoveryApiV1AuthRecoveryRequestPost**](AuthApi.md#requestrecoveryapiv1authrecoveryrequestpost) | **POST** /api/v1/auth/recovery/request | Request Recovery |
| [**signInApiV1AuthSignInPost**](AuthApi.md#signinapiv1authsigninpost) | **POST** /api/v1/auth/sign-in | Sign In |
| [**signOutApiV1AuthSignOutPost**](AuthApi.md#signoutapiv1authsignoutpost) | **POST** /api/v1/auth/sign-out | Sign Out |
| [**startOidcApiV1AuthOidcConnectionIdStartPost**](AuthApi.md#startoidcapiv1authoidcconnectionidstartpost) | **POST** /api/v1/auth/oidc/{connectionId}/start | Start Oidc |
| [**startPasskeyAuthenticationApiV1AuthPasskeysAuthenticationStartPost**](AuthApi.md#startpasskeyauthenticationapiv1authpasskeysauthenticationstartpost) | **POST** /api/v1/auth/passkeys/authentication/start | Start Passkey Authentication |
| [**startPasskeyRegistrationApiV1AuthPasskeysRegistrationStartPost**](AuthApi.md#startpasskeyregistrationapiv1authpasskeysregistrationstartpost) | **POST** /api/v1/auth/passkeys/registration/start | Start Passkey Registration |



## changePasswordApiV1AuthPasswordPost

> changePasswordApiV1AuthPasswordPost(changePasswordRequest)

Change Password

Passwort aendern und alle Sitzungen beenden.  Auch die eigene: wer sein Passwort aendert, vermutet oft einen fremden Zugriff - dann darf kein Geraet angemeldet bleiben.

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { ChangePasswordApiV1AuthPasswordPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // ChangePasswordRequest
    changePasswordRequest: ...,
  } satisfies ChangePasswordApiV1AuthPasswordPostRequest;

  try {
    const data = await api.changePasswordApiV1AuthPasswordPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **changePasswordRequest** | [ChangePasswordRequest](ChangePasswordRequest.md) |  | |

### Return type

`void` (Empty response body)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **204** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## completeOidcApiV1AuthOidcConnectionIdCallbackPost

> SessionView completeOidcApiV1AuthOidcConnectionIdCallbackPost(connectionId, oidcCallbackRequest)

Complete Oidc

Den Rueckweg vom Anbieter abschliessen.

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { CompleteOidcApiV1AuthOidcConnectionIdCallbackPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // string
    connectionId: connectionId_example,
    // OidcCallbackRequest
    oidcCallbackRequest: ...,
  } satisfies CompleteOidcApiV1AuthOidcConnectionIdCallbackPostRequest;

  try {
    const data = await api.completeOidcApiV1AuthOidcConnectionIdCallbackPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **connectionId** | `string` |  | [Defaults to `undefined`] |
| **oidcCallbackRequest** | [OidcCallbackRequest](OidcCallbackRequest.md) |  | |

### Return type

[**SessionView**](SessionView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **409** | Die Anfrage kollidiert mit dem aktuellen Zustand der Ressource. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## confirmEmailApiV1AuthEmailVerificationConfirmPost

> confirmEmailApiV1AuthEmailVerificationConfirmPost(tokenOnlyRequest)

Confirm Email

Die Adresse bestaetigen.  Ohne Anmeldung: der Link wird oft in einem anderen Programm geoeffnet als dem, in dem die Sitzung liegt.

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { ConfirmEmailApiV1AuthEmailVerificationConfirmPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // TokenOnlyRequest
    tokenOnlyRequest: ...,
  } satisfies ConfirmEmailApiV1AuthEmailVerificationConfirmPostRequest;

  try {
    const data = await api.confirmEmailApiV1AuthEmailVerificationConfirmPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **tokenOnlyRequest** | [TokenOnlyRequest](TokenOnlyRequest.md) |  | |

### Return type

`void` (Empty response body)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **204** | Successful Response |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## consumeMagicLinkApiV1AuthMagicLinkConsumePost

> SessionView consumeMagicLinkApiV1AuthMagicLinkConsumePost(magicLinkConsumeRequest)

Consume Magic Link

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { ConsumeMagicLinkApiV1AuthMagicLinkConsumePostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // MagicLinkConsumeRequest
    magicLinkConsumeRequest: ...,
  } satisfies ConsumeMagicLinkApiV1AuthMagicLinkConsumePostRequest;

  try {
    const data = await api.consumeMagicLinkApiV1AuthMagicLinkConsumePost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **magicLinkConsumeRequest** | [MagicLinkConsumeRequest](MagicLinkConsumeRequest.md) |  | |

### Return type

[**SessionView**](SessionView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## consumeRecoveryApiV1AuthRecoveryConsumePost

> SessionView consumeRecoveryApiV1AuthRecoveryConsumePost(recoveryConsumeRequest)

Consume Recovery

Ein neues Passwort setzen; alle bisherigen Sitzungen enden.

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { ConsumeRecoveryApiV1AuthRecoveryConsumePostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // RecoveryConsumeRequest
    recoveryConsumeRequest: ...,
  } satisfies ConsumeRecoveryApiV1AuthRecoveryConsumePostRequest;

  try {
    const data = await api.consumeRecoveryApiV1AuthRecoveryConsumePost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **recoveryConsumeRequest** | [RecoveryConsumeRequest](RecoveryConsumeRequest.md) |  | |

### Return type

[**SessionView**](SessionView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## finishPasskeyAuthenticationApiV1AuthPasskeysAuthenticationFinishPost

> SessionView finishPasskeyAuthenticationApiV1AuthPasskeysAuthenticationFinishPost(passkeyAuthenticationRequest)

Finish Passkey Authentication

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { FinishPasskeyAuthenticationApiV1AuthPasskeysAuthenticationFinishPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // PasskeyAuthenticationRequest
    passkeyAuthenticationRequest: ...,
  } satisfies FinishPasskeyAuthenticationApiV1AuthPasskeysAuthenticationFinishPostRequest;

  try {
    const data = await api.finishPasskeyAuthenticationApiV1AuthPasskeysAuthenticationFinishPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **passkeyAuthenticationRequest** | [PasskeyAuthenticationRequest](PasskeyAuthenticationRequest.md) |  | |

### Return type

[**SessionView**](SessionView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## finishPasskeyRegistrationApiV1AuthPasskeysRegistrationFinishPost

> PasskeyView finishPasskeyRegistrationApiV1AuthPasskeysRegistrationFinishPost(passkeyRegistrationRequest)

Finish Passkey Registration

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { FinishPasskeyRegistrationApiV1AuthPasskeysRegistrationFinishPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // PasskeyRegistrationRequest
    passkeyRegistrationRequest: ...,
  } satisfies FinishPasskeyRegistrationApiV1AuthPasskeysRegistrationFinishPostRequest;

  try {
    const data = await api.finishPasskeyRegistrationApiV1AuthPasskeysRegistrationFinishPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **passkeyRegistrationRequest** | [PasskeyRegistrationRequest](PasskeyRegistrationRequest.md) |  | |

### Return type

[**PasskeyView**](PasskeyView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## linkOidcApiV1AuthOidcConnectionIdLinkPost

> OidcStartView linkOidcApiV1AuthOidcConnectionIdLinkPost(connectionId)

Link Oidc

Eine externe Identitaet mit dem angemeldeten Konto verknuepfen.

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { LinkOidcApiV1AuthOidcConnectionIdLinkPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // string
    connectionId: connectionId_example,
  } satisfies LinkOidcApiV1AuthOidcConnectionIdLinkPostRequest;

  try {
    const data = await api.linkOidcApiV1AuthOidcConnectionIdLinkPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **connectionId** | `string` |  | [Defaults to `undefined`] |

### Return type

[**OidcStartView**](OidcStartView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |
| **429** | Zu viele Versuche innerhalb des erlaubten Zeitfensters. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## meApiV1AuthMeGet

> AccountView meApiV1AuthMeGet()

Me

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { MeApiV1AuthMeGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  try {
    const data = await api.meApiV1AuthMeGet();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**AccountView**](AccountView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## refreshApiV1AuthRefreshPost

> TokenView refreshApiV1AuthRefreshPost(refreshRequest)

Refresh

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { RefreshApiV1AuthRefreshPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // RefreshRequest
    refreshRequest: ...,
  } satisfies RefreshApiV1AuthRefreshPostRequest;

  try {
    const data = await api.refreshApiV1AuthRefreshPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **refreshRequest** | [RefreshRequest](RefreshRequest.md) |  | |

### Return type

[**TokenView**](TokenView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |
| **429** | Zu viele Versuche innerhalb des erlaubten Zeitfensters. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## registerApiV1AuthRegisterPost

> SessionView registerApiV1AuthRegisterPost(registerRequest)

Register

Einen Account anlegen.  Der erste Account braucht den einmaligen Bootstrap-Nachweis. Danach braucht jede Registrierung eine gueltige Einladung.

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { RegisterApiV1AuthRegisterPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // RegisterRequest
    registerRequest: ...,
  } satisfies RegisterApiV1AuthRegisterPostRequest;

  try {
    const data = await api.registerApiV1AuthRegisterPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **registerRequest** | [RegisterRequest](RegisterRequest.md) |  | |

### Return type

[**SessionView**](SessionView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  -  |
| **403** | Der Aufrufer ist authentifiziert, aber fuer diesen Vorgang nicht berechtigt. |  -  |
| **409** | Die Anfrage kollidiert mit dem aktuellen Zustand der Ressource. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |
| **429** | Zu viele Versuche innerhalb des erlaubten Zeitfensters. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## requestEmailVerificationApiV1AuthEmailVerificationRequestPost

> requestEmailVerificationApiV1AuthEmailVerificationRequestPost()

Request Email Verification

Die Bestaetigung der eigenen Adresse anfordern.

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { RequestEmailVerificationApiV1AuthEmailVerificationRequestPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  try {
    const data = await api.requestEmailVerificationApiV1AuthEmailVerificationRequestPost();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

`void` (Empty response body)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **202** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **429** | Zu viele Versuche innerhalb des erlaubten Zeitfensters. |  -  |
| **503** | Eine fuer diesen Vorgang noetige Faehigkeit ist auf dieser Instanz nicht eingerichtet. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## requestMagicLinkApiV1AuthMagicLinkRequestPost

> requestMagicLinkApiV1AuthMagicLinkRequestPost(emailRequest)

Request Magic Link

Einen passwortlosen Anmeldelink anfordern.  Antwortet immer gleich - ob es die Adresse gibt, steht nicht in der Antwort. Sonst waere dieser Endpunkt ein Verzeichnis aller Konten.

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { RequestMagicLinkApiV1AuthMagicLinkRequestPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // EmailRequest
    emailRequest: ...,
  } satisfies RequestMagicLinkApiV1AuthMagicLinkRequestPostRequest;

  try {
    const data = await api.requestMagicLinkApiV1AuthMagicLinkRequestPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **emailRequest** | [EmailRequest](EmailRequest.md) |  | |

### Return type

`void` (Empty response body)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **202** | Successful Response |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |
| **429** | Zu viele Versuche innerhalb des erlaubten Zeitfensters. |  -  |
| **503** | Eine fuer diesen Vorgang noetige Faehigkeit ist auf dieser Instanz nicht eingerichtet. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## requestRecoveryApiV1AuthRecoveryRequestPost

> requestRecoveryApiV1AuthRecoveryRequestPost(emailRequest)

Request Recovery

Das Zuruecksetzen des Passworts anfordern. Antwortet immer gleich.

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { RequestRecoveryApiV1AuthRecoveryRequestPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // EmailRequest
    emailRequest: ...,
  } satisfies RequestRecoveryApiV1AuthRecoveryRequestPostRequest;

  try {
    const data = await api.requestRecoveryApiV1AuthRecoveryRequestPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **emailRequest** | [EmailRequest](EmailRequest.md) |  | |

### Return type

`void` (Empty response body)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **202** | Successful Response |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |
| **429** | Zu viele Versuche innerhalb des erlaubten Zeitfensters. |  -  |
| **503** | Eine fuer diesen Vorgang noetige Faehigkeit ist auf dieser Instanz nicht eingerichtet. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## signInApiV1AuthSignInPost

> SessionView signInApiV1AuthSignInPost(signInRequest)

Sign In

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { SignInApiV1AuthSignInPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // SignInRequest
    signInRequest: ...,
  } satisfies SignInApiV1AuthSignInPostRequest;

  try {
    const data = await api.signInApiV1AuthSignInPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **signInRequest** | [SignInRequest](SignInRequest.md) |  | |

### Return type

[**SessionView**](SessionView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |
| **429** | Zu viele Versuche innerhalb des erlaubten Zeitfensters. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## signOutApiV1AuthSignOutPost

> signOutApiV1AuthSignOutPost()

Sign Out

Diese Sitzung beenden. Andere Geraete bleiben angemeldet.

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { SignOutApiV1AuthSignOutPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  try {
    const data = await api.signOutApiV1AuthSignOutPost();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

`void` (Empty response body)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **204** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## startOidcApiV1AuthOidcConnectionIdStartPost

> OidcStartView startOidcApiV1AuthOidcConnectionIdStartPost(connectionId, oidcStartRequest)

Start Oidc

Eine Anmeldung ueber einen externen Anbieter beginnen.  State, Nonce und PKCE-Verifier entstehen serverseitig. Der Client bekommt nur die Adresse und den State. Eine Einladung bleibt dabei serverseitig gebunden und wird nie an den Anbieter weitergegeben.

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { StartOidcApiV1AuthOidcConnectionIdStartPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // string
    connectionId: connectionId_example,
    // OidcStartRequest (optional)
    oidcStartRequest: ...,
  } satisfies StartOidcApiV1AuthOidcConnectionIdStartPostRequest;

  try {
    const data = await api.startOidcApiV1AuthOidcConnectionIdStartPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **connectionId** | `string` |  | [Defaults to `undefined`] |
| **oidcStartRequest** | [OidcStartRequest](OidcStartRequest.md) |  | [Optional] |

### Return type

[**OidcStartView**](OidcStartView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |
| **429** | Zu viele Versuche innerhalb des erlaubten Zeitfensters. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## startPasskeyAuthenticationApiV1AuthPasskeysAuthenticationStartPost

> { [key: string]: any | null; } startPasskeyAuthenticationApiV1AuthPasskeysAuthenticationStartPost()

Start Passkey Authentication

Eine Anmeldung mit Passkey beginnen.  Ohne Kontobezug: der Authenticator waehlt selbst, welches auffindbare Credential er anbietet. Ein Endpunkt, der zu einer Adresse die passenden Credentials nennt, waere ein Verzeichnis der Konten.

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { StartPasskeyAuthenticationApiV1AuthPasskeysAuthenticationStartPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  try {
    const data = await api.startPasskeyAuthenticationApiV1AuthPasskeysAuthenticationStartPost();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

**{ [key: string]: any | null; }**

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## startPasskeyRegistrationApiV1AuthPasskeysRegistrationStartPost

> { [key: string]: any | null; } startPasskeyRegistrationApiV1AuthPasskeysRegistrationStartPost()

Start Passkey Registration

Die Registrierung eines Passkeys beginnen.  Nur aus einer bestehenden Anmeldung heraus: ein Passkey ist ein zusaetzlicher Zugang zu einem Konto, das es schon gibt.

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { StartPasskeyRegistrationApiV1AuthPasskeysRegistrationStartPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  try {
    const data = await api.startPasskeyRegistrationApiV1AuthPasskeysRegistrationStartPost();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

**{ [key: string]: any | null; }**

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

