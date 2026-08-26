
# ImportantDateView


## Properties

Name | Type
------------ | -------------
`createdAt` | Date
`date` | Date
`id` | string
`label` | string
`relatedPersonId` | string
`repeats` | [DateRepeat](DateRepeat.md)
`type` | [ImportantDateType](ImportantDateType.md)
`updatedAt` | Date
`version` | number
`visibility` | [ContentVisibility](ContentVisibility.md)

## Example

```typescript
import type { ImportantDateView } from ''

// TODO: Update the object below with actual values
const example = {
  "createdAt": null,
  "date": null,
  "id": null,
  "label": null,
  "relatedPersonId": null,
  "repeats": null,
  "type": null,
  "updatedAt": null,
  "version": null,
  "visibility": null,
} satisfies ImportantDateView

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ImportantDateView
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


