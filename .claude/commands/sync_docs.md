Automate documentation synchronization using gemini CLI and source analysis.

WORKFLOW INSTRUCTIONS:
1. Use gemini CLI to analyze source.md (548KB XML project source) 
2. Use gemini CLI to generate updated GEMINI.md from source analysis
3. AFTER gemini completes, compare GEMINI.md and CLAUDE.md
4. Create and propose new version of CLAUDE.md with aligned changes
5. Present proposed changes for user approval

SEQUENTIAL STEPS:
Step 1: Tool Call - Gemini CLI Source Analysis
- Execute: `gemini --prompt "Please read the file 'source.md' in the current working directory and analyze this complete source code XML file. Understand the project structure, technologies, conventions, key files, and architecture. Focus on identifying: 1) Main entry points and core files, 2) Key technologies and frameworks used, 3) Development commands and workflows, 4) Database structure and migrations, 5) Testing approaches, 6) Directory organization and purpose of each major component."`

Step 2: Tool Call - Generate Updated GEMINI.md
- Execute: `gemini --prompt "Please read the file 'source.md' in the current working directory. Based on your analysis of this source code XML file, create a comprehensive new version of GEMINI.md that accurately reflects the current project. Include: 1) Project overview and purpose, 2) Complete technology stack, 3) Building and running instructions, 4) Development conventions, 5) Key files with descriptions, 6) Architecture details. Format as markdown suitable for Gemini Code Assistant context. Please write this updated content to the GEMINI.md file."`

Step 3: Documentation Comparison
- Read current @CLAUDE.md file
- Read updated @GEMINI.md file  
- Analyze differences and alignment opportunities

Step 4: Propose CLAUDE.md Updates
- Generate proposed changes to CLAUDE.md based on GEMINI.md insights
- Identify missing sections, outdated information, or improvements needed
- Present comprehensive change proposal with specific edits

IMPORTANT RESTRICTIONS:
- DO NOT make any file edits until all analysis is complete
- DO NOT run any commands except gemini CLI calls
- ONLY propose changes after completing full comparison
- Follow the sequential workflow exactly as specified
- Wait for user approval before implementing any changes
- Ensure gemini CLI has completely finished before proceeding to next step
