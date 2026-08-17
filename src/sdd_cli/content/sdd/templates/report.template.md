<!-- STAGE REPORT — produced by sdd-close.
     Becomes input context for the next stage. Must stand alone.
     No "done" claim without verification (see section 2).
     Write the content in the project language (Settings > Language). -->

# Report — Stage NNN: [slug]

- **Started:** [date] · **Closed:** [date]
  <!-- Always record both dates, even with estimation off: this is what makes
       schedule metrics reconstructible if the feature is enabled later. -->
- **Spec:** `spec.md` · **Final status:** done

---

## 1. What was delivered

[Summary of the stage outcome.]

## 2. Ground-truth verification

> Every claimed artifact plus how its existence was confirmed. Without this,
> a claim is a divergence, not a conclusion.

| Claimed artifact | How it was verified | OK? |
|------------------|---------------------|-----|
| [migration/function/deploy/file] | [check on disk / live system] | yes |

## 3. Artifacts created/changed

> Real names, so the next stage can reference them without guessing.

- [file/module/contract] — [role/format]

## 4. Acceptance criteria vs evidence

- [x] [criterion] — *evidence:* [...]

## 5. Local decisions made during implementation

- [choices the next stage needs to know about]

## 6. What this stage exposes to the future

- [APIs, data, extension points]

## 7. Divergences from the spec

> What turned out different and why. (If none, write "none".)

- [...]

## 8. Known debt

> Deliberately deferred work, with the reason. (If none, write "none".)

- [...]
