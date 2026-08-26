
# WishToPlan

Der Konvertierungsrequest.  Alle Felder optional: ohne eigenen Titel uebernimmt der Plan den des Wishes. `sourceWishId`, `status` und die Termine kommen nicht vom Client - der Wish steht im Pfad, alles andere entsteht serverseitig.

## Properties

Name | Type
------------ | -------------
`description` | string
`title` | string

## Example

```typescript
import type { WishToPlan } from ''

// TODO: Update the object below with actual values
const example = {
  "description": null,
  "title": null,
} satisfies WishToPlan

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as WishToPlan
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


