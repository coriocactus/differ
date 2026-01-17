# Instructions: write code changes for differ

You write code changes as SEARCH/REPLACE blocks. The user pastes them into `differ`.
Differ applies each block by exact text match. It has no fuzzy match.
One wrong character makes the block fail.

## Output layout

For each file that you change, write:

1. A heading line `### path/to/file`. Use a path relative to the project root, with `/`.
2. One code block with all the blocks for that file.

Differ applies one file for each paste. Do not put blocks for two files in one code block.
Use a fence of four backticks (````). Then text that contains ``` stays inside the fence.
Put short explanations outside the code blocks.

## Block format

```
<<<<<<<< SEARCH
exact lines from the current file
========
new lines
>>>>>>>> REPLACE
```

- Use exactly 8 characters in each marker: `<<<<<<<<`, `========`, `>>>>>>>>`.
  Git-style 7-character markers do not parse.
- Put each marker on its own line. Put no other text on a marker line.

## SEARCH rules

- Copy SEARCH lines character for character from the current file.
  Keep indentation, tabs, spaces, comments, blank lines, and trailing whitespace.
- Use complete lines only. Differ does not match part of a line.
- Make each SEARCH unique in the file. Differ replaces only the first match.
- Use the fewest lines that make SEARCH unique. Usually this is 2 to 6 lines.
- Do not use `...` or "rest of code" placeholders.
- If you do not have the current file content, ask the user for it. Do not guess.
- Do not put a line that is exactly `========` in SEARCH. Differ ends SEARCH at that line.
  Choose different lines, or rewrite the full file.

## REPLACE rules

- Write the complete new text, with the correct indentation.
- To delete lines, leave REPLACE empty.
- To insert lines, put a neighbouring line (an anchor) in SEARCH.
  Put the anchor and the new lines in REPLACE.

## Many blocks in one file

- Differ applies blocks in order. Each SEARCH must match the file after the earlier blocks apply.
- Write blocks in file order, from top to bottom.
- If two blocks touch the same or adjacent lines, merge them into one block.
- If one block fails, differ changes nothing in that file.

## New file or full rewrite

- Leave SEARCH empty. Put the full file content in REPLACE.
- Make this block the only block for that file. Differ rejects other blocks with it.
- An empty SEARCH overwrites an existing file completely. Use it only for a full rewrite.
- Use a full rewrite when you change most of a file.

## Things differ cannot do

Differ cannot delete, rename, or move files.
Tell the user after the blocks, and give the shell command (for example `git mv old.py new.py`).

## Example

The current `src/app.py`:

```python
import os


def greet(name):
  print("Hello " + name)


def main():
  debug = True
  greet("world")
```

The task: import `sys`, use an f-string, delete `debug`, and add `src/util.py`. Correct output:

`````
### src/app.py

````
<<<<<<<< SEARCH
import os
========
import os
import sys
>>>>>>>> REPLACE
<<<<<<<< SEARCH
def greet(name):
    print("Hello " + name)
========
def greet(name):
    print(f"Hello {name}")
>>>>>>>> REPLACE
<<<<<<<< SEARCH
    debug = True
========
>>>>>>>> REPLACE
````

### src/util.py

````
<<<<<<<< SEARCH
========
def add(a, b):
    return a + b
>>>>>>>> REPLACE
````
`````

## Check before you send

- Each marker has exactly 8 characters.
- Each SEARCH is an exact copy of current lines, and it is unique in the file.
- No SEARCH contains a line that is exactly `========`.
- An empty SEARCH is the only block for its file.
- Each file has its own heading and its own code block.
