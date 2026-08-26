# MemoriesApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createMemory**](MemoriesApi.md#creatememory) | **POST** /api/v1/spaces/{spaceId}/memories | Create Memory |
| [**deleteMemory**](MemoriesApi.md#deletememory) | **DELETE** /api/v1/spaces/{spaceId}/memories/{memoryId} | Delete Memory |
| [**getMemory**](MemoriesApi.md#getmemory) | **GET** /api/v1/spaces/{spaceId}/memories/{memoryId} | Get Memory |
| [**listMemories**](MemoriesApi.md#listmemories) | **GET** /api/v1/spaces/{spaceId}/memories | List Memories |
| [**replaceMemoryAttachments**](MemoriesApi.md#replacememoryattachments) | **PUT** /api/v1/spaces/{spaceId}/memories/{memoryId}/attachments | Replace Memory Attachments |
| [**updateMemory**](MemoriesApi.md#updatememory) | **PATCH** /api/v1/spaces/{spaceId}/memories/{memoryId} | Update Memory |



## createMemory

> MemoryDetail createMemory(spaceId, memoryCreate)

Create Memory

### Example

```ts
import {
  Configuration,
  MemoriesApi,
} from '';
import type { CreateMemoryRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new MemoriesApi();

  const body = {
    // string
    spaceId: spaceId_example,
    // MemoryCreate
    memoryCreate: ...,
  } satisfies CreateMemoryRequest;

  try {
    const data = await api.createMemory(body);
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
| **memoryCreate** | [MemoryCreate](MemoryCreate.md) |  | |

### Return type

[**MemoryDetail**](MemoryDetail.md)

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


## deleteMemory

> deleteMemory(memoryId, spaceId, ifMatch)

Delete Memory

### Example

```ts
import {
  Configuration,
  MemoriesApi,
} from '';
import type { DeleteMemoryRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new MemoriesApi();

  const body = {
    // string
    memoryId: memoryId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
  } satisfies DeleteMemoryRequest;

  try {
    const data = await api.deleteMemory(body);
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
| **memoryId** | `string` |  | [Defaults to `undefined`] |
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


## getMemory

> MemoryDetail getMemory(memoryId, spaceId)

Get Memory

### Example

```ts
import {
  Configuration,
  MemoriesApi,
} from '';
import type { GetMemoryRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new MemoriesApi();

  const body = {
    // string
    memoryId: memoryId_example,
    // string
    spaceId: spaceId_example,
  } satisfies GetMemoryRequest;

  try {
    const data = await api.getMemory(body);
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
| **memoryId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |

### Return type

[**MemoryDetail**](MemoryDetail.md)

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


## listMemories

> MemoryPage listMemories(spaceId, cursor, limit, year)

List Memories

### Example

```ts
import {
  Configuration,
  MemoriesApi,
} from '';
import type { ListMemoriesRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new MemoriesApi();

  const body = {
    // string
    spaceId: spaceId_example,
    // string (optional)
    cursor: cursor_example,
    // number (optional)
    limit: 56,
    // number (optional)
    year: 56,
  } satisfies ListMemoriesRequest;

  try {
    const data = await api.listMemories(body);
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
| **year** | `number` |  | [Optional] [Defaults to `undefined`] |

### Return type

[**MemoryPage**](MemoryPage.md)

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


## replaceMemoryAttachments

> MemoryDetail replaceMemoryAttachments(memoryId, spaceId, ifMatch, memoryAttachmentSet)

Replace Memory Attachments

Menge und Reihenfolge in einem Zug setzen.  Ein PUT, kein Hinzufuegen und Entfernen: der Client schickt den Zustand, den er gesehen hat, und &#x60;If-Match&#x60; sorgt dafuer, dass er ihn noch hat.

### Example

```ts
import {
  Configuration,
  MemoriesApi,
} from '';
import type { ReplaceMemoryAttachmentsRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new MemoriesApi();

  const body = {
    // string
    memoryId: memoryId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
    // MemoryAttachmentSet
    memoryAttachmentSet: ...,
  } satisfies ReplaceMemoryAttachmentsRequest;

  try {
    const data = await api.replaceMemoryAttachments(body);
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
| **memoryId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |
| **ifMatch** | `string` | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben. | [Defaults to `undefined`] |
| **memoryAttachmentSet** | [MemoryAttachmentSet](MemoryAttachmentSet.md) |  | |

### Return type

[**MemoryDetail**](MemoryDetail.md)

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


## updateMemory

> MemoryDetail updateMemory(memoryId, spaceId, ifMatch, memoryUpdate)

Update Memory

### Example

```ts
import {
  Configuration,
  MemoriesApi,
} from '';
import type { UpdateMemoryRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new MemoriesApi();

  const body = {
    // string
    memoryId: memoryId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
    // MemoryUpdate
    memoryUpdate: ...,
  } satisfies UpdateMemoryRequest;

  try {
    const data = await api.updateMemory(body);
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
| **memoryId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |
| **ifMatch** | `string` | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben. | [Defaults to `undefined`] |
| **memoryUpdate** | [MemoryUpdate](MemoryUpdate.md) |  | |

### Return type

[**MemoryDetail**](MemoryDetail.md)

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

