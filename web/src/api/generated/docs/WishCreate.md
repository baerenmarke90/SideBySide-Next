
# WishCreate

Ein Wish entsteht aus genau einem Feld.  `extra=\"forbid\"` ist hier mehr als Hygiene: `status`, `createdBy`, `spaceId` und `version` sind nach M3-D01/D02 serverseitig. Ein Request, der sie mitschickt, wird abgewiesen und nicht stillschweigend um sie erleichtert - sonst glaubte der Client, er haette sie gesetzt.

## Properties

Name | Type
------------ | -------------
`title` | string

## Example

```typescript
import type { WishCreate } from ''

// TODO: Update the object below with actual values
const example = {
  "title": null,
} satisfies WishCreate

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as WishCreate
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


