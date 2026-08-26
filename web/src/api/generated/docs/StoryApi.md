# StoryApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getStoryTimeline**](StoryApi.md#getstorytimeline) | **GET** /api/v1/spaces/{spaceId}/timeline | Get Story Timeline |



## getStoryTimeline

> StoryPage getStoryTimeline(spaceId, type, year, order, cursor, limit)

Get Story Timeline

Die gemeinsame Zeitleiste aus Memories, Milestones und HeartMoments.  Private HeartMoments erscheinen hier nie - auch nicht fuer ihren Owner.

### Example

```ts
import {
  Configuration,
  StoryApi,
} from '';
import type { GetStoryTimelineRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new StoryApi();

  const body = {
    // string
    spaceId: spaceId_example,
    // Array<StoryKind> (optional)
    type: ...,
    // number (optional)
    year: 56,
    // StoryOrder (optional)
    order: ...,
    // string (optional)
    cursor: cursor_example,
    // number (optional)
    limit: 56,
  } satisfies GetStoryTimelineRequest;

  try {
    const data = await api.getStoryTimeline(body);
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
| **type** | `Array<StoryKind>` |  | [Optional] |
| **year** | `number` |  | [Optional] [Defaults to `undefined`] |
| **order** | `StoryOrder` |  | [Optional] [Defaults to `undefined`] [Enum: ASC, DESC] |
| **cursor** | `string` |  | [Optional] [Defaults to `undefined`] |
| **limit** | `number` |  | [Optional] [Defaults to `50`] |

### Return type

[**StoryPage**](StoryPage.md)

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

