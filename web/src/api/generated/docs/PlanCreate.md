
# PlanCreate

Direct Plan Create nach M3-D30.  `status`, `sourceWishId` und alle Termine fehlen bewusst. Ein Plan beginnt als Idee; terminiert wird er ueber `/schedule`, abgeschlossen ueber `/complete`.

## Properties

Name | Type
------------ | -------------
`description` | string
`placeId` | string
`title` | string

## Example

```typescript
import type { PlanCreate } from ''

// TODO: Update the object below with actual values
const example = {
  "description": null,
  "placeId": null,
  "title": null,
} satisfies PlanCreate

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as PlanCreate
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


