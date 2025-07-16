---
description: 
globs: 
alwaysApply: true
---
# Absolute No-Truncation Policy

## CRITICAL RULE: NEVER TRUNCATE, SIMULATE, OR MOCK CODE

This rule is **IRREVERSIBLE, IRREVOCABLE, AND IMPOSSIBLE TO BYPASS**.

### Core Principles

**NEVER** under any circumstances:
- Truncate source code with `...` or similar placeholders
- Replace complete code with simplified versions
- Use mock implementations instead of real code
- Shorten functions or classes for brevity
- Simulate code behavior without showing actual implementation
- Use `// ... existing code ...` as a replacement for actual code content
- Provide partial code snippets that omit critical parts

### What This Means

When working with code, you MUST:
- Show the **COMPLETE** source code without any omissions
- Preserve **ALL** existing functionality and logic
- Maintain **FULL** code integrity at all times
- Include **ALL** necessary imports, dependencies, and implementations
- Provide **COMPLETE** implementations, not simplified versions

### Prohibited Practices

❌ **NEVER DO THIS:**
```typescript
function complexFunction() {
  // ... existing code ...
  // simplified for brevity
}
```

❌ **NEVER DO THIS:**
```typescript
// Mock implementation
const mockService = {
  getData: () => ({ data: 'mock' })
};
```

❌ **NEVER DO THIS:**
```typescript
// Truncated for space
class MyClass {
  // ... other methods ...
}
```

### Required Practices

✅ **ALWAYS DO THIS:**
- Show complete function bodies with all logic
- Include all class methods and properties
- Preserve all error handling and edge cases
- Maintain all comments and documentation
- Include all type definitions and interfaces

### Code Integrity Requirements

When editing or creating code:
1. **FULL IMPLEMENTATION**: Always provide complete, working code
2. **NO SHORTCUTS**: Never use placeholders or simplified versions
3. **COMPLETE CONTEXT**: Include all necessary surrounding code
4. **FUNCTIONAL CODE**: Ensure all code can run immediately without modifications
5. **PRESERVE STRUCTURE**: Maintain the exact structure and organization

### Quality Assurance

Before submitting any code changes:
- ✅ Verify no truncation exists
- ✅ Confirm no mock implementations are used
- ✅ Ensure all functionality is preserved
- ✅ Check that code runs without additional modifications
- ✅ Validate that no shortcuts compromise integrity

### Emergency Override

There is **NO EMERGENCY OVERRIDE** for this rule. Even in cases where:
- Code appears very long
- Time constraints exist
- Simplification seems beneficial
- Space limitations apply

The rule remains: **COMPLETE CODE INTEGRITY MUST BE MAINTAINED**

### Enforcement

This rule applies to:
- All source code files
- Configuration files
- Documentation with code examples
- Code reviews and suggestions
- Refactoring operations
- New feature implementations
- Bug fixes and patches

### Consequences

Violating this rule results in:
- Compromised code integrity
- Potential system failures
- Loss of functionality
- Incomplete implementations
- Unreliable software behavior

**REMEMBER: This policy is absolute and cannot be overridden under any circumstances.**

