
# PasskeyAuthenticationRequest


## Properties

Name | Type
------------ | -------------
`credential` | { [key: string]: any; }
`deviceName` | string
`platform` | string

## Example

```typescript
import type { PasskeyAuthenticationRequest } from ''

// TODO: Update the object below with actual values
const example = {
  "credential": null,
  "deviceName": null,
  "platform": null,
} satisfies PasskeyAuthenticationRequest

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as PasskeyAuthenticationRequest
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


