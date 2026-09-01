# ServerAdminApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getServerAdminActivityApiV1ServerAdminActivityGet**](ServerAdminApi.md#getserveradminactivityapiv1serveradminactivityget) | **GET** /api/v1/server-admin/activity | Get Server Admin Activity |
| [**getServerAdminOverviewApiV1ServerAdminOverviewGet**](ServerAdminApi.md#getserveradminoverviewapiv1serveradminoverviewget) | **GET** /api/v1/server-admin/overview | Get Server Admin Overview |
| [**getServerAdminSettingsApiV1ServerAdminSettingsGet**](ServerAdminApi.md#getserveradminsettingsapiv1serveradminsettingsget) | **GET** /api/v1/server-admin/settings | Get Server Admin Settings |
| [**updateMaintenanceSettingApiV1ServerAdminSettingsMaintenancePut**](ServerAdminApi.md#updatemaintenancesettingapiv1serveradminsettingsmaintenanceput) | **PUT** /api/v1/server-admin/settings/maintenance | Update Maintenance Setting |
| [**updateRegistrationSettingApiV1ServerAdminSettingsRegistrationPut**](ServerAdminApi.md#updateregistrationsettingapiv1serveradminsettingsregistrationput) | **PUT** /api/v1/server-admin/settings/registration | Update Registration Setting |



## getServerAdminActivityApiV1ServerAdminActivityGet

> Array&lt;ServerAdminActivityItem&gt; getServerAdminActivityApiV1ServerAdminActivityGet()

Get Server Admin Activity

### Example

```ts
import {
  Configuration,
  ServerAdminApi,
} from '';
import type { GetServerAdminActivityApiV1ServerAdminActivityGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ServerAdminApi();

  try {
    const data = await api.getServerAdminActivityApiV1ServerAdminActivityGet();
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

[**Array&lt;ServerAdminActivityItem&gt;**](ServerAdminActivityItem.md)

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


## getServerAdminSettingsApiV1ServerAdminSettingsGet

> ServerAdminSettings getServerAdminSettingsApiV1ServerAdminSettingsGet()

Get Server Admin Settings

### Example

```ts
import {
  Configuration,
  ServerAdminApi,
} from '';
import type { GetServerAdminSettingsApiV1ServerAdminSettingsGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ServerAdminApi();

  try {
    const data = await api.getServerAdminSettingsApiV1ServerAdminSettingsGet();
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

[**ServerAdminSettings**](ServerAdminSettings.md)

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


## updateMaintenanceSettingApiV1ServerAdminSettingsMaintenancePut

> ServerAdminSettings updateMaintenanceSettingApiV1ServerAdminSettingsMaintenancePut(serverAdminSettingUpdate)

Update Maintenance Setting

### Example

```ts
import {
  Configuration,
  ServerAdminApi,
} from '';
import type { UpdateMaintenanceSettingApiV1ServerAdminSettingsMaintenancePutRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ServerAdminApi();

  const body = {
    // ServerAdminSettingUpdate
    serverAdminSettingUpdate: ...,
  } satisfies UpdateMaintenanceSettingApiV1ServerAdminSettingsMaintenancePutRequest;

  try {
    const data = await api.updateMaintenanceSettingApiV1ServerAdminSettingsMaintenancePut(body);
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
| **serverAdminSettingUpdate** | [ServerAdminSettingUpdate](ServerAdminSettingUpdate.md) |  | |

### Return type

[**ServerAdminSettings**](ServerAdminSettings.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **403** | The caller is authenticated but is not authorized for this operation. |  -  |
| **422** | Request parameters or domain inputs are invalid. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## updateRegistrationSettingApiV1ServerAdminSettingsRegistrationPut

> ServerAdminSettings updateRegistrationSettingApiV1ServerAdminSettingsRegistrationPut(serverAdminSettingUpdate)

Update Registration Setting

### Example

```ts
import {
  Configuration,
  ServerAdminApi,
} from '';
import type { UpdateRegistrationSettingApiV1ServerAdminSettingsRegistrationPutRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ServerAdminApi();

  const body = {
    // ServerAdminSettingUpdate
    serverAdminSettingUpdate: ...,
  } satisfies UpdateRegistrationSettingApiV1ServerAdminSettingsRegistrationPutRequest;

  try {
    const data = await api.updateRegistrationSettingApiV1ServerAdminSettingsRegistrationPut(body);
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
| **serverAdminSettingUpdate** | [ServerAdminSettingUpdate](ServerAdminSettingUpdate.md) |  | |

### Return type

[**ServerAdminSettings**](ServerAdminSettings.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **403** | The caller is authenticated but is not authorized for this operation. |  -  |
| **422** | Request parameters or domain inputs are invalid. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

