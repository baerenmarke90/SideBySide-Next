# DashboardApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getDashboard**](DashboardApi.md#getdashboard) | **GET** /api/v1/spaces/{spaceId}/dashboard | Get Dashboard |



## getDashboard

> DashboardView getDashboard(spaceId)

Get Dashboard

Return the shared-only relationship overview for one Space.

### Example

```ts
import {
  Configuration,
  DashboardApi,
} from '';
import type { GetDashboardRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new DashboardApi();

  const body = {
    // string
    spaceId: spaceId_example,
  } satisfies GetDashboardRequest;

  try {
    const data = await api.getDashboard(body);
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

[**DashboardView**](DashboardView.md)

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
| **422** | Request parameters or domain inputs are invalid. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

