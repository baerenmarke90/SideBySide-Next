# ActivityApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getActivity**](ActivityApi.md#getactivity) | **GET** /api/v1/spaces/{spaceId}/activity | Get Activity |
| [**getNotificationUnreadCount**](ActivityApi.md#getnotificationunreadcount) | **GET** /api/v1/spaces/{spaceId}/notifications/unread-count | Get Notification Unread Count |
| [**getNotifications**](ActivityApi.md#getnotifications) | **GET** /api/v1/spaces/{spaceId}/notifications | Get Notifications |
| [**markAllNotificationsRead**](ActivityApi.md#markallnotificationsread) | **POST** /api/v1/spaces/{spaceId}/notifications/read-all | Mark All Notifications Read |
| [**markNotificationRead**](ActivityApi.md#marknotificationread) | **POST** /api/v1/spaces/{spaceId}/notifications/{notificationId}/read | Mark Notification Read |



## getActivity

> ActivityPage getActivity(spaceId, cursor, limit)

Get Activity

### Example

```ts
import {
  Configuration,
  ActivityApi,
} from '';
import type { GetActivityRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ActivityApi();

  const body = {
    // string
    spaceId: spaceId_example,
    // string (optional)
    cursor: cursor_example,
    // number (optional)
    limit: 56,
  } satisfies GetActivityRequest;

  try {
    const data = await api.getActivity(body);
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
| **limit** | `number` |  | [Optional] [Defaults to `25`] |

### Return type

[**ActivityPage**](ActivityPage.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **400** | The request is syntactically valid but cannot be processed in this form. |  -  |
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **404** | The resource does not exist or is not visible to the caller. |  -  |
| **422** | Request parameters or domain inputs are invalid. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getNotificationUnreadCount

> NotificationUnreadCount getNotificationUnreadCount(spaceId)

Get Notification Unread Count

### Example

```ts
import {
  Configuration,
  ActivityApi,
} from '';
import type { GetNotificationUnreadCountRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ActivityApi();

  const body = {
    // string
    spaceId: spaceId_example,
  } satisfies GetNotificationUnreadCountRequest;

  try {
    const data = await api.getNotificationUnreadCount(body);
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

[**NotificationUnreadCount**](NotificationUnreadCount.md)

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


## getNotifications

> NotificationPage getNotifications(spaceId, cursor, limit)

Get Notifications

### Example

```ts
import {
  Configuration,
  ActivityApi,
} from '';
import type { GetNotificationsRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ActivityApi();

  const body = {
    // string
    spaceId: spaceId_example,
    // string (optional)
    cursor: cursor_example,
    // number (optional)
    limit: 56,
  } satisfies GetNotificationsRequest;

  try {
    const data = await api.getNotifications(body);
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
| **limit** | `number` |  | [Optional] [Defaults to `25`] |

### Return type

[**NotificationPage**](NotificationPage.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **400** | The request is syntactically valid but cannot be processed in this form. |  -  |
| **401** | Authentication is missing, invalid, or the session has expired. |  -  |
| **404** | The resource does not exist or is not visible to the caller. |  -  |
| **422** | Request parameters or domain inputs are invalid. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## markAllNotificationsRead

> NotificationsReadAllResult markAllNotificationsRead(spaceId)

Mark All Notifications Read

### Example

```ts
import {
  Configuration,
  ActivityApi,
} from '';
import type { MarkAllNotificationsReadRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ActivityApi();

  const body = {
    // string
    spaceId: spaceId_example,
  } satisfies MarkAllNotificationsReadRequest;

  try {
    const data = await api.markAllNotificationsRead(body);
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

[**NotificationsReadAllResult**](NotificationsReadAllResult.md)

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


## markNotificationRead

> NotificationItem markNotificationRead(notificationId, spaceId)

Mark Notification Read

### Example

```ts
import {
  Configuration,
  ActivityApi,
} from '';
import type { MarkNotificationReadRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ActivityApi();

  const body = {
    // string
    notificationId: 38400000-8cf0-11bd-b23e-10b96e4ef00d,
    // string
    spaceId: spaceId_example,
  } satisfies MarkNotificationReadRequest;

  try {
    const data = await api.markNotificationRead(body);
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
| **notificationId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |

### Return type

[**NotificationItem**](NotificationItem.md)

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

