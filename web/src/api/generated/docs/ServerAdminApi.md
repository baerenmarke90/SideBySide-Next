# ServerAdminApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getServerAdminOverviewApiV1ServerAdminOverviewGet**](ServerAdminApi.md#getserveradminoverviewapiv1serveradminoverviewget) | **GET** /api/v1/server-admin/overview | Get Server Admin Overview |



## getServerAdminOverviewApiV1ServerAdminOverviewGet

> ServerAdminOverview getServerAdminOverviewApiV1ServerAdminOverviewGet()

Get Server Admin Overview

Return safe operational state for an authorized ServerAdmin.

### Example

```ts
import {
  Configuration,
  ServerAdminApi,
} from '';
import type { GetServerAdminOverviewApiV1ServerAdminOverviewGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ServerAdminApi();

  try {
    const data = await api.getServerAdminOverviewApiV1ServerAdminOverviewGet();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**ServerAdminOverview**](ServerAdminOverview.md)

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
| **403** | The caller is authenticated but is not authorized for this operation. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

