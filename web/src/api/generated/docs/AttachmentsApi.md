# AttachmentsApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createAttachmentReadAccess**](AttachmentsApi.md#createattachmentreadaccess) | **POST** /api/v1/spaces/{spaceId}/attachments/{attachmentId}/read-access | Create Attachment Read Access |
| [**createAttachmentUpload**](AttachmentsApi.md#createattachmentupload) | **POST** /api/v1/spaces/{spaceId}/attachments | Create Attachment Upload |
| [**deleteAttachment**](AttachmentsApi.md#deleteattachment) | **DELETE** /api/v1/spaces/{spaceId}/attachments/{attachmentId} | Delete Attachment |
| [**finalizeAttachmentUpload**](AttachmentsApi.md#finalizeattachmentupload) | **POST** /api/v1/spaces/{spaceId}/attachments/{attachmentId}/finalize | Finalize Attachment Upload |
| [**getAttachment**](AttachmentsApi.md#getattachment) | **GET** /api/v1/spaces/{spaceId}/attachments/{attachmentId} | Get Attachment |
| [**getAttachmentContent**](AttachmentsApi.md#getattachmentcontent) | **GET** /api/v1/spaces/{spaceId}/attachments/{attachmentId}/content | Get Attachment Content |
| [**uploadAttachmentContent**](AttachmentsApi.md#uploadattachmentcontent) | **PUT** /api/v1/spaces/{spaceId}/attachments/{attachmentId}/content | Upload Attachment Content |



## createAttachmentReadAccess

> ReadDescriptor createAttachmentReadAccess(attachmentId, spaceId, attachmentReadRequest)

Create Attachment Read Access

### Example

```ts
import {
  Configuration,
  AttachmentsApi,
} from '';
import type { CreateAttachmentReadAccessRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AttachmentsApi();

  const body = {
    // string
    attachmentId: attachmentId_example,
    // string
    spaceId: spaceId_example,
    // AttachmentReadRequest
    attachmentReadRequest: ...,
  } satisfies CreateAttachmentReadAccessRequest;

  try {
    const data = await api.createAttachmentReadAccess(body);
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
| **attachmentId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |
| **attachmentReadRequest** | [AttachmentReadRequest](AttachmentReadRequest.md) |  | |

### Return type

[**ReadDescriptor**](ReadDescriptor.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **403** | Der Aufrufer ist authentifiziert, aber fuer diesen Vorgang nicht berechtigt. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **409** | Die Anfrage kollidiert mit dem aktuellen Zustand der Ressource. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## createAttachmentUpload

> UploadDescriptor createAttachmentUpload(spaceId, attachmentUploadCreate)

Create Attachment Upload

### Example

```ts
import {
  Configuration,
  AttachmentsApi,
} from '';
import type { CreateAttachmentUploadRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AttachmentsApi();

  const body = {
    // string
    spaceId: spaceId_example,
    // AttachmentUploadCreate
    attachmentUploadCreate: ...,
  } satisfies CreateAttachmentUploadRequest;

  try {
    const data = await api.createAttachmentUpload(body);
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
| **attachmentUploadCreate** | [AttachmentUploadCreate](AttachmentUploadCreate.md) |  | |

### Return type

[**UploadDescriptor**](UploadDescriptor.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **413** | Der Inhalt ueberschreitet die serverseitige Groessengrenze. |  -  |
| **415** | Der Medientyp steht nicht auf der Allowlist. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## deleteAttachment

> deleteAttachment(attachmentId, spaceId, ifMatch)

Delete Attachment

### Example

```ts
import {
  Configuration,
  AttachmentsApi,
} from '';
import type { DeleteAttachmentRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AttachmentsApi();

  const body = {
    // string
    attachmentId: attachmentId_example,
    // string
    spaceId: spaceId_example,
    // string | Die zuletzt gelesene Version der Ressource, als starkes ETag. Ohne diesen Kopf wird nicht geschrieben.
    ifMatch: ifMatch_example,
  } satisfies DeleteAttachmentRequest;

  try {
    const data = await api.deleteAttachment(body);
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
| **attachmentId** | `string` |  | [Defaults to `undefined`] |
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


## finalizeAttachmentUpload

> AttachmentDetail finalizeAttachmentUpload(attachmentId, spaceId, body)

Finalize Attachment Upload

### Example

```ts
import {
  Configuration,
  AttachmentsApi,
} from '';
import type { FinalizeAttachmentUploadRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AttachmentsApi();

  const body = {
    // string
    attachmentId: attachmentId_example,
    // string
    spaceId: spaceId_example,
    // object
    body: Object,
  } satisfies FinalizeAttachmentUploadRequest;

  try {
    const data = await api.finalizeAttachmentUpload(body);
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
| **attachmentId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |
| **body** | `object` |  | |

### Return type

[**AttachmentDetail**](AttachmentDetail.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **202** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **403** | Der Aufrufer ist authentifiziert, aber fuer diesen Vorgang nicht berechtigt. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **409** | Die Anfrage kollidiert mit dem aktuellen Zustand der Ressource. |  -  |
| **422** | Anfrageparameter oder fachliche Eingaben sind ungueltig. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getAttachment

> AttachmentDetail getAttachment(attachmentId, spaceId)

Get Attachment

### Example

```ts
import {
  Configuration,
  AttachmentsApi,
} from '';
import type { GetAttachmentRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AttachmentsApi();

  const body = {
    // string
    attachmentId: attachmentId_example,
    // string
    spaceId: spaceId_example,
  } satisfies GetAttachmentRequest;

  try {
    const data = await api.getAttachment(body);
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
| **attachmentId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |

### Return type

[**AttachmentDetail**](AttachmentDetail.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  * ETag -  <br>  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getAttachmentContent

> getAttachmentContent(attachmentId, spaceId, variant)

Get Attachment Content

Die autorisierte Streamingroute (Media-Pipeline, Abschnitt 9).  Jeder Zugriff wird unmittelbar vor dem Oeffnen geprueft. Der zuvor ausgestellte ReadDescriptor ist kein Ausweis: er verkuerzt nichts und ersetzt diese Pruefung nicht.

### Example

```ts
import {
  Configuration,
  AttachmentsApi,
} from '';
import type { GetAttachmentContentRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AttachmentsApi();

  const body = {
    // string
    attachmentId: attachmentId_example,
    // string
    spaceId: spaceId_example,
    // 'original' | 'thumbnail' (optional)
    variant: variant_example,
  } satisfies GetAttachmentContentRequest;

  try {
    const data = await api.getAttachmentContent(body);
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
| **attachmentId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |
| **variant** | `original`, `thumbnail` |  | [Optional] [Defaults to `&#39;original&#39;`] [Enum: original, thumbnail] |

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
| **200** | Successful Response |  -  |
| **401** | Authentifizierung fehlt, ist ungueltig oder die Sitzung ist abgelaufen. |  -  |
| **403** | Der Aufrufer ist authentifiziert, aber fuer diesen Vorgang nicht berechtigt. |  -  |
| **404** | Die Ressource existiert nicht oder ist fuer den Aufrufer nicht sichtbar. |  -  |
| **409** | Die Anfrage kollidiert mit dem aktuellen Zustand der Ressource. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## uploadAttachmentContent

> uploadAttachmentContent(attachmentId, spaceId)

Upload Attachment Content

Die Bytes im Serverstream entgegennehmen (M2-D13, Local-Adapter).  Zwei Dinge stehen hier bewusst in dieser Reihenfolge.  Erst wird autorisiert, dann gelesen. Andernfalls entschiede ein beliebiger Absender darueber, wie viel der Server entgegennimmt, bevor feststeht, ob er ueberhaupt hochladen darf.  Und gelesen wird gegen eine Grenze. &#x60;await request.body()&#x60; wuerde den ganzen Koerper puffern, wie gross er auch ist - die Media-Pipeline verlangt ausdruecklich kein unbegrenztes Puffern im RAM. Der Strom bricht deshalb bei der ersten Ueberschreitung ab, statt erst danach zu messen.

### Example

```ts
import {
  Configuration,
  AttachmentsApi,
} from '';
import type { UploadAttachmentContentRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AttachmentsApi();

  const body = {
    // string
    attachmentId: attachmentId_example,
    // string
    spaceId: spaceId_example,
  } satisfies UploadAttachmentContentRequest;

  try {
    const data = await api.uploadAttachmentContent(body);
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
| **attachmentId** | `string` |  | [Defaults to `undefined`] |
| **spaceId** | `string` |  | [Defaults to `undefined`] |

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
| **413** | Der Inhalt ueberschreitet die serverseitige Groessengrenze. |  -  |
| **415** | Der Medientyp steht nicht auf der Allowlist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

