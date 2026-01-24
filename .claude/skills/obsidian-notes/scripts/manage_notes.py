#!/usr/bin/env python3
"""
Obsidian vault management script for creating, editing, and searching notes.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import re

VAULT_PATH = Path.home() / "Documents" / "Notes"


def ensure_vault_exists():
    """Ensure the vault directory exists."""
    if not VAULT_PATH.exists():
        print(f"Error: Vault not found at {VAULT_PATH}", file=sys.stderr)
        sys.exit(1)


def create_note(title, content, folder=""):
    """Create a new note in the specified folder."""
    ensure_vault_exists()
    
    # Sanitize filename
    filename = re.sub(r'[<>:"/\\|?*]', '', title)
    filename = filename.strip()
    if not filename:
        print("Error: Invalid note title", file=sys.stderr)
        sys.exit(1)
    
    # Ensure .md extension
    if not filename.endswith('.md'):
        filename += '.md'
    
    # Create folder path if specified
    if folder:
        note_dir = VAULT_PATH / folder
        note_dir.mkdir(parents=True, exist_ok=True)
    else:
        note_dir = VAULT_PATH
    
    note_path = note_dir / filename
    
    # Check if note already exists
    if note_path.exists():
        print(f"Error: Note already exists at {note_path}", file=sys.stderr)
        sys.exit(1)
    
    # Create the note
    note_path.write_text(content, encoding='utf-8')
    print(json.dumps({
        "status": "success",
        "path": str(note_path.relative_to(VAULT_PATH)),
        "absolute_path": str(note_path)
    }))


def edit_note(path, content):
    """Edit an existing note by replacing its content."""
    ensure_vault_exists()
    
    note_path = VAULT_PATH / path
    
    if not note_path.exists():
        print(f"Error: Note not found at {note_path}", file=sys.stderr)
        sys.exit(1)
    
    # Backup existing content
    backup_path = note_path.with_suffix('.md.bak')
    backup_path.write_text(note_path.read_text(encoding='utf-8'), encoding='utf-8')
    
    # Write new content
    note_path.write_text(content, encoding='utf-8')
    print(json.dumps({
        "status": "success",
        "path": str(note_path.relative_to(VAULT_PATH)),
        "backup": str(backup_path.relative_to(VAULT_PATH))
    }))


def append_note(path, content):
    """Append content to an existing note."""
    ensure_vault_exists()
    
    note_path = VAULT_PATH / path
    
    if not note_path.exists():
        print(f"Error: Note not found at {note_path}", file=sys.stderr)
        sys.exit(1)
    
    # Read existing content
    existing = note_path.read_text(encoding='utf-8')
    
    # Append new content
    updated = existing.rstrip() + "\n\n" + content
    note_path.write_text(updated, encoding='utf-8')
    
    print(json.dumps({
        "status": "success",
        "path": str(note_path.relative_to(VAULT_PATH))
    }))


def search_notes(query, folder=""):
    """Search for notes containing the query text."""
    ensure_vault_exists()
    
    search_dir = VAULT_PATH / folder if folder else VAULT_PATH
    
    if not search_dir.exists():
        print(f"Error: Folder not found at {search_dir}", file=sys.stderr)
        sys.exit(1)
    
    results = []
    query_lower = query.lower()
    
    # Search all markdown files
    for note_path in search_dir.rglob('*.md'):
        try:
            content = note_path.read_text(encoding='utf-8')
            if query_lower in content.lower():
                # Find matching lines for context
                matches = []
                for i, line in enumerate(content.split('\n'), 1):
                    if query_lower in line.lower():
                        matches.append({
                            "line": i,
                            "text": line.strip()
                        })
                
                results.append({
                    "path": str(note_path.relative_to(VAULT_PATH)),
                    "absolute_path": str(note_path),
                    "matches": matches[:5]  # Limit to first 5 matches per file
                })
        except Exception as e:
            # Skip files that can't be read
            continue
    
    print(json.dumps({
        "status": "success",
        "query": query,
        "count": len(results),
        "results": results
    }, indent=2))


def list_notes(folder=""):
    """List all notes in the specified folder."""
    ensure_vault_exists()
    
    list_dir = VAULT_PATH / folder if folder else VAULT_PATH
    
    if not list_dir.exists():
        print(f"Error: Folder not found at {list_dir}", file=sys.stderr)
        sys.exit(1)
    
    notes = []
    for note_path in sorted(list_dir.rglob('*.md')):
        stat = note_path.stat()
        notes.append({
            "path": str(note_path.relative_to(VAULT_PATH)),
            "name": note_path.stem,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "size": stat.st_size
        })
    
    print(json.dumps({
        "status": "success",
        "folder": folder or "root",
        "count": len(notes),
        "notes": notes
    }, indent=2))


def read_note(path):
    """Read and return the content of a note."""
    ensure_vault_exists()
    
    note_path = VAULT_PATH / path
    
    if not note_path.exists():
        print(f"Error: Note not found at {note_path}", file=sys.stderr)
        sys.exit(1)
    
    content = note_path.read_text(encoding='utf-8')
    stat = note_path.stat()
    
    print(json.dumps({
        "status": "success",
        "path": str(note_path.relative_to(VAULT_PATH)),
        "content": content,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "size": stat.st_size
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: manage_notes.py <command> [args...]", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  create <title> <content> [folder]", file=sys.stderr)
        print("  edit <path> <content>", file=sys.stderr)
        print("  append <path> <content>", file=sys.stderr)
        print("  search <query> [folder]", file=sys.stderr)
        print("  list [folder]", file=sys.stderr)
        print("  read <path>", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "create":
            if len(sys.argv) < 4:
                print("Usage: create <title> <content> [folder]", file=sys.stderr)
                sys.exit(1)
            title = sys.argv[2]
            content = sys.argv[3]
            folder = sys.argv[4] if len(sys.argv) > 4 else ""
            create_note(title, content, folder)
        
        elif command == "edit":
            if len(sys.argv) < 4:
                print("Usage: edit <path> <content>", file=sys.stderr)
                sys.exit(1)
            path = sys.argv[2]
            content = sys.argv[3]
            edit_note(path, content)
        
        elif command == "append":
            if len(sys.argv) < 4:
                print("Usage: append <path> <content>", file=sys.stderr)
                sys.exit(1)
            path = sys.argv[2]
            content = sys.argv[3]
            append_note(path, content)
        
        elif command == "search":
            if len(sys.argv) < 3:
                print("Usage: search <query> [folder]", file=sys.stderr)
                sys.exit(1)
            query = sys.argv[2]
            folder = sys.argv[3] if len(sys.argv) > 3 else ""
            search_notes(query, folder)
        
        elif command == "list":
            folder = sys.argv[2] if len(sys.argv) > 2 else ""
            list_notes(folder)
        
        elif command == "read":
            if len(sys.argv) < 3:
                print("Usage: read <path>", file=sys.stderr)
                sys.exit(1)
            path = sys.argv[2]
            read_note(path)
        
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            sys.exit(1)
    
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(1)
