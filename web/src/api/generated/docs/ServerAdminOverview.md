
# ServerAdminOverview

Privacy-safe operational projection for one SideBySide installation.

## Properties

Name | Type
------------ | -------------
`accountCount` | number
`accountsLast24h` | number
`accountsLast7d` | number
`activeSpaceCount` | number
`applicationStatus` | string
`buildRevision` | string
`databaseProvider` | string
`databaseStatus` | string
`demoMode` | boolean
`deployment` | string
`environment` | string
`jobsFailed` | number
`jobsPending` | number
`jobsRunning` | number
`lastSuccessfulJobAt` | Date
`mailTransport` | string
`mediaObjectCount` | number
`mediaStatus` | string
`mediaStore` | string
`mediaStoredBytes` | number
`oidcConnectionCount` | number
`processStartedAt` | Date
`publicBaseUrl` | string
`recentFailedJobs` | [Array&lt;ServerAdminFailedJob&gt;](ServerAdminFailedJob.md)
`workerStatus` | string

## Example

```typescript
import type { ServerAdminOverview } from ''

// TODO: Update the object below with actual values
const example = {
  "accountCount": null,
  "accountsLast24h": null,
  "accountsLast7d": null,
  "activeSpaceCount": null,
  "applicationStatus": null,
  "buildRevision": null,
  "databaseProvider": null,
  "databaseStatus": null,
  "demoMode": null,
  "deployment": null,
  "environment": null,
  "jobsFailed": null,
  "jobsPending": null,
  "jobsRunning": null,
  "lastSuccessfulJobAt": null,
  "mailTransport": null,
  "mediaObjectCount": null,
  "mediaStatus": null,
  "mediaStore": null,
  "mediaStoredBytes": null,
  "oidcConnectionCount": null,
  "processStartedAt": null,
  "publicBaseUrl": null,
  "recentFailedJobs": null,
  "workerStatus": null,
} satisfies ServerAdminOverview

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ServerAdminOverview
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


