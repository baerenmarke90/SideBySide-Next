
# PartnerView

Was von einem Account nach aussen geht.  Ausdruecklich eine Whitelist. Am Account haengen Anmeldedaten und Kontaktangaben, die in einer Space-Antwort nichts verloren haben - und eine allgemeine Modell-Serialisierung wuerde sie irgendwann mitnehmen.

## Properties

Name | Type
------------ | -------------
`displayName` | string
`id` | string

## Example

```typescript
import type { PartnerView } from ''

// TODO: Update the object below with actual values
const example = {
  "displayName": null,
  "id": null,
} satisfies PartnerView

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as PartnerView
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


