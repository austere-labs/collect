<title># Ultra Diff Review</title>

<purpose>
We want to conduct a thorough comprehensive code review using the appropriate diff approach.
Given the following instructions, execute each task in the order given.
Within each task, execute each instruction in order.
</purpose>

<instructions>
    <task>## Task 1: Create diff.md</task>
        <instruction>Create a new file called diff.md in the root of the project</instruction>
        <instruction>At the top of the file, add the following markdown:

        ```md
        # Code Review:  
        - Review the diff, report on issues, bugs and improvements.  
        - End with a concise markdown table of any issues found, their solutions and a risk
        assessment for each issue if applicable
        - Use emojis to convey the severity of each issue
        
        ## Diff

        ```
    <task>## Task 2: git diff and append</task>
        <instruction>Run the following command and make sure there is a result:
        ```bash
        git diff --staged
        ```
        </instruction>
        <instruction>IF there is a result: Run the following command to get the diff 
        and append it to the diff.md file:

        ```bash
        git diff --staged >> diff.md
        ```
        </instruction>
</instructions>
