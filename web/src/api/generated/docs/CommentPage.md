
# CommentPage


## Properties

Name | Type
------------ | -------------
`hasMore` | boolean
`items` | [Array&lt;CommentDetail&gt;](CommentDetail.md)
`nextCursor` | string

## Example

```typescript
import type { CommentPage } from ''

// TODO: Update the object below with actual values
const example = {
  "hasMore": null,
  "items": null,
  "nextCursor": null,
} satisfies CommentPage

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as CommentPage
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


