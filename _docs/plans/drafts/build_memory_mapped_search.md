# Plan: Build Memory-Mapped Ripgrep-Style Search Tool

## Overview
Implement a high-performance code search tool that leverages memory-mapped files for zero-copy searching with ripgrep-style features, optimized for Apple Silicon and large memory systems.

## Architecture Design

### Core Components
1. **FileMapper**: Memory map management system
2. **SearchEngine**: Pattern matching and search algorithms  
3. **QueryParser**: Handle ripgrep-style patterns and flags
4. **ResultFormatter**: Output formatting with context lines
5. **FileFilter**: Gitignore and file type filtering

## Implementation Steps

### Phase 1: Core Memory Mapping Infrastructure

#### 1. Enhanced FileMapper System
```go
package mmsearch

import (
    "sync"
    "syscall"
    "path/filepath"
)

type Repository struct {
    mu          sync.RWMutex
    mappedFiles map[string]*MappedFile
    indexStats  IndexStats
    fileTypes   map[string][]string // Extension to file paths mapping
}

type MappedFile struct {
    Path     string
    Data     []byte
    Size     int64
    LineEnds []int32 // Precomputed line endings for fast line number lookup
    file     *os.File
}

type IndexStats struct {
    TotalFiles   int
    TotalSize    int64
    IndexTime    time.Duration
}

func (r *Repository) IndexDirectory(root string, opts IndexOptions) error {
    // Walk directory tree
    // Apply .gitignore rules
    // Memory map each file
    // Precompute line endings
    return nil
}
```

#### 2. Precompute Line Information
```go
func (mf *MappedFile) computeLineEndings() {
    mf.LineEnds = make([]int32, 0, mf.Size/80) // Preallocate assuming ~80 chars per line
    for i, b := range mf.Data {
        if b == '\n' {
            mf.LineEnds = append(mf.LineEnds, int32(i))
        }
    }
}

func (mf *MappedFile) GetLine(lineNum int) ([]byte, int, int) {
    // Return line content with start/end positions
    start := 0
    if lineNum > 0 && lineNum <= len(mf.LineEnds) {
        start = int(mf.LineEnds[lineNum-1]) + 1
    }
    end := len(mf.Data)
    if lineNum < len(mf.LineEnds) {
        end = int(mf.LineEnds[lineNum])
    }
    return mf.Data[start:end], start, end
}
```

### Phase 2: Search Engine Core

#### 3. Standard Library Pattern Matching
```go
type SearchEngine struct {
    repo *Repository
}

// Boyer-Moore implementation using standard library only
func (se *SearchEngine) boyerMooreSearch(data []byte, pattern []byte) []Match {
    if len(pattern) == 0 || len(data) < len(pattern) {
        return nil
    }
    
    // Build bad character table
    badChar := make([]int, 256)
    for i := range badChar {
        badChar[i] = len(pattern)
    }
    for i := 0; i < len(pattern)-1; i++ {
        badChar[pattern[i]] = len(pattern) - 1 - i
    }
    
    var matches []Match
    i := len(pattern) - 1
    
    for i < len(data) {
        j := len(pattern) - 1
        k := i
        
        for j >= 0 && data[k] == pattern[j] {
            j--
            k--
        }
        
        if j < 0 {
            // Match found
            matches = append(matches, Match{
                Start: k + 1,
                End:   k + 1 + len(pattern),
            })
            i += len(pattern)
        } else {
            i += badChar[data[k]]
        }
    }
    return matches
}

// Regex support using standard library
func (se *SearchEngine) regexSearch(data []byte, pattern *regexp.Regexp) []Match {
    allMatches := pattern.FindAllIndex(data, -1)
    matches := make([]Match, len(allMatches))
    for i, m := range allMatches {
        matches[i] = Match{Start: m[0], End: m[1]}
    }
    return matches
}
```

#### 4. Parallel Search Implementation
```go
func (se *SearchEngine) Search(query Query) *SearchResults {
    results := &SearchResults{
        Query: query,
        Files: make([]FileResult, 0),
    }
    
    // Use worker pool for parallel searching
    numWorkers := runtime.NumCPU()
    jobs := make(chan *MappedFile, len(se.repo.mappedFiles))
    resultsChan := make(chan FileResult, len(se.repo.mappedFiles))
    
    var wg sync.WaitGroup
    
    // Start workers
    for w := 0; w < numWorkers; w++ {
        wg.Add(1)
        go se.searchWorker(&wg, jobs, resultsChan, query)
    }
    
    // Queue files
    for _, mf := range se.repo.mappedFiles {
        jobs <- mf
    }
    close(jobs)
    
    // Collect results
    go func() {
        wg.Wait()
        close(resultsChan)
    }()
    
    for result := range resultsChan {
        if len(result.Matches) > 0 {
            results.Files = append(results.Files, result)
        }
    }
    
    return results
}
```

### Phase 3: Ripgrep-Style Features

#### 5. Query Parser and Options
```go
type Query struct {
    Pattern        string
    Regex         *regexp.Regexp
    CaseSensitive bool
    WholeWord     bool
    Invert        bool
    FileTypes     []string
    Exclude       []string
    BeforeContext int
    AfterContext  int
}

func ParseQuery(args []string) (*Query, error) {
    // Parse command line flags ripgrep-style
    // Support: -i (ignore case), -w (word boundary), -v (invert)
    // -A (after context), -B (before context), -C (context)
    // -t (type), --exclude
    return nil, nil
}
```

#### 6. Context Line Support
```go
type MatchWithContext struct {
    Match
    LineBefore [][]byte
    LineAfter  [][]byte
    LineNumber int
}

func (mf *MappedFile) GetMatchContext(match Match, before, after int) MatchWithContext {
    lineNum := mf.GetLineNumber(match.Start)
    result := MatchWithContext{
        Match:      match,
        LineNumber: lineNum,
    }
    
    // Get before context
    for i := lineNum - before; i < lineNum && i >= 0; i++ {
        line, _, _ := mf.GetLine(i)
        result.LineBefore = append(result.LineBefore, line)
    }
    
    // Get after context  
    for i := lineNum + 1; i <= lineNum+after && i < len(mf.LineEnds); i++ {
        line, _, _ := mf.GetLine(i)
        result.LineAfter = append(result.LineAfter, line)
    }
    
    return result
}
```

### Phase 4: File Filtering

#### 7. Gitignore and Type Filtering
```go
type FileFilter struct {
    gitignoreRules []IgnoreRule
    typeExtensions map[string][]string // e.g., "go" -> [".go"]
}

func (ff *FileFilter) ShouldIndex(path string) bool {
    // Check gitignore rules
    for _, rule := range ff.gitignoreRules {
        if rule.Matches(path) {
            return false
        }
    }
    
    // Check file type filters if specified
    if len(ff.typeExtensions) > 0 {
        ext := filepath.Ext(path)
        // Check if extension matches any requested type
    }
    
    return true
}

// Simple gitignore parser
func ParseGitignore(content []byte) []IgnoreRule {
    lines := bytes.Split(content, []byte{'\n'})
    var rules []IgnoreRule
    for _, line := range lines {
        line = bytes.TrimSpace(line)
        if len(line) == 0 || line[0] == '#' {
            continue
        }
        rules = append(rules, NewIgnoreRule(string(line)))
    }
    return rules
}
```

### Phase 5: Output Formatting

#### 8. Result Formatter
```go
type OutputFormatter struct {
    UseColor    bool
    ShowLineNum bool
    GroupByFile bool
}

func (of *OutputFormatter) Format(results *SearchResults) string {
    var buf bytes.Buffer
    
    for _, file := range results.Files {
        if of.GroupByFile {
            buf.WriteString(file.Path)
            buf.WriteString("\n")
        }
        
        for _, match := range file.Matches {
            if !of.GroupByFile {
                buf.WriteString(file.Path)
                buf.WriteString(":")
            }
            
            if of.ShowLineNum {
                fmt.Fprintf(&buf, "%d:", match.LineNumber)
            }
            
            // Format match with optional color highlighting
            if of.UseColor {
                of.writeColorMatch(&buf, match)
            } else {
                buf.Write(match.LineContent)
            }
            buf.WriteString("\n")
        }
    }
    
    return buf.String()
}
```

## Alternative Library Options

### Second Option: Using Specialized Libraries

1. **String Search Libraries**
   - `github.com/cloudflare/ahocorasick` - Multi-pattern matching
   - `github.com/blevesearch/vellum` - FST-based searching
   - `github.com/golang/go/src/index/suffixarray` - Suffix array for advanced searching

2. **Memory Mapping Libraries**
   - `github.com/edsrzf/mmap-go` - Cross-platform mmap wrapper
   - `golang.org/x/exp/mmap` - Official experimental mmap

3. **Regex Optimization**
   - `github.com/moby/buildkit/frontend/dockerfile/parser` - Fast pattern matching
   - `github.com/intel/hyperscan-go` - Intel Hyperscan bindings (requires CGO)

4. **File Walking**
   - `github.com/charlievieth/fastwalk` - Faster alternative to filepath.Walk
   - `github.com/karrick/godirwalk` - Optimized directory traversal

## Performance Optimizations

### SIMD Acceleration (Platform Specific)
```go
// For Apple Silicon (ARM NEON)
// Would require CGO or assembly
func simdSearch_arm64(data []byte, pattern []byte) []Match {
    // Implement using ARM NEON instructions
    // Fallback to Boyer-Moore for unsupported platforms
}
```

### Benchmark Suite
```go
func BenchmarkSearchMethods(b *testing.B) {
    repo := setupTestRepo()
    patterns := []string{
        "TODO",           // Common literal
        "func \\w+\\(",   // Regex pattern
        "import",         // Frequent word
    }
    
    for _, pattern := range patterns {
        b.Run(pattern, func(b *testing.B) {
            for i := 0; i < b.N; i++ {
                repo.Search(Query{Pattern: pattern})
            }
        })
    }
}
```

## Testing Strategy

1. **Unit Tests**: Test each component independently
2. **Integration Tests**: Test full search pipeline
3. **Performance Tests**: Compare with ripgrep on same datasets
4. **Memory Tests**: Verify proper cleanup and no leaks
5. **Stress Tests**: Large repositories (100GB+)

## CLI Interface

```bash
# Basic usage
mmsearch "pattern" /path/to/repo

# Ripgrep-compatible flags
mmsearch -i "todo" .                    # Case insensitive
mmsearch -w "main" .                    # Whole word
mmsearch -t go "func main" .            # Type filter
mmsearch -A 2 -B 2 "error" .            # Context lines
mmsearch --exclude "*.test.go" "TODO" . # Exclude patterns
```

## Expected Performance

With 128GB RAM and Apple M4 Max:
- **Index time**: ~1-2 seconds per GB of source code
- **Search latency**: <50ms for literal patterns
- **Memory usage**: ~1.1x repository size (includes line index)
- **Throughput**: 10-20 GB/s for literal searches

## Next Steps

1. Implement Phase 1 (Core Infrastructure)
2. Benchmark against ripgrep baseline
3. Add Phase 2 (Search algorithms)
4. Implement remaining phases iteratively
5. Package as standalone binary