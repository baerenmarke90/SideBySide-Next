
# WishStatus

Der Statusautomat aus M3-D02/D03/D04.  Vollstaendig aufgefuehrt, aber in M3-S1 erreicht ein Wish nur `OPEN`: die beiden anderen Zustaende entstehen ausschliesslich aus dem noch nicht gebauten Wish->Plan-Vertrag. Die Werte stehen trotzdem schon in Modell und Datenbank, damit der spaetere Slice keine Statusmigration ueber bestehende Zeilen fahren muss.

## Properties

Name | Type
------------ | -------------

## Example

```typescript
import type { WishStatus } from ''

// TODO: Update the object below with actual values
const example = {
} satisfies WishStatus

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as WishStatus
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


