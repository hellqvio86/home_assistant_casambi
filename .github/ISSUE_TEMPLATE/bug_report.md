---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

**Describe the bug**

A clear and concise description of what the bug is.

**To Reproduce**

Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**

A clear and concise description of what you expected to happen.

**Debug logs**

Provide debug logs for integration and aiocasambi in plain text, remove credentials. Enable them through *configuration.yaml* e.g:

```
logger:
  default: info
  logs:
    homeassistant.components.casambi: debug
    custom_components.casambi: debug
    aiocasambi: debug
```

**Screenshots**

If applicable, add screenshots to help explain your problem.

**Platform information (please complete the following information):**

 - OS: [e.g. iOS]
 - Home assistant version [e.g. chrome, safari]

**Additional context**

Add any other context about the problem here.
