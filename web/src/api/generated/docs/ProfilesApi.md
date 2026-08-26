# ProfilesApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPost**](ProfilesApi.md#createprofilepreferenceapiv1spacesspaceidprofilepreferencespost) | **POST** /api/v1/spaces/{spaceId}/profile-preferences | Create Profile Preference |
| [**deleteProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdDelete**](ProfilesApi.md#deleteprofilepreferenceapiv1spacesspaceidprofilepreferencespreferenceiddelete) | **DELETE** /api/v1/spaces/{spaceId}/profile-preferences/{preferenceId} | Delete Profile Preference |
| [**getPartnerProfileApiV1SpacesSpaceIdProfilesAccountIdGet**](ProfilesApi.md#getpartnerprofileapiv1spacesspaceidprofilesaccountidget) | **GET** /api/v1/spaces/{spaceId}/profiles/{accountId} | Get Partner Profile |
| [**getProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdGet**](ProfilesApi.md#getprofilepreferenceapiv1spacesspaceidprofilepreferencespreferenceidget) | **GET** /api/v1/spaces/{spaceId}/profile-preferences/{preferenceId} | Get Profile Preference |
| [**listProfilePreferencesApiV1SpacesSpaceIdProfilePreferencesGet**](ProfilesApi.md#listprofilepreferencesapiv1spacesspaceidprofilepreferencesget) | **GET** /api/v1/spaces/{spaceId}/profile-preferences | List Profile Preferences |
| [**updateProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdPut**](ProfilesApi.md#updateprofilepreferenceapiv1spacesspaceidprofilepreferencespreferenceidput) | **PUT** /api/v1/spaces/{spaceId}/profile-preferences/{preferenceId} | Update Profile Preference |



## createProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPost

> ProfilePreferenceView createProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPost(spaceId, profilePreferenceCreate)

Create Profile Preference

### Example

```ts
import {
  Configuration,
  ProfilesApi,
} from '';
import type { CreateProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ProfilesApi();

  const body = {
    // string
    spaceId: spaceId_example,
    // ProfilePreferenceCreate
    profilePreferenceCreate: ...,
  } satisfies CreateProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPostRequest;

  try {
    const data = await api.createProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPost(body);
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
| **profilePreferenceCreate** | [ProfilePreferenceCreate](ProfilePreferenceCreate.md) |  | |

### Return type

[**ProfilePreferenceView**](ProfilePreferenceView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  * ETag - Version der ProfilePreference fuer den naechsten If-Match-Schreibzugriff. <br>  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **403** | Der Aufrufer ist authentifiziert, aber fuer diesen Vorgang nicht berechtigt. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## deleteProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdDelete

> deleteProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdDelete(preferenceId, spaceId, ifMatch)

Delete Profile Preference

### Example

```ts
import {
  Configuration,
  ProfilesApi,
} from '';
import type { DeleteProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdDeleteRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ProfilesApi();

  const body = {
    // string
    preferenceId: preferenceId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
  } satisfies DeleteProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdDeleteRequest;

  try {
    const data = await api.deleteProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdDelete(body);
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
| **preferenceId** | `string` |  | [Defaults to `undefined`] |
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


## getPartnerProfileApiV1SpacesSpaceIdProfilesAccountIdGet

> PartnerProfileView getPartnerProfileApiV1SpacesSpaceIdProfilesAccountIdGet(accountId, spaceId)

Get Partner Profile

### Example

```ts
import {
  Configuration,
  ProfilesApi,
} from '';
import type { GetPartnerProfileApiV1SpacesSpaceIdProfilesAccountIdGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ProfilesApi();

  const body = {
    // string
    accountId: accountId_example,
    // string
    spaceId: spaceId_example,
  } satisfies GetPartnerProfileApiV1SpacesSpaceIdProfilesAccountIdGetRequest;

  try {
    const data = await api.getPartnerProfileApiV1SpacesSpaceIdProfilesAccountIdGet(body);
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
| **accountId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |

### Return type

[**PartnerProfileView**](PartnerProfileView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdGet

> ProfilePreferenceView getProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdGet(preferenceId, spaceId)

Get Profile Preference

### Example

```ts
import {
  Configuration,
  ProfilesApi,
} from '';
import type { GetProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ProfilesApi();

  const body = {
    // string
    preferenceId: preferenceId_example,
    // string
    spaceId: spaceId_example,
  } satisfies GetProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdGetRequest;

  try {
    const data = await api.getProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdGet(body);
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
| **preferenceId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |

### Return type

[**ProfilePreferenceView**](ProfilePreferenceView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  * ETag - Version der ProfilePreference fuer den naechsten If-Match-Schreibzugriff. <br>  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## listProfilePreferencesApiV1SpacesSpaceIdProfilePreferencesGet

> Array&lt;ProfilePreferenceView&gt; listProfilePreferencesApiV1SpacesSpaceIdProfilePreferencesGet(spaceId)

List Profile Preferences

### Example

```ts
import {
  Configuration,
  ProfilesApi,
} from '';
import type { ListProfilePreferencesApiV1SpacesSpaceIdProfilePreferencesGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ProfilesApi();

  const body = {
    // string
    spaceId: spaceId_example,
  } satisfies ListProfilePreferencesApiV1SpacesSpaceIdProfilePreferencesGetRequest;

  try {
    const data = await api.listProfilePreferencesApiV1SpacesSpaceIdProfilePreferencesGet(body);
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

[**Array&lt;ProfilePreferenceView&gt;**](ProfilePreferenceView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## updateProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdPut

> ProfilePreferenceView updateProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdPut(preferenceId, spaceId, ifMatch, profilePreferenceUpdate)

Update Profile Preference

### Example

```ts
import {
  Configuration,
  ProfilesApi,
} from '';
import type { UpdateProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdPutRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ProfilesApi();

  const body = {
    // string
    preferenceId: preferenceId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
    // ProfilePreferenceUpdate
    profilePreferenceUpdate: ...,
  } satisfies UpdateProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdPutRequest;

  try {
    const data = await api.updateProfilePreferenceApiV1SpacesSpaceIdProfilePreferencesPreferenceIdPut(body);
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
| **preferenceId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |
| **ifMatch** | `string` | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben. | [Defaults to `undefined`] |
| **profilePreferenceUpdate** | [ProfilePreferenceUpdate](ProfilePreferenceUpdate.md) |  | |

### Return type

[**ProfilePreferenceView**](ProfilePreferenceView.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  * ETag - Version der ProfilePreference fuer den naechsten If-Match-Schreibzugriff. <br>  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **403** | Der Aufrufer ist authentifiziert, aber fuer diesen Vorgang nicht berechtigt. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **409** | Die Anfrage kollidiert mit dem aktuellen Zustand der Ressource. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

