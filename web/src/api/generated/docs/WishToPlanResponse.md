
# WishToPlanResponse

Beide Ressourcen in einer Antwort.  Die Konvertierung veraendert den Wish und erzeugt den Plan. Ein Client, der nur eines von beidem zurueckbekaeme, muesste das andere sofort nachladen - und haette bis dahin einen veralteten Stand angezeigt.

## Properties

Name | Type
------------ | -------------
`plan` | [PlanDetail](PlanDetail.md)
`wish` | [WishDetail](WishDetail.md)

## Example

```typescript
import type { WishToPlanResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "plan": null,
  "wish": null,
} satisfies WishToPlanResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as WishToPlanResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


