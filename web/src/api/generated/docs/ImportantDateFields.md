
# ImportantDateFields


## Properties

Name | Type
------------ | -------------
`date` | Date
`label` | string
`relatedPersonId` | string
`repeats` | [DateRepeat](DateRepeat.md)
`type` | [ImportantDateType](ImportantDateType.md)
`visibility` | [ContentVisibility](ContentVisibility.md)

## Example

```typescript
import type { ImportantDateFields } from ''

// TODO: Update the object below with actual values
const example = {
  "date": null,
  "label": null,
  "relatedPersonId": null,
  "repeats": null,
  "type": null,
  "visibility": null,
} satisfies ImportantDateFields

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ImportantDateFields
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


