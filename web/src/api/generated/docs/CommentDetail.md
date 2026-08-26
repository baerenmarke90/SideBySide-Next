
# CommentDetail


## Properties

Name | Type
------------ | -------------
`author` | [AuthorSummary](AuthorSummary.md)
`authorId` | string
`body` | string
`createdAt` | Date
`id` | string
`spaceId` | string
`updatedAt` | Date
`version` | number

## Example

```typescript
import type { CommentDetail } from ''

// TODO: Update the object below with actual values
const example = {
  "author": null,
  "authorId": null,
  "body": null,
  "createdAt": null,
  "id": null,
  "spaceId": null,
  "updatedAt": null,
  "version": null,
} satisfies CommentDetail

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as CommentDetail
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


