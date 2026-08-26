# InvitationsApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**acceptInvitationApiV1InvitationsAcceptPost**](InvitationsApi.md#acceptinvitationapiv1invitationsacceptpost) | **POST** /api/v1/invitations/accept | Accept Invitation |
| [**createInvitationApiV1SpacesSpaceIdInvitationsPost**](InvitationsApi.md#createinvitationapiv1spacesspaceidinvitationspost) | **POST** /api/v1/spaces/{spaceId}/invitations | Create Invitation |
| [**listInvitationsApiV1SpacesSpaceIdInvitationsGet**](InvitationsApi.md#listinvitationsapiv1spacesspaceidinvitationsget) | **GET** /api/v1/spaces/{spaceId}/invitations | List Invitations |
| [**revokeInvitationApiV1SpacesSpaceIdInvitationsInvitationIdDelete**](InvitationsApi.md#revokeinvitationapiv1spacesspaceidinvitationsinvitationiddelete) | **DELETE** /api/v1/spaces/{spaceId}/invitations/{invitationId} | Revoke Invitation |



## acceptInvitationApiV1InvitationsAcceptPost

> MembershipView acceptInvitationApiV1InvitationsAcceptPost(acceptRequest)

Accept Invitation

Eine Einladung annehmen.  Ausserhalb von /spaces/..., weil der Aufrufer den Space noch nicht kennt - der Token bestimmt ihn.

### Example

```ts
import {
  Configuration,
  InvitationsApi,
} from '';
import type { AcceptInvitationApiV1InvitationsAcceptPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new InvitationsApi();

  const body = {
    // AcceptRequest
    acceptRequest: ...,
  } satisfies AcceptInvitationApiV1InvitationsAcceptPostRequest;

  try {
    const data = await api.acceptInvitationApiV1InvitationsAcceptPost(body);
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
| **acceptRequest** | [AcceptRequest](AcceptRequest.md) |  | |

### Return type

[**MembershipView**](MembershipView.md)

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


## createInvitationApiV1SpacesSpaceIdInvitationsPost

> IssuedInvitationView createInvitationApiV1SpacesSpaceIdInvitationsPost(spaceId)

Create Invitation

### Example

```ts
import {
  Configuration,
  InvitationsApi,
} from '';
import type { CreateInvitationApiV1SpacesSpaceIdInvitationsPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new InvitationsApi();

  const body = {
    // string
    spaceId: spaceId_example,
  } satisfies CreateInvitationApiV1SpacesSpaceIdInvitationsPostRequest;

  try {
    const data = await api.createInvitationApiV1SpacesSpaceIdInvitationsPost(body);
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
| **spaceId** | `string` |  | [Defaults to `undefined`] |

### Return type

[**IssuedInvitationView**](IssuedInvitationView.md)

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
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **409** | Die Anfrage kollidiert mit dem aktuellen Zustand der Ressource. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## listInvitationsApiV1SpacesSpaceIdInvitationsGet

> Array&lt;InvitationView&gt; listInvitationsApiV1SpacesSpaceIdInvitationsGet(spaceId)

List Invitations

Die offenen Einladungen. Ohne Token - der ist einmalig gewesen.

### Example

```ts
import {
  Configuration,
  InvitationsApi,
} from '';
import type { ListInvitationsApiV1SpacesSpaceIdInvitationsGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new InvitationsApi();

  const body = {
    // string
    spaceId: spaceId_example,
  } satisfies ListInvitationsApiV1SpacesSpaceIdInvitationsGetRequest;

  try {
    const data = await api.listInvitationsApiV1SpacesSpaceIdInvitationsGet(body);
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
| **spaceId** | `string` |  | [Defaults to `undefined`] |

### Return type

[**Array&lt;InvitationView&gt;**](InvitationView.md)

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
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## revokeInvitationApiV1SpacesSpaceIdInvitationsInvitationIdDelete

> revokeInvitationApiV1SpacesSpaceIdInvitationsInvitationIdDelete(invitationId, spaceId)

Revoke Invitation

### Example

```ts
import {
  Configuration,
  InvitationsApi,
} from '';
import type { RevokeInvitationApiV1SpacesSpaceIdInvitationsInvitationIdDeleteRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new InvitationsApi();

  const body = {
    // string
    invitationId: invitationId_example,
    // string
    spaceId: spaceId_example,
  } satisfies RevokeInvitationApiV1SpacesSpaceIdInvitationsInvitationIdDeleteRequest;

  try {
    const data = await api.revokeInvitationApiV1SpacesSpaceIdInvitationsInvitationIdDelete(body);
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
| **invitationId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |

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
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

