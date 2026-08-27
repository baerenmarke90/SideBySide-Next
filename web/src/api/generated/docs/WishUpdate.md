
# WishUpdate

Die Titelkorrektur.  Es gibt bewusst kein `status`-Feld. Der Wish-Status folgt ausschliesslich dem Wish->Plan-Vertrag (M3-D02/D03/D04); ein freier Status-PATCH waere der Weg, an ihm vorbeizukommen.

## Properties

Name | Type
------------ | -------------
`title` | string

## Example

```typescript
import type { WishUpdate } from ''

// TODO: Update the object below with actual values
const example = {
  "title": null,
} satisfies WishUpdate

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as WishUpdate
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


