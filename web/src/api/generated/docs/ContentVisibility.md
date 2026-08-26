
# ContentVisibility

Die fachliche Sichtbarkeit aus Abschnitt 15 der Spezifikation.  Der Request nennt sie, nicht die Privacy-Klasse: `privacyClass` ist eine serverseitige Ableitung und kein Feld, das ein Client setzen kann.  Sie steht hier und nicht in einer Domaene, weil sie keiner gehoert: RelatedPerson, ImportantDate und HeartMoment sprechen dieselbe Sichtbarkeit. Laege sie bei der ersten Domaene, die sie brauchte, importierten alle spaeteren aus einem fremden Fachmodul.

## Properties

Name | Type
------------ | -------------

## Example

```typescript
import type { ContentVisibility } from ''

// TODO: Update the object below with actual values
const example = {
} satisfies ContentVisibility

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ContentVisibility
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


