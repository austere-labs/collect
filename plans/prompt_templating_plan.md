# Prompt Templating Implementation Plan

## Overview
Build a comprehensive prompt templating system that leverages Anthropic's experimental prompt tools API to create, improve, and templatize prompts with variable substitution support.

## Key Components

### 1. Data Models (models/prompt_template.py)
- **PromptTemplate**: Core template model with UUID, version, name, content, variables, metadata
- **PromptVariable**: Variable definition with name, description, type, default value
- **TemplateResponse**: Response model for template operations

### 2. MCP Tools in collect.py

#### a. template_prompt Tool
- Converts existing prompts into reusable templates using Anthropic's templatize_prompt API
- Extracts variables and creates template placeholders
- Returns template with variable mappings

#### b. improve_prompt Tool  
- Enhances prompt quality using Anthropic's improve_prompt API
- Optimizes for clarity, structure, and effectiveness
- Supports system prompts and assistant prefills

#### c. list_prompt_templates Tool
- Lists all saved templates from database
- Filters by active status, version, metadata
- Returns template summaries

#### d. get_prompt_template Tool
- Retrieves specific template by name or UUID
- Supports version selection
- Returns full template with variables

#### e. fill_prompt_template Tool
- Populates template variables with actual values
- Validates variable types and requirements
- Returns ready-to-use prompt

### 3. Repository Layer (repository/prompt_template_service.py)
- Extends existing PromptService for template-specific operations
- Methods: save_template, get_template, list_templates, fill_template
- Handles versioning and variable management

### 4. Database Schema (migrations/)
- New prompt_templates table with template-specific fields
- prompt_template_variables table for variable definitions
- Maintains relationship with existing prompts table

### 5. Integration Points
- Leverage existing AnthropicMCP methods (generate_prompt, improve_prompt, templatize_prompt)
- Reuse existing database infrastructure
- Integrate with current prompt management system

## Implementation Steps

1. Create Pydantic models for template data structures
2. Add template_prompt MCP tool using templatize_prompt API
3. Add improve_prompt MCP tool for prompt enhancement
4. Extend repository with template management methods
5. Create database migrations for template storage
6. Implement template listing and retrieval tools
7. Build fill_prompt_template for variable substitution
8. Write comprehensive tests for all functionality
9. Update documentation with usage examples

## Example Usage

```python
# Create a template from existing prompt
template = await template_prompt(
    prompt="Translate {{TEXT}} from {{SOURCE_LANG}} to {{TARGET_LANG}}",
    name="translation_template"
)

# List available templates
templates = await list_prompt_templates()

# Fill template with values
filled = await fill_prompt_template(
    name="translation_template",
    variables={
        "TEXT": "Hello world",
        "SOURCE_LANG": "English", 
        "TARGET_LANG": "Spanish"
    }
)
```

## Todo List

1. Research and analyze existing prompt API methods (generate_prompt, improve_prompt, templatize_prompt) in anthropic_mcp.py
2. Design prompt template data model with variables, placeholders, and metadata support
3. Create PromptTemplate and PromptVariable Pydantic models for template structure
4. Implement template_prompt MCP tool that uses Anthropic's templatize_prompt API
5. Implement improve_prompt MCP tool that enhances existing prompts
6. Create prompt template repository methods for saving/loading templates
7. Add database migrations for prompt templates table with variables support
8. Implement list_prompt_templates MCP tool to view saved templates
9. Implement get_prompt_template MCP tool to retrieve specific templates
10. Implement fill_prompt_template MCP tool to populate template variables
11. Create comprehensive tests for all prompt templating functionality
12. Update CLAUDE.md documentation with prompt templating examples

This implementation will provide a robust prompt templating system that integrates seamlessly with the existing codebase while leveraging Anthropic's advanced prompt engineering capabilities.