---
argument-hint: [instructions]
description: A Claude Code command that restricts Claude to working only with user-provided context, preventing automatic file reading or web searches unless explicitly requested.
model: opus
---

# Focus only on the data I have provided you.
# I want to collaborate to build a plan with the data I have already provided.

## IMPORTANT INSTRUCTONS:  
- Do not read additional files unless I ask you to. 
- Do not search the web for additional information unless I ask you to. 
- I have already provided the context for the problem I am asking to help me with

Please read the {instructions} I have provided and only use the context provided ahead of time to collaborate with me on an approach or set of possible approaches.
