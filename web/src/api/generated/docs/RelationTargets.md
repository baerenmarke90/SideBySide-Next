
# RelationTargets

Die verknuepften Ziele eines Ortes.  Ausschliesslich IDs. Inhalte kommen ueber die Route der jeweiligen Domaene und damit durch deren eigenen Guard; eine Relationsliste, die Inhalte mitliefert, waere ein zweiter Leseweg mit eigener Autorisierung.

## Properties

Name | Type
------------ | -------------
`items` | Array&lt;string&gt;

## Example

```typescript
import type { RelationTargets } from ''

// TODO: Update the object below with actual values
const example = {
  "items": null,
} satisfies RelationTargets

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as RelationTargets
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


