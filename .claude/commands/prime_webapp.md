<purpose>
Prime the context window with the area of the project that we want the model to focus on and understand.	
</purpose>

<instructions>
	<instruction>Read the README.md in this directory {{directory}}</instruction>
	<instruction>Read the Claude.md in this directory {{directory}}</instruction>
	<instruction>THEN: run git ls-files from this directory {{directory}} to understand the context of the project</instruction>
	<instruction>THEN: Please focus on the content provided in the content variable</instruction>
</instructions>

<content>
{{content}}
</content>
