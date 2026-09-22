# bundles/

A bundle groups several commercial [packs](../packs/) sold together on SkillzForest, at a combined price or as a themed offer.

```text
Conceptual example — Digital Agency Bundle
├── Sales & Presales
├── Development & Engineering
└── Project Management
```

A bundle never duplicates pack or skill content — it only references pack IDs, the same way a pack only references skill names.

No bundle is defined yet: the packs above aren't mature enough to combine. Once the first bundle is needed, it will follow the same manifest pattern as `packs/*/pack.json` (an id, a name, a publisher, a version, and a list of pack references) rather than inventing a new format ad hoc.
