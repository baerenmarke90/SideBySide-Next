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
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **404** | The resource does not exist or is not visible to the caller. |  -  |

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
| **200** | Successful Response |  * ETag - Resource version. Send it unchanged in the next write request\&#39;s &#x60;If-Match&#x60; header. <br>  |
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **404** | The resource does not exist or is not visible to the caller. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## updateSpaceProfileApiV1SpacesSpaceIdProfilePut

> SpaceProfileView updateSpaceProfileApiV1SpacesSpaceIdProfilePut(spaceId, ifMatch, spaceProfileUpdate)

Update Space Profile

Replace the relationship profile.  The caller supplies the version it read through &#x60;&#x60;If-Match&#x60;&#x60;. If the partner has written in the meantime, the endpoint returns 409 and changes nothing; otherwise simultaneous edits could silently overwrite each other.

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
    // string | The last-read resource version, encoded as a strong ETag. Writes are rejected without this header.
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
| **ifMatch** | `string` | The last-read resource version, encoded as a strong ETag. Writes are rejected without this header. | [Defaults to `undefined`] |
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
| **200** | Successful Response |  * ETag - Resource version. Send it unchanged in the next write request\&#39;s &#x60;If-Match&#x60; header. <br>  |
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **404** | The resource does not exist or is not visible to the caller. |  -  |
| **409** | The supplied version is no longer current. Nothing was changed; reload the latest state before retrying. |  -  |
| **422** | Request parameters or domain inputs are invalid. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

