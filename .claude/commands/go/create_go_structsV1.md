# Create Golang structs from API documentation for requests and responses

## There are two phases to the work we need to do:  
* Phase 1: we will call the provided URL using the `get_docs` tool
* Phase 2: we will use the data that is extracted from the `get_docs` process and build golang structs from the json response that is returned from the Phase 1 process.

<Phase 1>
* Read the provided documentation, surface the endpoint name

```
Use the get_docs tool with:
- url: $ARGUMENTS[0] (The URL of the documentation page)
- extract_value: $ARGUMENTS[1] (The specific section/function/topic to extract)

Example: get_docs($ARGUMENTS[0], $ARGUMENTS[1])
```

## What it does

This tool:
1. Fetches content from the specified URL
2. Uses Gemini 2.5 Flash Preview to intelligently extract documentation for the requested section
3. Returns the relevant documentation as clean, readable text

## Best for

- API documentation extraction
- Function/method documentation
- Specific topic documentation from larger pages
- Technical documentation that needs focused extraction

## Command Template

When called, this will execute:
```
get_docs($ARGUMENTS[0], $ARGUMENTS[1])
```
Example usage for getting the json response from a url: 
```
get_docs("https://developer.tastytrade.com/api-guides/customer-account-info/",
"the exact json response for getting customer accounts")
```

<Phase 2>

# JSON to Golang Struct Generator

## After extracting the json structur, I'll automatically:
1. Identify all objects in the JSON
2. Determine appropriate Golang types for each field
3. Create properly formatted structs with JSON tags
4. Handle nested objects and arrays properly and idiomatically per best practice in Golang
5. Follow Go naming conventions
6. Add helpful comments
7. Ensure that if there are potential null values in the JSON (per the documentation) that we appropriately handle those with Golang pointers