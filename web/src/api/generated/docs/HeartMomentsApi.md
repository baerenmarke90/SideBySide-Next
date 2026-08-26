# HeartMomentsApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**changeHeartMomentVisibility**](HeartMomentsApi.md#changeheartmomentvisibility) | **PATCH** /api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}/visibility | Change Heart Moment Visibility |
| [**createHeartMoment**](HeartMomentsApi.md#createheartmoment) | **POST** /api/v1/spaces/{spaceId}/heart-moments | Create Heart Moment |
| [**deleteHeartMoment**](HeartMomentsApi.md#deleteheartmoment) | **DELETE** /api/v1/spaces/{spaceId}/heart-moments/{heartMomentId} | Delete Heart Moment |
| [**getHeartMoment**](HeartMomentsApi.md#getheartmoment) | **GET** /api/v1/spaces/{spaceId}/heart-moments/{heartMomentId} | Get Heart Moment |
| [**listHeartMoments**](HeartMomentsApi.md#listheartmoments) | **GET** /api/v1/spaces/{spaceId}/heart-moments | List Heart Moments |
| [**updateHeartMoment**](HeartMomentsApi.md#updateheartmoment) | **PATCH** /api/v1/spaces/{spaceId}/heart-moments/{heartMomentId} | Update Heart Moment |



## changeHeartMomentVisibility

> HeartMomentDetail changeHeartMomentVisibility(heartMomentId, spaceId, ifMatch, heartMomentVisibilityChange)

Change Heart Moment Visibility

### Example

```ts
import {
  Configuration,
  HeartMomentsApi,
} from '';
import type { ChangeHeartMomentVisibilityRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new HeartMomentsApi();

  const body = {
    // string
    heartMomentId: heartMomentId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
    // HeartMomentVisibilityChange
    heartMomentVisibilityChange: ...,
  } satisfies ChangeHeartMomentVisibilityRequest;

  try {
    const data = await api.changeHeartMomentVisibility(body);
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
| **heartMomentId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |
| **ifMatch** | `string` | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben. | [Defaults to `undefined`] |
| **heartMomentVisibilityChange** | [HeartMomentVisibilityChange](HeartMomentVisibilityChange.md) |  | |

### Return type

[**HeartMomentDetail**](HeartMomentDetail.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  * ETag - Version der Ressource fuer den naechsten If-Match-Schreibzugriff. <br>  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **403** | Der Aufrufer ist authentifiziert, aber fuer diesen Vorgang nicht berechtigt. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **409** | Die Anfrage kollidiert mit dem aktuellen Zustand der Ressource. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## createHeartMoment

> HeartMomentDetail createHeartMoment(spaceId, heartMomentCreate)

Create Heart Moment

### Example

```ts
import {
  Configuration,
  HeartMomentsApi,
} from '';
import type { CreateHeartMomentRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new HeartMomentsApi();

  const body = {
    // string
    spaceId: spaceId_example,
    // HeartMomentCreate
    heartMomentCreate: ...,
  } satisfies CreateHeartMomentRequest;

  try {
    const data = await api.createHeartMoment(body);
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
| **heartMomentCreate** | [HeartMomentCreate](HeartMomentCreate.md) |  | |

### Return type

[**HeartMomentDetail**](HeartMomentDetail.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  * ETag - Version der Ressource fuer den naechsten If-Match-Schreibzugriff. <br>  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## deleteHeartMoment

> deleteHeartMoment(heartMomentId, spaceId, ifMatch)

Delete Heart Moment

### Example

```ts
import {
  Configuration,
  HeartMomentsApi,
} from '';
import type { DeleteHeartMomentRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new HeartMomentsApi();

  const body = {
    // string
    heartMomentId: heartMomentId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
  } satisfies DeleteHeartMomentRequest;

  try {
    const data = await api.deleteHeartMoment(body);
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
| **heartMomentId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |
| **ifMatch** | `string` | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben. | [Defaults to `undefined`] |

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
| **403** | Der Aufrufer ist authentifiziert, aber fuer diesen Vorgang nicht berechtigt. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **409** | Die Anfrage kollidiert mit dem aktuellen Zustand der Ressource. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getHeartMoment

> HeartMomentDetail getHeartMoment(heartMomentId, spaceId)

Get Heart Moment

### Example

```ts
import {
  Configuration,
  HeartMomentsApi,
} from '';
import type { GetHeartMomentRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new HeartMomentsApi();

  const body = {
    // string
    heartMomentId: heartMomentId_example,
    // string
    spaceId: spaceId_example,
  } satisfies GetHeartMomentRequest;

  try {
    const data = await api.getHeartMoment(body);
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
| **heartMomentId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |

### Return type

[**HeartMomentDetail**](HeartMomentDetail.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  * ETag - Version der Ressource fuer den naechsten If-Match-Schreibzugriff. <br>  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## listHeartMoments

> HeartMomentPage listHeartMoments(spaceId, cursor, limit, visibility)

List Heart Moments

### Example

```ts
import {
  Configuration,
  HeartMomentsApi,
} from '';
import type { ListHeartMomentsRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new HeartMomentsApi();

  const body = {
    // string
    spaceId: spaceId_example,
    // string (optional)
    cursor: cursor_example,
    // number (optional)
    limit: 56,
    // ContentVisibility (optional)
    visibility: ...,
  } satisfies ListHeartMomentsRequest;

  try {
    const data = await api.listHeartMoments(body);
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
| **cursor** | `string` |  | [Optional] [Defaults to `undefined`] |
| **limit** | `number` |  | [Optional] [Defaults to `50`] |
| **visibility** | `ContentVisibility` |  | [Optional] [Defaults to `undefined`] [Enum: SHARED, PRIVATE] |

### Return type

[**HeartMomentPage**](HeartMomentPage.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **400** | Die Anfrage ist syntaktisch gueltig, kann aber so nicht verarbeitet werden. |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## updateHeartMoment

> HeartMomentDetail updateHeartMoment(heartMomentId, spaceId, ifMatch, heartMomentUpdate)

Update Heart Moment

### Example

```ts
import {
  Configuration,
  HeartMomentsApi,
} from '';
import type { UpdateHeartMomentRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new HeartMomentsApi();

  const body = {
    // string
    heartMomentId: heartMomentId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
    // HeartMomentUpdate
    heartMomentUpdate: ...,
  } satisfies UpdateHeartMomentRequest;

  try {
    const data = await api.updateHeartMoment(body);
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
| **heartMomentId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |
| **ifMatch** | `string` | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben. | [Defaults to `undefined`] |
| **heartMomentUpdate** | [HeartMomentUpdate](HeartMomentUpdate.md) |  | |

### Return type

[**HeartMomentDetail**](HeartMomentDetail.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  * ETag - Version der Ressource fuer den naechsten If-Match-Schreibzugriff. <br>  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **403** | Der Aufrufer ist authentifiziert, aber fuer diesen Vorgang nicht berechtigt. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **409** | Die Anfrage kollidiert mit dem aktuellen Zustand der Ressource. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

