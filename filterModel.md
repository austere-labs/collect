# Gemini Model Filtering Implementation Guide

## Overview

This document describes how to filter Gemini models by version number (2.0, 2.5, etc.) and extract input token limits from the API response.

## Current State

The `GeminiMCP.get_model_list()` method has been updated to return the full API response instead of just model names:

```python
def get_model_list(self) -> Dict:
    # ... API call logic ...
    model_data = response.json()
    return model_data  # Returns full response with all model metadata
```

## Implementation Plan

### 1. Add Filtering Methods to GeminiMCP Class

Add these methods to the `GeminiMCP` class in `models/gemini_mcp.py`:

```python
def filter_models_by_version(self, versions: list[str]) -> list[dict]:
    """
    Filter models by version numbers and include token limits.
    
    Args:
        versions: List of version strings (e.g., ['2.0', '2.5'])
    
    Returns:
        List of dicts with model info including inputTokenLimit
    """
    all_models = self.get_model_list()
    filtered_models = []
    
    for model in all_models.get('models', []):
        model_name = model['name'].split('/')[-1]
        
        # Check if model matches any requested version
        for version in versions:
            if version in model_name:
                model_info = {
                    'name': model_name,
                    'displayName': model.get('displayName', ''),
                    'inputTokenLimit': model.get('inputTokenLimit', 0),
                    'outputTokenLimit': model.get('outputTokenLimit', 0),
                    'description': model.get('description', ''),
                    'supportedGenerationMethods': model.get('supportedGenerationMethods', [])
                }
                filtered_models.append(model_info)
                break
    
    return filtered_models

def get_models_with_token_info(self) -> list[dict]:
    """
    Get all models with their token limit information.
    
    Returns:
        List of models sorted by inputTokenLimit (descending)
    """

    all_models = self.get_model_list()
    models_with_tokens = []

    for model in all_models.get('models', []):
        model_name = model['name'].split('/')[-1]
        input_limit = model.get('inputTokenLimit', 0)
        
        # Only include models with token limit info
        if input_limit > 0:
            models_with_tokens.append({
                'name': model_name,
                'inputTokenLimit': input_limit,
                'outputTokenLimit': model.get('outputTokenLimit', 0)
            })
    
    # Sort by input token limit (highest first)
    models_with_tokens.sort(key=lambda x: x['inputTokenLimit'], reverse=True)
    return models_with_tokens
```

### 2. Advanced Filtering Function (Standalone)

For more complex filtering needs, you can use this standalone function:

```python
def filter_gemini_models(models_data: dict, 
                        versions: list[str] = None,
                        min_input_tokens: int = None,
                        max_input_tokens: int = None,
                        generation_methods: list[str] = None) -> list[dict]:
    """
    Advanced filtering with multiple criteria.
    
    Args:
        models_data: Response from get_model_list()
        versions: Filter by version numbers (optional)
        min_input_tokens: Minimum inputTokenLimit (optional)
        max_input_tokens: Maximum inputTokenLimit (optional)
        generation_methods: Required generation methods (optional)
    
    Returns:
        Filtered list of model information
    """
    filtered_models = []
    
    for model in models_data.get('models', []):
        model_name = model['name'].split('/')[-1]
        input_limit = model.get('inputTokenLimit', 0)
        
        # Apply version filter
        if versions:
            if not any(ver in model_name for ver in versions):
                continue
        
        # Apply token limit filters
        if min_input_tokens and input_limit < min_input_tokens:
            continue
        if max_input_tokens and input_limit > max_input_tokens:
            continue
        
        # Apply generation method filter
        if generation_methods:
            supported_methods = model.get('supportedGenerationMethods', [])
            if not all(method in supported_methods for method in generation_methods):
                continue
        
        # Model passed all filters
        model_info = {
            'name': model_name,
            'displayName': model.get('displayName', ''),
            'inputTokenLimit': input_limit,
            'outputTokenLimit': model.get('outputTokenLimit', 0),
            'description': model.get('description', ''),
            'supportedGenerationMethods': model.get('supportedGenerationMethods', [])
        }
        filtered_models.append(model_info)
    
    return filtered_models
```

## Usage Examples

### Basic Version Filtering

```python
def test_filter_by_version(gemini_mcp):
    # Get models for versions 2.0 and 2.5
    filtered = gemini_mcp.filter_models_by_version(['2.0', '2.5'])
    
    print(f"Found {len(filtered)} models:")
    for model in filtered:
        print(f"- {model['name']}: {model['inputTokenLimit']:,} input tokens")
```

### Get Models with Token Info

```python
def test_models_with_tokens(gemini_mcp):
    models = gemini_mcp.get_models_with_token_info()
    
    print("Models by input token limit:")
    for model in models[:10]:  # Top 10 models
        print(f"- {model['name']}: {model['inputTokenLimit']:,} tokens")
```

### Advanced Filtering

```python
def test_advanced_filtering(gemini_mcp):
    all_models = gemini_mcp.get_model_list()
    
    # Find 2.5 models with at least 100k input tokens
    filtered = filter_gemini_models(
        all_models,
        versions=['2.5'],
        min_input_tokens=100000,
        generation_methods=['generateContent']
    )
    
    print("High-capacity 2.5 models:")
    for model in filtered:
        print(f"- {model['name']}")
        print(f"  Input limit: {model['inputTokenLimit']:,}")
        print(f"  Output limit: {model['outputTokenLimit']:,}")
```

### Grouping Models by Version

```python
def group_models_by_version(gemini_mcp):
    from collections import defaultdict
    
    all_models = gemini_mcp.get_model_list()
    version_groups = defaultdict(list)
    
    for model in all_models.get('models', []):
        model_name = model['name'].split('/')[-1]
        
        # Extract version pattern
        if '2.5' in model_name:
            version = '2.5'
        elif '2.0' in model_name:
            version = '2.0'
        elif '1.5' in model_name:
            version = '1.5'
        elif '1.0' in model_name:
            version = '1.0'
        else:
            version = 'other'
        
        version_groups[version].append({
            'name': model_name,
            'inputTokenLimit': model.get('inputTokenLimit', 0)
        })
    
    # Display grouped results
    for version, models in sorted(version_groups.items()):
        print(f"\nVersion {version} ({len(models)} models):")
        for model in sorted(models, key=lambda x: x['inputTokenLimit'], reverse=True)[:3]:
            print(f"  - {model['name']}: {model['inputTokenLimit']:,} tokens")
```

## Expected Output Format

When filtering models, you'll get results like:

```
Found 15 models:
- gemini-2.5-pro: 2,000,000 input tokens
- gemini-2.5-flash: 1,000,000 input tokens
- gemini-2.5-flash-preview-05-20: 1,000,000 input tokens
- gemini-2.0-flash: 32,768 input tokens
- gemini-2.0-flash-exp: 32,768 input tokens
- gemini-2.0-pro-exp: 32,768 input tokens
```

## API Response Structure

The Gemini API returns model data in this format:

```json
{
  "models": [
    {
      "name": "models/gemini-2.5-flash",
      "displayName": "Gemini 2.5 Flash",
      "description": "Fast and versatile multimodal model",
      "inputTokenLimit": 1000000,
      "outputTokenLimit": 8192,
      "supportedGenerationMethods": [
        "generateContent",
        "countTokens"
      ]
    }
    // ... more models
  ]
}
```

## Testing the Implementation

Add this test to `models/test_gemini_mcp.py`:

```python
def test_filter_models_by_version(gemini_mcp):
    # Test filtering for 2.0 and 2.5 versions
    filtered = gemini_mcp.filter_models_by_version(['2.0', '2.5'])
    
    assert len(filtered) > 0
    assert all('2.0' in m['name'] or '2.5' in m['name'] for m in filtered)
    assert all('inputTokenLimit' in m for m in filtered)
    
    # Print results for verification
    print(f"\nFound {len(filtered)} models for versions 2.0 and 2.5:")
    for model in sorted(filtered, key=lambda x: x['inputTokenLimit'], reverse=True):
        print(f"  {model['name']}: {model['inputTokenLimit']:,} tokens")
```

## Notes

1. **Token Limits**: Not all models return `inputTokenLimit`. Handle missing values gracefully.
2. **Model Names**: The API returns full names like "models/gemini-2.5-flash". We extract just the model part.
3. **Sorting**: Consider sorting results by token limit, name, or version for consistent output.
4. **Caching**: For production use, consider caching the model list as it doesn't change frequently.
