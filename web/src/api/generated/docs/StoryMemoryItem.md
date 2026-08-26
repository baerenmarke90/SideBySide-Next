
# StoryMemoryItem


## Properties

Name | Type
------------ | -------------
`effectiveDate` | Date
`kind` | string
`memory` | [MemorySummary](MemorySummary.md)

## Example

```typescript
import type { StoryMemoryItem } from ''

// TODO: Update the object below with actual values
const example = {
  "effectiveDate": null,
  "kind": null,
  "memory": null,
} satisfies StoryMemoryItem

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as StoryMemoryItem
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


