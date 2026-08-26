
# PlanUpdate

Fachliche Korrektur ohne Statuswirkung.  `status`, `plannedStart` und `plannedEnd` sind hier nicht vorgesehen - sie gehoeren den Lifecycle-Operationen. `experiencedOn` ist die eine Ausnahme: es darf auf einem abgeschlossenen Plan korrigiert werden, ohne dass daraus eine Rueckoeffnung wird (M3-D04).

## Properties

Name | Type
------------ | -------------
`description` | string
`experiencedOn` | Date
`title` | string

## Example

```typescript
import type { PlanUpdate } from ''

// TODO: Update the object below with actual values
const example = {
  "description": null,
  "experiencedOn": null,
  "title": null,
} satisfies PlanUpdate

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as PlanUpdate
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


