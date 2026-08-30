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
| [**listAccountMembershipsApiV1AuthMembershipsGet**](AuthApi.md#listaccountmembershipsapiv1authmembershipsget) | **GET** /api/v1/auth/memberships | List Account Memberships |
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

Change the password and revoke every session.  This includes the current session. A password change often follows a suspected compromise, in which case no device should remain authenticated.

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
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **422** | Request parameters or domain inputs are invalid. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## completeOidcApiV1AuthOidcConnectionIdCallbackPost

> SessionView completeOidcApiV1AuthOidcConnectionIdCallbackPost(connectionId, oidcCallbackRequest)

Complete Oidc

Complete the callback from the external identity provider.

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
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **409** | The request conflicts with the current state of the resource. |  -  |
| **422** | Request parameters or domain inputs are invalid. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## confirmEmailApiV1AuthEmailVerificationConfirmPost

> confirmEmailApiV1AuthEmailVerificationConfirmPost(tokenOnlyRequest)

Confirm Email

Confirm the email address without requiring authentication.  Verification links are frequently opened in a different application from the one that holds the current session.

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
| **422** | Request parameters or domain inputs are invalid. |  -  |

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
| **422** | Request parameters or domain inputs are invalid. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## consumeRecoveryApiV1AuthRecoveryConsumePost

> SessionView consumeRecoveryApiV1AuthRecoveryConsumePost(recoveryConsumeRequest)

Consume Recovery

Set a new password and terminate all previous sessions.

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
| **422** | Request parameters or domain inputs are invalid. |  -  |

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
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **422** | Request parameters or domain inputs are invalid. |  -  |

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
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **422** | Request parameters or domain inputs are invalid. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## linkOidcApiV1AuthOidcConnectionIdLinkPost

> OidcStartView linkOidcApiV1AuthOidcConnectionIdLinkPost(connectionId)

Link Oidc

Link an external identity to the authenticated account.

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
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **422** | Request parameters or domain inputs are invalid. |  -  |
| **429** | Too many attempts occurred within the allowed time window. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## listAccountMembershipsApiV1AuthMembershipsGet

> Array&lt;AccountMembershipView&gt; listAccountMembershipsApiV1AuthMembershipsGet()

List Account Memberships

Return the caller\&#39;s active Space memberships.  Returning this small authorization projection lets official clients select an authorized Space without a build-time Space identifier or ID probing. It intentionally contains no partner or Space content; clients load the selected Space through the normal tenant-guarded endpoint afterward.

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { ListAccountMembershipsApiV1AuthMembershipsGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  try {
    const data = await api.listAccountMembershipsApiV1AuthMembershipsGet();
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

[**Array&lt;AccountMembershipView&gt;**](AccountMembershipView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |

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
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |

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
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **422** | Request parameters or domain inputs are invalid. |  -  |
| **429** | Too many attempts occurred within the allowed time window. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## registerApiV1AuthRegisterPost

> SessionView registerApiV1AuthRegisterPost(registerRequest)

Register

Create an account.  The first account requires the one-time bootstrap proof. Every later registration requires a valid invitation.

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
| **403** | The caller is authenticated but is not authorized for this operation. |  -  |
| **409** | The request conflicts with the current state of the resource. |  -  |
| **422** | Request parameters or domain inputs are invalid. |  -  |
| **429** | Too many attempts occurred within the allowed time window. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## requestEmailVerificationApiV1AuthEmailVerificationRequestPost

> requestEmailVerificationApiV1AuthEmailVerificationRequestPost()

Request Email Verification

Request verification of the authenticated account\&#39;s own email address.

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
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **429** | Too many attempts occurred within the allowed time window. |  -  |
| **503** | A capability required for this operation is not configured on this instance. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## requestMagicLinkApiV1AuthMagicLinkRequestPost

> requestMagicLinkApiV1AuthMagicLinkRequestPost(emailRequest)

Request Magic Link

Request a passwordless sign-in link.  The response is identical whether or not the address exists. Otherwise this endpoint would become an account directory.

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
| **422** | Request parameters or domain inputs are invalid. |  -  |
| **429** | Too many attempts occurred within the allowed time window. |  -  |
| **503** | A capability required for this operation is not configured on this instance. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## requestRecoveryApiV1AuthRecoveryRequestPost

> requestRecoveryApiV1AuthRecoveryRequestPost(emailRequest)

Request Recovery

Request a password reset while always returning the same response.

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
| **422** | Request parameters or domain inputs are invalid. |  -  |
| **429** | Too many attempts occurred within the allowed time window. |  -  |
| **503** | A capability required for this operation is not configured on this instance. |  -  |

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
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **422** | Request parameters or domain inputs are invalid. |  -  |
| **429** | Too many attempts occurred within the allowed time window. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## signOutApiV1AuthSignOutPost

> signOutApiV1AuthSignOutPost()

Sign Out

End this session while leaving other devices signed in.

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
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## startOidcApiV1AuthOidcConnectionIdStartPost

> OidcStartView startOidcApiV1AuthOidcConnectionIdStartPost(connectionId, oidcStartRequest)

Start Oidc

Begin authentication through an external identity provider.  State, nonce, and PKCE verifier are created server-side. The client receives only the authorization URL and state. Any invitation remains bound server-side and is never forwarded to the provider.

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
| **422** | Request parameters or domain inputs are invalid. |  -  |
| **429** | Too many attempts occurred within the allowed time window. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## startPasskeyAuthenticationApiV1AuthPasskeysAuthenticationStartPost

> { [key: string]: any | null; } startPasskeyAuthenticationApiV1AuthPasskeysAuthenticationStartPost()

Start Passkey Authentication

Begin passkey authentication without binding it to an account.  The authenticator selects which discoverable credential to offer. An endpoint that returned credentials for a given address would be an account directory.

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
| **422** | Request parameters or domain inputs are invalid. |  -  |
| **429** | Too many attempts occurred within the allowed time window. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## startPasskeyRegistrationApiV1AuthPasskeysRegistrationStartPost

> { [key: string]: any | null; } startPasskeyRegistrationApiV1AuthPasskeysRegistrationStartPost()

Start Passkey Registration

Begin passkey registration for an existing authenticated account.  A passkey is an additional access method for an account that already exists, so registration starts only from an authenticated session.

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
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

