
# ProfilePreferenceView


## Properties

Name | Type
------------ | -------------
`accountId` | string
`category` | [PreferenceCategory](PreferenceCategory.md)
`createdAt` | Date
`id` | string
`sentiment` | [PreferenceSentiment](PreferenceSentiment.md)
`topic` | string
`updatedAt` | Date
`value` | string
`version` | number
`visibility` | [ProfileVisibility](ProfileVisibility.md)

## Example

```typescript
import type { ProfilePreferenceView } from ''

// TODO: Update the object below with actual values
const example = {
  "accountId": null,
  "category": null,
  "createdAt": null,
  "id": null,
  "sentiment": null,
  "topic": null,
  "updatedAt": null,
  "value": null,
  "version": null,
  "visibility": null,
} satisfies ProfilePreferenceView

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ProfilePreferenceView
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


