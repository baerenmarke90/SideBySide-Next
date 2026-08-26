
# AttachmentSummary

Die Projektion eines gebundenen Attachments an seinem Parent.  Ein Typ und nicht je Domaene einer: zwei gleichnamige DTOs haetten im OpenAPI-Vertrag modulqualifizierte Namen erzeugt und damit interne Pfade nach aussen getragen.

## Properties

Name | Type
------------ | -------------
`hasThumbnail` | boolean
`height` | number
`id` | string
`mediaType` | [MediaType](MediaType.md)
`mimeType` | string
`size` | number
`status` | string
`width` | number

## Example

```typescript
import type { AttachmentSummary } from ''

// TODO: Update the object below with actual values
const example = {
  "hasThumbnail": null,
  "height": null,
  "id": null,
  "mediaType": null,
  "mimeType": null,
  "size": null,
  "status": null,
  "width": null,
} satisfies AttachmentSummary

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as AttachmentSummary
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


