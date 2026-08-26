
# SpaceView


## Properties

Name | Type
------------ | -------------
`createdAt` | Date
`durationDisplayMode` | string
`id` | string
`partners` | [Array&lt;PartnerView&gt;](PartnerView.md)
`relationshipDays` | number
`relationshipMonths` | number
`relationshipStartedOn` | string
`relationshipYears` | number
`showRelationshipDuration` | boolean

## Example

```typescript
import type { SpaceView } from ''

// TODO: Update the object below with actual values
const example = {
  "createdAt": null,
  "durationDisplayMode": null,
  "id": null,
  "partners": null,
  "relationshipDays": null,
  "relationshipMonths": null,
  "relationshipStartedOn": null,
  "relationshipYears": null,
  "showRelationshipDuration": null,
} satisfies SpaceView

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as SpaceView
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


