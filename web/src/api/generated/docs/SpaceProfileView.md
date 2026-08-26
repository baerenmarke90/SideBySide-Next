
# SpaceProfileView

Das Beziehungsprofil eines Space.  `version` ist der Stand, den ein spaeterer Schreibzugriff per `If-Match` vorlegen muss. Die Antwort traegt ihn zusaetzlich als ETag.

## Properties

Name | Type
------------ | -------------
`durationDisplayMode` | [DurationDisplayMode](DurationDisplayMode.md)
`relationshipDays` | number
`relationshipMonths` | number
`relationshipStartedOn` | Date
`relationshipYears` | number
`showRelationshipDuration` | boolean
`spaceId` | string
`version` | number

## Example

```typescript
import type { SpaceProfileView } from ''

// TODO: Update the object below with actual values
const example = {
  "durationDisplayMode": null,
  "relationshipDays": null,
  "relationshipMonths": null,
  "relationshipStartedOn": null,
  "relationshipYears": null,
  "showRelationshipDuration": null,
  "spaceId": null,
  "version": null,
} satisfies SpaceProfileView

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as SpaceProfileView
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


