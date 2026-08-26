# CommentsApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createHeartMomentComment**](CommentsApi.md#createheartmomentcomment) | **POST** /api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}/comments | Create Heart Moment Comment |
| [**createMemoryComment**](CommentsApi.md#creatememorycomment) | **POST** /api/v1/spaces/{spaceId}/memories/{memoryId}/comments | Create Memory Comment |
| [**createMilestoneComment**](CommentsApi.md#createmilestonecomment) | **POST** /api/v1/spaces/{spaceId}/milestones/{milestoneId}/comments | Create Milestone Comment |
| [**deleteComment**](CommentsApi.md#deletecomment) | **DELETE** /api/v1/spaces/{spaceId}/comments/{commentId} | Delete Comment |
| [**listHeartMomentComments**](CommentsApi.md#listheartmomentcomments) | **GET** /api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}/comments | List Heart Moment Comments |
| [**listMemoryComments**](CommentsApi.md#listmemorycomments) | **GET** /api/v1/spaces/{spaceId}/memories/{memoryId}/comments | List Memory Comments |
| [**listMilestoneComments**](CommentsApi.md#listmilestonecomments) | **GET** /api/v1/spaces/{spaceId}/milestones/{milestoneId}/comments | List Milestone Comments |
| [**updateComment**](CommentsApi.md#updatecomment) | **PATCH** /api/v1/spaces/{spaceId}/comments/{commentId} | Update Comment |



## createHeartMomentComment

> CommentDetail createHeartMomentComment(heartMomentId, spaceId, commentCreate)

Create Heart Moment Comment

### Example

```ts
import {
  Configuration,
  CommentsApi,
} from '';
import type { CreateHeartMomentCommentRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new CommentsApi();

  const body = {
    // string
    heartMomentId: heartMomentId_example,
    // string
    spaceId: spaceId_example,
    // CommentCreate
    commentCreate: ...,
  } satisfies CreateHeartMomentCommentRequest;

  try {
    const data = await api.createHeartMomentComment(body);
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
| **commentCreate** | [CommentCreate](CommentCreate.md) |  | |

### Return type

[**CommentDetail**](CommentDetail.md)

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


## createMemoryComment

> CommentDetail createMemoryComment(memoryId, spaceId, commentCreate)

Create Memory Comment

### Example

```ts
import {
  Configuration,
  CommentsApi,
} from '';
import type { CreateMemoryCommentRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new CommentsApi();

  const body = {
    // string
    memoryId: memoryId_example,
    // string
    spaceId: spaceId_example,
    // CommentCreate
    commentCreate: ...,
  } satisfies CreateMemoryCommentRequest;

  try {
    const data = await api.createMemoryComment(body);
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
| **commentCreate** | [CommentCreate](CommentCreate.md) |  | |

### Return type

[**CommentDetail**](CommentDetail.md)

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


## createMilestoneComment

> CommentDetail createMilestoneComment(milestoneId, spaceId, commentCreate)

Create Milestone Comment

### Example

```ts
import {
  Configuration,
  CommentsApi,
} from '';
import type { CreateMilestoneCommentRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new CommentsApi();

  const body = {
    // string
    milestoneId: milestoneId_example,
    // string
    spaceId: spaceId_example,
    // CommentCreate
    commentCreate: ...,
  } satisfies CreateMilestoneCommentRequest;

  try {
    const data = await api.createMilestoneComment(body);
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
| **commentCreate** | [CommentCreate](CommentCreate.md) |  | |

### Return type

[**CommentDetail**](CommentDetail.md)

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


## deleteComment

> deleteComment(commentId, spaceId, ifMatch)

Delete Comment

### Example

```ts
import {
  Configuration,
  CommentsApi,
} from '';
import type { DeleteCommentRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new CommentsApi();

  const body = {
    // string
    commentId: commentId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
  } satisfies DeleteCommentRequest;

  try {
    const data = await api.deleteComment(body);
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
| **commentId** | `string` |  | [Defaults to `undefined`] |
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


## listHeartMomentComments

> CommentPage listHeartMomentComments(heartMomentId, spaceId, cursor, limit)

List Heart Moment Comments

### Example

```ts
import {
  Configuration,
  CommentsApi,
} from '';
import type { ListHeartMomentCommentsRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new CommentsApi();

  const body = {
    // string
    heartMomentId: heartMomentId_example,
    // string
    spaceId: spaceId_example,
    // string (optional)
    cursor: cursor_example,
    // number (optional)
    limit: 56,
  } satisfies ListHeartMomentCommentsRequest;

  try {
    const data = await api.listHeartMomentComments(body);
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
| **cursor** | `string` |  | [Optional] [Defaults to `undefined`] |
| **limit** | `number` |  | [Optional] [Defaults to `50`] |

### Return type

[**CommentPage**](CommentPage.md)

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


## listMemoryComments

> CommentPage listMemoryComments(memoryId, spaceId, cursor, limit)

List Memory Comments

### Example

```ts
import {
  Configuration,
  CommentsApi,
} from '';
import type { ListMemoryCommentsRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new CommentsApi();

  const body = {
    // string
    memoryId: memoryId_example,
    // string
    spaceId: spaceId_example,
    // string (optional)
    cursor: cursor_example,
    // number (optional)
    limit: 56,
  } satisfies ListMemoryCommentsRequest;

  try {
    const data = await api.listMemoryComments(body);
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
| **cursor** | `string` |  | [Optional] [Defaults to `undefined`] |
| **limit** | `number` |  | [Optional] [Defaults to `50`] |

### Return type

[**CommentPage**](CommentPage.md)

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


## listMilestoneComments

> CommentPage listMilestoneComments(milestoneId, spaceId, cursor, limit)

List Milestone Comments

### Example

```ts
import {
  Configuration,
  CommentsApi,
} from '';
import type { ListMilestoneCommentsRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new CommentsApi();

  const body = {
    // string
    milestoneId: milestoneId_example,
    // string
    spaceId: spaceId_example,
    // string (optional)
    cursor: cursor_example,
    // number (optional)
    limit: 56,
  } satisfies ListMilestoneCommentsRequest;

  try {
    const data = await api.listMilestoneComments(body);
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
| **cursor** | `string` |  | [Optional] [Defaults to `undefined`] |
| **limit** | `number` |  | [Optional] [Defaults to `50`] |

### Return type

[**CommentPage**](CommentPage.md)

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


## updateComment

> CommentDetail updateComment(commentId, spaceId, ifMatch, commentUpdate)

Update Comment

### Example

```ts
import {
  Configuration,
  CommentsApi,
} from '';
import type { UpdateCommentRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new CommentsApi();

  const body = {
    // string
    commentId: commentId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
    // CommentUpdate
    commentUpdate: ...,
  } satisfies UpdateCommentRequest;

  try {
    const data = await api.updateComment(body);
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
| **commentId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |
| **ifMatch** | `string` | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben. | [Defaults to `undefined`] |
| **commentUpdate** | [CommentUpdate](CommentUpdate.md) |  | |

### Return type

[**CommentDetail**](CommentDetail.md)

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

