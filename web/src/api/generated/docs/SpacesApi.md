# SpacesApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getSpaceApiV1SpacesSpaceIdGet**](SpacesApi.md#getspaceapiv1spacesspaceidget) | **GET** /api/v1/spaces/{spaceId} | Get Space |
| [**getSpaceProfileApiV1SpacesSpaceIdProfileGet**](SpacesApi.md#getspaceprofileapiv1spacesspaceidprofileget) | **GET** /api/v1/spaces/{spaceId}/profile | Get Space Profile |
| [**updateSpaceProfileApiV1SpacesSpaceIdProfilePut**](SpacesApi.md#updatespaceprofileapiv1spacesspaceidprofileput) | **PUT** /api/v1/spaces/{spaceId}/profile | Update Space Profile |



## getSpaceApiV1SpacesSpaceIdGet

> SpaceView getSpaceApiV1SpacesSpaceIdGet(spaceId)

Get Space

### Example

```ts
import {
  Configuration,
  SpacesApi,
} from '';
import type { GetSpaceApiV1SpacesSpaceIdGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new SpacesApi();

  const body = {
    // string
    spaceId: spaceId_example,
  } satisfies GetSpaceApiV1SpacesSpaceIdGetRequest;

  try {
    const data = await api.getSpaceApiV1SpacesSpaceIdGet(body);
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

[**SpaceView**](SpaceView.md)

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


## getSpaceProfileApiV1SpacesSpaceIdProfileGet

> SpaceProfileView getSpaceProfileApiV1SpacesSpaceIdProfileGet(spaceId)

Get Space Profile

### Example

```ts
import {
  Configuration,
  SpacesApi,
} from '';
import type { GetSpaceProfileApiV1SpacesSpaceIdProfileGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new SpacesApi();

  const body = {
    // string
    spaceId: spaceId_example,
  } satisfies GetSpaceProfileApiV1SpacesSpaceIdProfileGetRequest;

  try {
    const data = await api.getSpaceProfileApiV1SpacesSpaceIdProfileGet(body);
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

[**SpaceProfileView**](SpaceProfileView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  * ETag - Die Version der Ressource. Gehoert unveraendert in das &#x60;If-Match&#x60; des naechsten Schreibzugriffs. <br>  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## updateSpaceProfileApiV1SpacesSpaceIdProfilePut

> SpaceProfileView updateSpaceProfileApiV1SpacesSpaceIdProfilePut(spaceId, ifMatch, spaceProfileUpdate)

Update Space Profile

Das Beziehungsprofil ersetzen.  Der Aufrufer legt mit &#x60;If-Match&#x60; die Version vor, die er gelesen hat. Hat der Partner inzwischen geschrieben, antwortet der Endpunkt mit 409 und aendert nichts - ein stilles Ueberschreiben gaebe es sonst genau dann, wenn beide gleichzeitig am selben Profil arbeiten.

### Example

```ts
import {
  Configuration,
  SpacesApi,
} from '';
import type { UpdateSpaceProfileApiV1SpacesSpaceIdProfilePutRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new SpacesApi();

  const body = {
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
    // SpaceProfileUpdate
    spaceProfileUpdate: ...,
  } satisfies UpdateSpaceProfileApiV1SpacesSpaceIdProfilePutRequest;

  try {
    const data = await api.updateSpaceProfileApiV1SpacesSpaceIdProfilePut(body);
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
| **ifMatch** | `string` | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben. | [Defaults to `undefined`] |
| **spaceProfileUpdate** | [SpaceProfileUpdate](SpaceProfileUpdate.md) |  | |

### Return type

[**SpaceProfileView**](SpaceProfileView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  * ETag - Die Version der Ressource. Gehoert unveraendert in das &#x60;If-Match&#x60; des naechsten Schreibzugriffs. <br>  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **409** | Die vorgelegte Version ist nicht mehr aktuell. Es wurde nichts geaendert; der aktuelle Stand ist neu zu laden. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

