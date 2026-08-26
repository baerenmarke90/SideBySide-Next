
# SpaceProfileUpdate

Der vollstaendige neue Stand des Profils.  Alle drei Felder sind Pflicht. Ein weggelassenes Feld waere sonst nicht von \"auf leer setzen\" zu unterscheiden - und der Unterschied entscheidet darueber, ob ein Beziehungsbeginn erhalten bleibt oder verschwindet. `relationshipStartedOn` wird mit `null` ausdruecklich geloescht.

## Properties

Name | Type
------------ | -------------
`durationDisplayMode` | [DurationDisplayMode](DurationDisplayMode.md)
`relationshipStartedOn` | Date
`showRelationshipDuration` | boolean

## Example

```typescript
import type { SpaceProfileUpdate } from ''

// TODO: Update the object below with actual values
const example = {
  "durationDisplayMode": null,
  "relationshipStartedOn": null,
  "showRelationshipDuration": null,
} satisfies SpaceProfileUpdate

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as SpaceProfileUpdate
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


