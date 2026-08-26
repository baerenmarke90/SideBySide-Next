
# ProfilePreferenceCreate


## Properties

Name | Type
------------ | -------------
`accountId` | string
`category` | [PreferenceCategory](PreferenceCategory.md)
`sentiment` | [PreferenceSentiment](PreferenceSentiment.md)
`topic` | string
`value` | string
`visibility` | [ProfileVisibility](ProfileVisibility.md)

## Example

```typescript
import type { ProfilePreferenceCreate } from ''

// TODO: Update the object below with actual values
const example = {
  "accountId": null,
  "category": null,
  "sentiment": null,
  "topic": null,
  "value": null,
  "visibility": null,
} satisfies ProfilePreferenceCreate

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ProfilePreferenceCreate
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


