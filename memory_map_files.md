# Memory Mapped Files in Go

Here's a comprehensive Go example using the syscall package to memory map all files in a directory:

```go
package main

import (
    "fmt"
    "io/fs"
    "log"
    "os"
    "path/filepath"
    "syscall"
    "unsafe"
)

// MappedFile represents a memory-mapped file
type MappedFile struct {
    Path string
    Data []byte
    Size int64
    file *os.File
}

// Close unmaps the file and closes the file handle
func (mf *MappedFile) Close() error {
    if len(mf.Data) > 0 {
        if err := syscall.Munmap(mf.Data); err != nil {
            return fmt.Errorf("failed to unmap %s: %w", mf.Path, err)
        }
    }
    if mf.file != nil {
        return mf.file.Close()
    }
    return nil
}

// FileMapper manages multiple memory-mapped files
type FileMapper struct {
    mappedFiles []*MappedFile
}

// MapDirectory maps all regular files in the specified directory
func (fm *FileMapper) MapDirectory(dirPath string) error {
    return filepath.WalkDir(dirPath, func(path string, d fs.DirEntry, err error) error {
        if err != nil {
            return err
        }
        
        // Skip directories and non-regular files
        if d.IsDir() || !d.Type().IsRegular() {
            return nil
        }
        
        mappedFile, err := fm.mapSingleFile(path)
        if err != nil {
            return fmt.Errorf("failed to map %s: %w", path, err)
        }
        
        fm.mappedFiles = append(fm.mappedFiles, mappedFile)
        return nil
    })
}

// mapSingleFile maps a single file into memory
func (fm *FileMapper) mapSingleFile(filePath string) (*MappedFile, error) {
    file, err := os.Open(filePath)
    if err != nil {
        return nil, fmt.Errorf("cannot open file: %w", err)
    }
    
    stat, err := file.Stat()
    if err != nil {
        file.Close()
        return nil, fmt.Errorf("cannot stat file: %w", err)
    }
    
    size := stat.Size()
    if size == 0 {
        // Handle empty files - no mapping needed
        return &MappedFile{
            Path: filePath,
            Data: nil,
            Size: 0,
            file: file,
        }, nil
    }
    
    // Memory map the file
    data, err := syscall.Mmap(
        int(file.Fd()),    // file descriptor
        0,                 // offset
        int(size),         // length
        syscall.PROT_READ, // protection - read-only
        syscall.MAP_SHARED, // flags - shared mapping
    )
    if err != nil {
        file.Close()
        return nil, fmt.Errorf("mmap failed: %w", err)
    }
    
    return &MappedFile{
        Path: filePath,
        Data: data,
        Size: size,
        file: file,
    }, nil
}

// GetMappedFiles returns all currently mapped files
func (fm *FileMapper) GetMappedFiles() []*MappedFile {
    return fm.mappedFiles
}

// Close unmaps and closes all files
func (fm *FileMapper) Close() error {
    var lastErr error
    for _, mf := range fm.mappedFiles {
        if err := mf.Close(); err != nil {
            lastErr = err
            log.Printf("Error closing %s: %v", mf.Path, err)
        }
    }
    fm.mappedFiles = nil
    return lastErr
}

// ProcessFiles demonstrates processing mapped file contents
func (fm *FileMapper) ProcessFiles() {
    for _, mf := range fm.mappedFiles {
        fmt.Printf("\n=== Processing: %s (Size: %d bytes) ===\n", mf.Path, mf.Size)
        
        if len(mf.Data) == 0 {
            fmt.Println("Empty file")
            continue
        }
        
        // Example: Count lines
        lineCount := 0
        for _, b := range mf.Data {
            if b == '\n' {
                lineCount++
            }
        }
        
        // Example: Show first 100 characters
        preview := mf.Data
        if len(preview) > 100 {
            preview = preview[:100]
        }
        
        fmt.Printf("Lines: %d\n", lineCount)
        fmt.Printf("Preview: %s\n", string(preview))
        
        // Example: Search for specific content
        searchTerm := []byte("plan")
        if containsBytes(mf.Data, searchTerm) {
            fmt.Printf("Contains '%s': Yes\n", searchTerm)
        }
    }
}

// containsBytes checks if haystack contains needle
func containsBytes(haystack, needle []byte) bool {
    if len(needle) == 0 {
        return true
    }
    if len(haystack) < len(needle) {
        return false
    }
    
    for i := 0; i <= len(haystack)-len(needle); i++ {
        if bytesEqual(haystack[i:i+len(needle)], needle) {
            return true
        }
    }
    return false
}

// bytesEqual compares two byte slices for equality
func bytesEqual(a, b []byte) bool {
    if len(a) != len(b) {
        return false
    }
    for i := range a {
        if a[i] != b[i] {
            return false
        }
    }
    return true
}

func main() {
    dirPath := "_docs/plans/"
    
    // Create file mapper
    mapper := &FileMapper{}
    defer mapper.Close() // Ensure cleanup
    
    // Map all files in directory
    fmt.Printf("Mapping files in directory: %s\n", dirPath)
    if err := mapper.MapDirectory(dirPath); err != nil {
        log.Fatalf("Failed to map directory: %v", err)
    }
    
    // Report mapped files
    mappedFiles := mapper.GetMappedFiles()
    fmt.Printf("Successfully mapped %d files:\n", len(mappedFiles))
    
    for _, mf := range mappedFiles {
        fmt.Printf("  - %s (%d bytes)\n", mf.Path, mf.Size)
    }
    
    // Process the mapped files
    mapper.ProcessFiles()
    
    // Demonstrate direct memory access
    fmt.Println("\n=== Direct Memory Access Example ===")
    if len(mappedFiles) > 0 {
        firstFile := mappedFiles[0]
        if len(firstFile.Data) > 0 {
            // Direct byte access - very fast
            firstByte := firstFile.Data[0]
            lastByte := firstFile.Data[len(firstFile.Data)-1]
            fmt.Printf("First file '%s': first byte=0x%02x, last byte=0x%02x\n", 
                firstFile.Path, firstByte, lastByte)
            
            // Convert to string slice for text processing
            content := (*(*string)(unsafe.Pointer(&firstFile.Data)))
            fmt.Printf("Content length as string: %d characters\n", len(content))
        }
    }
}
```

## Key Features:

1. **Robust Error Handling**: Comprehensive error checking at each step
2. **Resource Management**: Proper cleanup with defer and Close methods
3. **Empty File Handling**: Safely handles zero-byte files
4. **Directory Traversal**: Uses `filepath.WalkDir` for efficient directory scanning
5. **Memory Safety**: Proper unmapping with `syscall.Munmap`
6. **Production Ready**: Structured types, clear interfaces, and proper lifecycle management

## Usage Benefits:

- **Zero-copy access**: File contents accessible as `[]byte` without copying
- **OS-optimized**: Leverages OS page cache and virtual memory
- **Scalable**: Can handle many files simultaneously
- **Fast random access**: Direct indexing into file contents

This approach is ideal for processing multiple files efficiently, especially when you need random access or when files are accessed multiple times.

## Memory Mapped Files Overview

Memory mapped files in Go allow you to map a file's contents directly into virtual memory, enabling you to access file data as if it were a regular byte slice in memory.

### Key Benefits
- **Performance**: Eliminates copying data between kernel and user space
- **Efficiency**: OS handles caching and paging automatically
- **Large files**: Can work with files larger than available RAM
- **Shared access**: Multiple processes can map the same file

### Go Implementation Options

1. **syscall package** (low-level):
```go
import "syscall"

// Map file to memory
data, err := syscall.Mmap(int(file.Fd()), 0, int(fileSize), 
    syscall.PROT_READ, syscall.MAP_SHARED)
```

2. **golang.org/x/exp/mmap** (higher-level):
```go
import "golang.org/x/exp/mmap"

reader, err := mmap.Open("filename")
defer reader.Close()
data := reader.Data() // []byte slice
```

3. **Third-party libraries** like `edsrzf/mmap-go`:
```go
import "github.com/edsrzf/mmap-go"

f, _ := os.Open("file.txt")
defer f.Close()
mmap, _ := mmap.Map(f, mmap.RDONLY, 0)
defer mmap.Unmap()
// Use mmap as []byte
```

### Use Cases
- Reading large log files
- Processing binary data
- Database implementations
- High-performance file parsing
- When you need random access to file contents

The mapped memory appears as a `[]byte` slice, making it easy to use with existing Go code.

## Advantages of Memory Mapped Files

The main advantages of memory mapped files are:

### Performance Benefits
- **Zero-copy access**: Data isn't copied between kernel and user space - you access file contents directly in memory
- **Faster I/O**: Eliminates system call overhead for reads/writes after initial mapping
- **Random access**: Jump to any position in the file instantly without seeking

### Memory Efficiency  
- **Virtual memory leverage**: Can work with files larger than available RAM - OS pages in/out as needed
- **Shared memory**: Multiple processes mapping the same file share physical memory pages
- **Automatic caching**: OS page cache handles buffering transparently

### Scalability
- **Large file handling**: Process multi-GB files without loading everything into RAM
- **Concurrent access**: Multiple threads/processes can safely access mapped regions
- **Lazy loading**: Only referenced portions are actually loaded into physical memory

### Simplicity
- **Array-like access**: File contents appear as a regular byte slice/array
- **No buffer management**: OS handles all the complex memory management
- **Automatic synchronization**: Changes can be automatically written back to disk

### When Most Beneficial
- Database storage engines
- Large log file processing  
- Binary file parsing (images, videos, executables)
- Search indexes
- Applications needing random access patterns
- High-performance data processing pipelines

The key advantage is **treating files like memory** - you get the performance of in-memory access with the persistence of disk storage, all managed transparently by the OS.

## Memory Mapping for Code Repository Search

Memory mapping your code repository files would provide significant advantages for searching and access:

### Search Performance Benefits

**Faster text searching**:
- Direct byte-level scanning without file I/O overhead
- Can use optimized string search algorithms (Boyer-Moore, etc.) directly on mapped memory
- No need to read files into buffers repeatedly

**Concurrent searching**:
- Multiple search threads can scan different files simultaneously
- All mapped files are instantly accessible without opening/closing

### Access Speed Improvements

**Instant file access**:
- No `open()` system calls - files are already "open" in memory
- Jump to any position in any file immediately
- Perfect for code navigation tools, LSPs, and IDEs

**Pattern matching**:
- Regular expressions run directly on mapped memory
- Multi-file grep operations become memory operations
- AST parsing can work directly on mapped source

### Practical Implementation for Code Repos

```go
// Example: Fast code search across repository
type CodeRepository struct {
    mappedFiles map[string]*MappedFile
}

func (cr *CodeRepository) SearchPattern(pattern []byte) []SearchResult {
    var results []SearchResult
    for path, mf := range cr.mappedFiles {
        // Direct memory search - very fast
        if matches := findAllInBytes(mf.Data, pattern); len(matches) > 0 {
            results = append(results, SearchResult{Path: path, Matches: matches})
        }
    }
    return results
}
```

### When It's Most Effective

**Repository characteristics**:
- Small to medium repositories (< 1GB total)
- Frequently accessed files
- Mixed file types (source code, configs, docs)
- Tools that need cross-file analysis

**Use cases**:
- Code search engines (ripgrep-style tools)
- Language servers needing symbol lookup
- Static analysis tools
- Code refactoring utilities
- Documentation generators

### Considerations

**Memory usage**: Files stay mapped even when not actively used
**File changes**: Need to remap files when they're modified externally  
**Repository size**: Very large repos might exhaust virtual address space

For typical code repositories, the speed improvement for search and access operations would be substantial - essentially turning file operations into memory operations.

## Virtual Address Space Limits for Large Repositories

Virtual address space limits vary significantly by architecture and can become a real constraint for large repositories:

### Architecture Limits

**32-bit systems**:
- **4GB total virtual address space** per process
- ~2-3GB available for user space (OS reserves the rest)
- **Severely limited** - even medium repositories can hit this

**64-bit systems**:
- **Theoretical**: 2^64 bytes (18.4 exabytes)
- **Practical limits** vary by OS:
  - Linux: 47-48 bits (~128TB-256TB user space)
  - Windows: 44 bits (~16TB user space)
  - macOS: 47 bits (~128TB user space)

### Real-World Repository Constraints

**Small repositories** (< 1GB):
- No issues on any modern system
- Perfect for memory mapping

**Medium repositories** (1-10GB):
- Fine on 64-bit systems
- May struggle on 32-bit systems

**Large repositories** (10-100GB):
- Still manageable on 64-bit systems
- Need careful memory management

**Massive repositories** (100GB+):
- Examples: Windows source (~300GB), Chrome (~40GB)
- Can approach virtual address space limits
- Need selective mapping strategies

### Memory Mapping Strategies for Large Repos

**Selective mapping**:
```go
// Map only frequently accessed files
func (cr *CodeRepository) MapHotFiles(accessPatterns map[string]int) {
    for path, frequency := range accessPatterns {
        if frequency > threshold {
            cr.mapFile(path)
        }
    }
}
```

**Lazy mapping**:
```go
// Map files on first access, unmap LRU files
func (cr *CodeRepository) GetFile(path string) *MappedFile {
    if mf, exists := cr.cache[path]; exists {
        return mf
    }
    return cr.mapAndCache(path)
}
```

**Partial file mapping**:
```go
// Map only portions of very large files
func mapFileRange(file *os.File, offset, length int64) ([]byte, error) {
    return syscall.Mmap(int(file.Fd()), offset, int(length), 
        syscall.PROT_READ, syscall.MAP_SHARED)
}
```

### Monitoring Virtual Memory Usage

```bash
# Linux - check virtual memory usage
cat /proc/self/status | grep Vm

# Check system limits
ulimit -v  # Virtual memory limit
```

### Practical Guidelines

**Safe to fully map**:
- Repositories < 10GB on modern 64-bit systems
- Focus on source code files (exclude binaries, node_modules, etc.)

**Use selective mapping**:
- Repositories 10GB-100GB
- Map by file type, recency, or access patterns
- Implement LRU eviction

**Avoid full mapping**:
- Repositories > 100GB
- Use traditional file I/O with smart caching instead

For most code repositories, virtual address space isn't the limiting factor - physical RAM and mapping overhead become constraints first. But for truly massive codebases, you'll need hybrid approaches combining memory mapping with traditional I/O.