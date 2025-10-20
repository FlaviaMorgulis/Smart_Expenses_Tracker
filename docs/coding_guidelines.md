# Coding Guidelines

This document defines the basic rules and standards for coding, committing, and collaborating in the **Smart Expenses Tracker** project.

---

## Folder Structure
Keep the main folders organized as follows:

```text
Smart_Expenses_Tracker/
│
├── backend/
├── frontend/
├── database/
└── docs/
```

## <Type>: <Short description>

| Type      | Meaning                                                  |
|-----------|----------------------------------------------------------|
| Add       | Something new is being added                             |
| Fix       | A bug or error is being fixed                             |
| Update    | An existing file is being updated                        |
| Docs      | Changes related only to documentation                    |
| Refactor  | Code structure is being changed, but functionality stays the same |
| Style     | Formatting or appearance adjustments                     |


- Keep messages short, clear, and in **English**.  
- Each commit should represent one logical change.

---

## Code Style
### Python
- Follow **PEP8** conventions.  
- Use meaningful variable and function names.  
- Comment when logic is not obvious.  
- Keep lines under **80 characters** when possible.

### HTML / CSS / JS
- Use consistent indentation (2 or 4 spaces).  
- Group related styles and scripts together.  
- Add comments for important elements.  
- Keep code readable and modular.

---

## Pull Requests (PR)
1. Always open a PR when merging into `main`.  
2. Add a clear title and short description.  
3. Reference the related issue (e.g. `Closes #8`).  
4. Wait for at least one review from a teammate before merging.  

---

## Testing & Review
- Test your code locally before pushing.  
- Do not push broken or incomplete code to `main`.  
- Use meaningful test data (not “test1”, “abc”, etc.).  

---

## Team Collaboration
- Communicate changes on GitHub or group chat.  
- Respect commit and branch rules.  
- Write code that others can easily understand.  

---

**Goal:** Clean, consistent, and collaborative codebase.
