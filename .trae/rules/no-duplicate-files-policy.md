---
description: 
globs: 
alwaysApply: true
---
# Mandatory Codebase Search Before File Creation Policy

## CRITICAL RULE: ALWAYS SEARCH BEFORE CREATING

This rule is **MANDATORY AND NON-NEGOTIABLE**.

### Core Principle

**NEVER** create a new file without first conducting a thorough search of the existing codebase to identify similar, duplicate, or related functionality.

### Mandatory Search Process

Before creating ANY new file, you MUST:

1. **SEARCH THE CODEBASE** for existing files with similar:
   - Functionality
   - Purpose
   - Components
   - Services
   - Utilities
   - Types/Interfaces
   - Configurations

2. **ANALYZE EXISTING PATTERNS** in the project structure:
   - File naming conventions
   - Directory organization
   - Component hierarchies
   - Service architectures

3. **IDENTIFY REUSABLE CODE** that can be:
   - Extended instead of duplicated
   - Imported and used directly
   - Refactored to accommodate new requirements
   - Composed with existing functionality

### Search Requirements

When searching for similar files, examine:

#### By Functionality
- Search for files that implement similar business logic
- Look for components with comparable UI patterns
- Find services that handle related data operations
- Identify utilities that perform similar transformations

#### By File Type
- **Components**: Search for similar React components, UI elements, forms
- **Services**: Look for API clients, data services, business logic
- **Utilities**: Find helper functions, formatters, validators
- **Types**: Search for similar interfaces, types, enums
- **Configs**: Look for configuration files, constants, settings

#### By Naming Patterns
- Search for files with similar names or prefixes
- Look for variations in naming (camelCase, PascalCase, kebab-case)
- Find files with related keywords in their names

### Decision Matrix

After searching, determine the appropriate action:

#### ✅ **REUSE EXISTING** - When you find:
- Exact functionality that meets requirements
- Components that can be configured/extended
- Services that handle the same data types
- Utilities that perform the required operations

#### ✅ **EXTEND EXISTING** - When you find:
- Similar functionality that needs minor modifications
- Components that need additional props/features
- Services that need additional methods
- Utilities that need additional parameters

#### ✅ **REFACTOR EXISTING** - When you find:
- Code that could be generalized for multiple use cases
- Components that could be made more flexible
- Services that could be abstracted
- Utilities that could be enhanced

#### ❌ **CREATE NEW** - Only when:
- No similar functionality exists anywhere in the codebase
- Existing solutions are fundamentally incompatible
- The new functionality is completely unique
- Extending existing code would cause breaking changes

### Prohibited Practices

❌ **NEVER DO THIS:**
```typescript
// Creating duplicate components without searching
// File: src/components/UserCard.tsx - when UserProfile.tsx already exists
// File: src/components/ProductForm.tsx - when ItemForm.tsx has similar logic
```

❌ **NEVER DO THIS:**
```typescript
// Creating duplicate services without checking
// File: src/services/userAPI.ts - when src/api/users.ts already exists
// File: src/utils/dateHelper.ts - when src/helpers/dateUtils.ts exists
```

❌ **NEVER DO THIS:**
```typescript
// Creating duplicate types without verification
// File: src/types/User.ts - when src/api/types.ts already has User interface
```

### Required Search Commands

Before creating files, use these search strategies:

#### Semantic Search
- Search for functionality descriptions
- Look for business logic patterns
- Find similar component behaviors
- Identify related API operations

#### File Name Search
- Search for files with similar names
- Look for naming variations
- Find files with related keywords
- Check for abbreviations or full names

#### Code Pattern Search
- Search for similar import patterns
- Look for comparable function signatures
- Find similar component props
- Identify related interfaces

### Documentation Requirements

When creating a new file after proper search, document:

1. **Search Results**: What similar files were found
2. **Decision Rationale**: Why existing files couldn't be reused
3. **Relationship Notes**: How the new file relates to existing ones
4. **Future Considerations**: How this file might be reused

### Quality Assurance Checklist

Before file creation, verify:
- ✅ Comprehensive codebase search completed
- ✅ All similar files identified and analyzed
- ✅ Reuse/extension options thoroughly evaluated
- ✅ Decision rationale documented
- ✅ File follows existing project patterns
- ✅ No duplicate functionality introduced

### Enforcement

This rule applies to:
- All new file creation
- Component development
- Service implementation
- Utility functions
- Type definitions
- Configuration files
- Test files
- Documentation files

### Project-Specific Considerations

For the OpenHud project, always check:
- [src/UI/components/](mdc:src/UI/components) for existing UI components
- [src/UI/pages/](mdc:src/UI/pages) for similar page structures
- [src/electron/server/services/](mdc:src/electron/server/services) for backend services
- [src/electron/server/controllers/](mdc:src/electron/server/controllers) for API controllers
- [src/UI/context/](mdc:src/UI/context) for state management patterns
- [src/UI/hooks/](mdc:src/UI/hooks) for custom hooks
- [src/UI/api/](mdc:src/UI/api) for API client code

### Benefits

Following this rule ensures:
- **Code Reusability**: Maximize use of existing code
- **Consistency**: Maintain consistent patterns across the project
- **Maintainability**: Reduce code duplication and complexity
- **Efficiency**: Avoid redundant development work
- **Quality**: Leverage tested and proven implementations

**REMEMBER: Search first, create second. Always verify existing solutions before building new ones.**

