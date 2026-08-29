
# PlanCreate

Direct plan creation defined by M3-D30.  ``status``, ``sourceWishId``, and all schedule fields are intentionally absent. A plan starts as an idea; ``/schedule`` schedules it and ``/complete`` completes it.

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


