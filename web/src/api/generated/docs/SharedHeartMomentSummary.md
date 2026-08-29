
# SharedHeartMomentSummary

A shared heart moment. There is deliberately no private variant.

## Properties

Name | Type
------------ | -------------
`attachment` | [AttachmentSummary](AttachmentSummary.md)
`author` | [AuthorSummary](AuthorSummary.md)
`capabilities` | [ResourceCapabilities](ResourceCapabilities.md)
`createdAt` | Date
`emotion` | [HeartEmotion](HeartEmotion.md)
`happenedOn` | Date
`id` | string
`text` | string

## Example

```typescript
import type { SharedHeartMomentSummary } from ''

// TODO: Update the object below with actual values
const example = {
  "attachment": null,
  "author": null,
  "capabilities": null,
  "createdAt": null,
  "emotion": null,
  "happenedOn": null,
  "id": null,
  "text": null,
} satisfies SharedHeartMomentSummary

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as SharedHeartMomentSummary
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


