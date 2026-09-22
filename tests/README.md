# tests/

Reserved for automated tests covering skill/pack/runtime validation and distribution builds (e.g. asserting `scripts/build-pack.js` produces a `dist/packs/<pack>/<runtime>/` containing exactly the skills listed in a given `pack.json`, or that `scripts/build-skill.js` skips every runtime marked `unknown`).

Nothing is implemented yet — `npm run validate` (see [`scripts/validate.js`](../scripts/validate.js)) covers the structural checks needed today. Add a real test runner here once the validation logic outgrows what a single script can reasonably assert.
