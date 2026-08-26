
# ProfilePreferenceUpdate


## Properties

Name | Type
------------ | -------------
`category` | [PreferenceCategory](PreferenceCategory.md)
`sentiment` | [PreferenceSentiment](PreferenceSentiment.md)
`topic` | string
`value` | string

## Example

```typescript
import type { ProfilePreferenceUpdate } from ''

// TODO: Update the object below with actual values
const example = {
  "category": null,
  "sentiment": null,
  "topic": null,
  "value": null,
} satisfies ProfilePreferenceUpdate

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ProfilePreferenceUpdate
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


