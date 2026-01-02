# CSV Import Guide

## Quick Answer

**Minimum required CSV format:**
```csv
front,back
hola,hello
adiós,goodbye
```

That's it! Just two columns: `front` and `back`. Everything else is optional.

**You don't need TSV** - CSV (comma-separated) works fine. TSV is only useful if your data contains commas.

**The web interface has a preview feature** - Upload your CSV, click "Preview File", and it will show you:
- What columns are available in your file
- A preview of the first 5 rows  
- Total number of rows

Then you just select which column is "front" and which is "back" from a dropdown. **You don't need to name your columns exactly "front" and "back"** - you can use any column names (like "Spanish", "English", "Question", "Answer", etc.) and just tell the system which one to use.

**When to use bulk import vs one-by-one:**
- **One-by-one**: Better when you're learning, adding cards as you encounter new words
- **Bulk import**: Better for importing existing word lists, vocabulary from textbooks, or exporting from other apps

## Overview

The CSV import feature allows you to bulk import cards from a CSV file. You can import cards with just the required fields (front/back) or include optional fields like tags, notes, and source.

## CSV Format

### Required Columns
- **front**: The prompt/question (front of the card)
- **back**: The answer (back of the card)

### Optional Columns
- **tags**: Comma or space-separated tags (e.g., "verb, present" or "verb present")
- **notes**: Additional notes about the card
- **source**: Where the card came from (e.g., "textbook chapter 5")
- **language**: Language label (e.g., "es" for Spanish, "de" for German)

## Example CSV Files

### Simple Format (Minimum Required)
```csv
front,back
hola,hello
adiós,goodbye
casa,house
```

### With Optional Fields
```csv
front,back,tags,notes,source,language
hola,hello,"greeting, basic","Common greeting","Textbook Ch1",es
adiós,goodbye,"greeting, basic","Farewell","Textbook Ch1",es
casa,house,"noun, basic","Home or house","Textbook Ch2",es
```

### With Tags (Comma-separated)
```csv
front,back,tags
hablar,to speak,"verb, present, regular"
comer,to eat,"verb, present, regular"
```

### With Tags (Space-separated)
```csv
front,back,tags
hablar,to speak,verb present regular
comer,to eat,verb present regular
```

## How It Works

1. **Upload File**: Select your CSV file (`.csv` or `.tsv`)
2. **Preview**: Click "Preview File" to see:
   - Available columns in your file
   - Total number of rows
   - Preview of first 5 rows
3. **Select Columns**: Choose which column contains:
   - Front (prompt)
   - Back (answer)
4. **Configure Options**:
   - Language (optional)
   - Create reverse cards (default: Yes) - creates back→front cards automatically
5. **Import**: Click "Import Cards" to import all cards

## TSV Format

TSV (Tab-Separated Values) is supported but not required. Use TSV if:
- Your data contains commas that you don't want to escape
- You prefer tabs as delimiters

Example TSV:
```
front	back	tags
hola	hello	greeting
adiós	goodbye	greeting
```

The system auto-detects the delimiter based on file extension (`.tsv` = tab, `.csv` = comma).

## Column Names

**Important**: Column names are case-sensitive and must match exactly. The import feature will show you all available columns when you preview the file, so you can see exactly what column names to use.

Common column name variations you might use:
- `front`, `Front`, `FRONT`, `prompt`, `question`
- `back`, `Back`, `BACK`, `answer`, `translation`
- `tags`, `Tags`, `TAGS`, `tag`
- `notes`, `Notes`, `NOTES`, `note`, `comment`
- `source`, `Source`, `SOURCE`
- `language`, `Language`, `LANGUAGE`, `lang`

## Tips

1. **Start Simple**: If you're unsure, start with just `front` and `back` columns
2. **Use Preview**: Always preview your file first to see what columns are available
3. **One-by-One vs Bulk**: 
   - **One-by-one**: Better for learning the system, adding cards as you encounter them
   - **Bulk import**: Better for importing existing word lists, vocabulary from textbooks, etc.
4. **Reverse Cards**: By default, reverse cards are created automatically. If you uncheck this, only forward cards (front→back) will be created.

## Example Use Cases

### Importing from a Vocabulary List
```csv
front,back,source
hola,hello,"Spanish 101 - Chapter 1"
adiós,goodbye,"Spanish 101 - Chapter 1"
gracias,thank you,"Spanish 101 - Chapter 1"
```

### Importing with Categories
```csv
front,back,tags
hola,hello,greeting
adiós,goodbye,greeting
hablar,to speak,verb
casa,house,noun
```

### Importing from Anki Export
If you export from Anki, you might get:
```csv
Front,Back
hola,hello
adiós,goodbye
```
Just select "Front" as front column and "Back" as back column when importing.

## Troubleshooting

- **"Column not found"**: Check the exact column name (case-sensitive) in the preview
- **"File encoding error"**: Save your CSV as UTF-8 encoding
- **Empty rows**: Rows with empty front or back will be skipped with an error message
- **Special characters**: Make sure your CSV is UTF-8 encoded to handle accents and special characters
