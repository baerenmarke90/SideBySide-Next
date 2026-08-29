
# WishToPlan

Wish-to-Plan conversion request.  Every field is optional: without an explicit title the plan inherits the wish title. ``sourceWishId``, ``status``, and schedule fields are not supplied by the client; the wish is identified by the path and everything else is established server-side.

## Properties

Name | Type
------------ | -------------
`description` | string
`placeId` | string
`title` | string

## Example

```typescript
import type { WishToPlan } from ''

// TODO: Update the object below with actual values
const example = {
  "description": null,
  "placeId": null,
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


