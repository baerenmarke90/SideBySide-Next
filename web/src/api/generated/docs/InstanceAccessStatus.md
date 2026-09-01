
# InstanceAccessStatus


## Properties

Name | Type
------------ | -------------
`maintenanceMode` | boolean
`registrationAvailable` | boolean
`registrationUnavailableReason` | string

## Example

```typescript
import type { InstanceAccessStatus } from ''

// TODO: Update the object below with actual values
const example = {
  "maintenanceMode": null,
  "registrationAvailable": null,
  "registrationUnavailableReason": null,
} satisfies InstanceAccessStatus

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as InstanceAccessStatus
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


