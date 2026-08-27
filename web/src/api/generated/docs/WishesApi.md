# WishesApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createWish**](WishesApi.md#createwish) | **POST** /api/v1/spaces/{spaceId}/wishes | Create Wish |
| [**deleteWish**](WishesApi.md#deletewish) | **DELETE** /api/v1/spaces/{spaceId}/wishes/{wishId} | Delete Wish |
| [**getWish**](WishesApi.md#getwish) | **GET** /api/v1/spaces/{spaceId}/wishes/{wishId} | Get Wish |
| [**listWishes**](WishesApi.md#listwishes) | **GET** /api/v1/spaces/{spaceId}/wishes | List Wishes |
| [**updateWish**](WishesApi.md#updatewish) | **PATCH** /api/v1/spaces/{spaceId}/wishes/{wishId} | Update Wish |



## createWish

> WishDetail createWish(spaceId, wishCreate)

Create Wish

### Example

```ts
import {
  Configuration,
  WishesApi,
} from '';
import type { CreateWishRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new WishesApi();

  const body = {
    // string
    spaceId: spaceId_example,
    // WishCreate
    wishCreate: ...,
  } satisfies CreateWishRequest;

  try {
    const data = await api.createWish(body);
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
| **wishCreate** | [WishCreate](WishCreate.md) |  | |

### Return type

[**WishDetail**](WishDetail.md)

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


## deleteWish

> deleteWish(wishId, spaceId, ifMatch)

Delete Wish

### Example

```ts
import {
  Configuration,
  WishesApi,
} from '';
import type { DeleteWishRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new WishesApi();

  const body = {
    // string
    wishId: wishId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
  } satisfies DeleteWishRequest;

  try {
    const data = await api.deleteWish(body);
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
| **wishId** | `string` |  | [Defaults to `undefined`] |
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
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **409** | Die Anfrage kollidiert mit dem aktuellen Zustand der Ressource. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getWish

> WishDetail getWish(wishId, spaceId)

Get Wish

### Example

```ts
import {
  Configuration,
  WishesApi,
} from '';
import type { GetWishRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new WishesApi();

  const body = {
    // string
    wishId: wishId_example,
    // string
    spaceId: spaceId_example,
  } satisfies GetWishRequest;

  try {
    const data = await api.getWish(body);
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
| **wishId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |

### Return type

[**WishDetail**](WishDetail.md)

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


## listWishes

> WishPage listWishes(spaceId, cursor, limit, status)

List Wishes

### Example

```ts
import {
  Configuration,
  WishesApi,
} from '';
import type { ListWishesRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new WishesApi();

  const body = {
    // string
    spaceId: spaceId_example,
    // string (optional)
    cursor: cursor_example,
    // number (optional)
    limit: 56,
    // WishStatus (optional)
    status: ...,
  } satisfies ListWishesRequest;

  try {
    const data = await api.listWishes(body);
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
| **status** | `WishStatus` |  | [Optional] [Defaults to `undefined`] [Enum: OPEN, PLANNED, COMPLETED] |

### Return type

[**WishPage**](WishPage.md)

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


## updateWish

> WishDetail updateWish(wishId, spaceId, ifMatch, wishUpdate)

Update Wish

### Example

```ts
import {
  Configuration,
  WishesApi,
} from '';
import type { UpdateWishRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new WishesApi();

  const body = {
    // string
    wishId: wishId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
    // WishUpdate
    wishUpdate: ...,
  } satisfies UpdateWishRequest;

  try {
    const data = await api.updateWish(body);
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
| **wishId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |
| **ifMatch** | `string` | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben. | [Defaults to `undefined`] |
| **wishUpdate** | [WishUpdate](WishUpdate.md) |  | |

### Return type

[**WishDetail**](WishDetail.md)

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
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **409** | Die Anfrage kollidiert mit dem aktuellen Zustand der Ressource. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

