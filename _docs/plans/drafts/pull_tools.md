## I want to build out a new version of `fetchcmds` called `fetchall`
## Do not remove `fetchcmds`, just use it as a reference for building `fetchall`

## `fetchall` needs to do the following using github cli to fetch from collect github repository:

- fetch `movetools`
- fetch all scripts from `/tools/*`
- fetch all *.md files from .claude/commands, just like `fetchcmds` does
- fetch all the *.md files from `/guides/*`
- if any of the directories don't exist then create them
