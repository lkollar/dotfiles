---
name: obsidian-notes
description: Manage notes in an Obsidian vault including creating, editing, searching, and organizing notes in folders. Use when the user asks to create notes, save information to Obsidian, search their notes, update existing notes, or work with their knowledge base. Supports project documentation in Project folder with subfolders for organization.
---

# Obsidian Notes Management

This skill enables Claude to manage notes in the user's Obsidian vault located at `~/Documents/Notes`.

## Vault Structure

- **Vault location**: `~/Documents/Notes`
- **Project documentation**: Store in `Project/` folder with subfolders for different projects
- **Additional categories**: Will be added as needed

## Operations

### Create a New Note

Use the `manage_notes.py` script to create new notes:

```bash
python scripts/manage_notes.py create "Note Title" "Note content here" [folder]
```

**Parameters**:
- `title`: Note title (will be sanitized for filename)
- `content`: Full markdown content of the note
- `folder`: Optional folder path (e.g., "Project/MyProject")

**Example**:
```bash
python scripts/manage_notes.py create "API Documentation" "# API Docs\n\n## Overview\nThis documents our API..." "Project/Backend"
```

### Read a Note

Read the content of an existing note:

```bash
python scripts/manage_notes.py read "path/to/note.md"
```

Returns JSON with the note content, modification date, and size.

### Edit a Note

Replace the entire content of an existing note:

```bash
python scripts/manage_notes.py edit "path/to/note.md" "New content here"
```

Creates a `.bak` backup of the original content before editing.

### Append to a Note

Add content to the end of an existing note:

```bash
python scripts/manage_notes.py append "path/to/note.md" "Additional content"
```

### Search Notes

Search for notes containing specific text:

```bash
python scripts/manage_notes.py search "query text" [folder]
```

**Parameters**:
- `query`: Search term (case-insensitive)
- `folder`: Optional folder to limit search scope

Returns JSON with matching notes and line numbers where matches occur.

### List Notes

List all notes in the vault or a specific folder:

```bash
python scripts/manage_notes.py list [folder]
```

Returns JSON with note paths, names, modification dates, and sizes.

## Best Practices

### Content Formatting

- Always use proper markdown formatting in note content
- Include frontmatter (YAML metadata) when helpful for Obsidian features
- Use WikiLinks `[[Note Name]]` for internal links to other notes
- Use standard markdown links `[text](url)` for external links

### Project Documentation

- Create project notes in `Project/ProjectName/` subfolders
- Use consistent naming conventions (e.g., `README.md`, `architecture.md`, `api-docs.md`)
- Include timestamps or dates in meeting notes
- Link related notes together using WikiLinks

### Search and Organization

- Search before creating to avoid duplicates
- Use descriptive titles that reflect content
- Consider folder structure when organizing related notes
- Tag notes with `#tags` for cross-cutting topics

## Working with JSON Output

All script commands return JSON output. Parse the JSON to:
- Check operation status
- Extract note content or search results
- Handle errors gracefully

Example JSON response structure:
```json
{
  "status": "success",
  "path": "Project/MyProject/notes.md",
  "content": "Note content..."
}
```

## Error Handling

- Script exits with non-zero status on errors
- Error messages are printed to stderr
- Backup files (`.bak`) are created before editing operations
- Vault existence is verified before all operations

## Workflow Examples

### Creating Project Documentation

1. List existing projects: `list Project/`
2. Create project subfolder structure as needed
3. Create notes with appropriate titles and content
4. Link notes together using WikiLinks

### Searching and Updating

1. Search for relevant notes: `search "topic"`
2. Read specific notes: `read "path/to/note.md"`
3. Either edit (replace) or append (add to) as needed
4. Verify changes by reading the note again

### Organizing Information

1. Determine appropriate folder structure
2. Create notes in correct locations
3. Use consistent naming and formatting
4. Add cross-references between related notes
