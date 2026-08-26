
# TokenView


## Properties

Name | Type
------------ | -------------
`accessExpiresAt` | Date
`accessToken` | string
`refreshExpiresAt` | Date
`refreshToken` | string

## Example

```typescript
import type { TokenView } from ''

// TODO: Update the object below with actual values
const example = {
  "accessExpiresAt": null,
  "accessToken": null,
  "refreshExpiresAt": null,
  "refreshToken": null,
} satisfies TokenView

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as TokenView
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


