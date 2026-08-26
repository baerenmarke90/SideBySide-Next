# MilestonesApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createMilestone**](MilestonesApi.md#createmilestone) | **POST** /api/v1/spaces/{spaceId}/milestones | Create Milestone |
| [**deleteMilestone**](MilestonesApi.md#deletemilestone) | **DELETE** /api/v1/spaces/{spaceId}/milestones/{milestoneId} | Delete Milestone |
| [**getMilestone**](MilestonesApi.md#getmilestone) | **GET** /api/v1/spaces/{spaceId}/milestones/{milestoneId} | Get Milestone |
| [**listMilestones**](MilestonesApi.md#listmilestones) | **GET** /api/v1/spaces/{spaceId}/milestones | List Milestones |
| [**updateMilestone**](MilestonesApi.md#updatemilestone) | **PATCH** /api/v1/spaces/{spaceId}/milestones/{milestoneId} | Update Milestone |



## createMilestone

> MilestoneDetail createMilestone(spaceId, milestoneCreate)

Create Milestone

### Example

```ts
import {
  Configuration,
  MilestonesApi,
} from '';
import type { CreateMilestoneRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new MilestonesApi();

  const body = {
    // string
    spaceId: spaceId_example,
    // MilestoneCreate
    milestoneCreate: ...,
  } satisfies CreateMilestoneRequest;

  try {
    const data = await api.createMilestone(body);
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
| **milestoneCreate** | [MilestoneCreate](MilestoneCreate.md) |  | |

### Return type

[**MilestoneDetail**](MilestoneDetail.md)

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


## deleteMilestone

> deleteMilestone(milestoneId, spaceId, ifMatch)

Delete Milestone

### Example

```ts
import {
  Configuration,
  MilestonesApi,
} from '';
import type { DeleteMilestoneRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new MilestonesApi();

  const body = {
    // string
    milestoneId: milestoneId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
  } satisfies DeleteMilestoneRequest;

  try {
    const data = await api.deleteMilestone(body);
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
| **milestoneId** | `string` |  | [Defaults to `undefined`] |
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


## getMilestone

> MilestoneDetail getMilestone(milestoneId, spaceId)

Get Milestone

### Example

```ts
import {
  Configuration,
  MilestonesApi,
} from '';
import type { GetMilestoneRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new MilestonesApi();

  const body = {
    // string
    milestoneId: milestoneId_example,
    // string
    spaceId: spaceId_example,
  } satisfies GetMilestoneRequest;

  try {
    const data = await api.getMilestone(body);
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
| **milestoneId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |

### Return type

[**MilestoneDetail**](MilestoneDetail.md)

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


## listMilestones

> MilestonePage listMilestones(spaceId, cursor, limit, year)

List Milestones

### Example

```ts
import {
  Configuration,
  MilestonesApi,
} from '';
import type { ListMilestonesRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new MilestonesApi();

  const body = {
    // string
    spaceId: spaceId_example,
    // string (optional)
    cursor: cursor_example,
    // number (optional)
    limit: 56,
    // number (optional)
    year: 56,
  } satisfies ListMilestonesRequest;

  try {
    const data = await api.listMilestones(body);
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

[**MilestonePage**](MilestonePage.md)

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


## updateMilestone

> MilestoneDetail updateMilestone(milestoneId, spaceId, ifMatch, milestoneUpdate)

Update Milestone

### Example

```ts
import {
  Configuration,
  MilestonesApi,
} from '';
import type { UpdateMilestoneRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new MilestonesApi();

  const body = {
    // string
    milestoneId: milestoneId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
    // MilestoneUpdate
    milestoneUpdate: ...,
  } satisfies UpdateMilestoneRequest;

  try {
    const data = await api.updateMilestone(body);
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
| **milestoneId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |
| **ifMatch** | `string` | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben. | [Defaults to `undefined`] |
| **milestoneUpdate** | [MilestoneUpdate](MilestoneUpdate.md) |  | |

### Return type

[**MilestoneDetail**](MilestoneDetail.md)

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

