# differ

Differ is a terminal app that applies SEARCH/REPLACE blocks to files.
Use it to apply code changes that an LLM writes in a chat.

## Install

You need [uv](https://docs.astral.sh/uv/). uv installs Python 3.14 if necessary.

```sh
uv tool install --editable /path/to/differ
```

This puts the `differ` command on your PATH.
With `--editable`, changes to `src/differ/__init__.py` apply without a new install.
If you change the dependencies, run the same command with `--reinstall`.

## Start differ

Differ finds files relative to the directory where you start it.
Start it in the root of the project that you want to change:

```sh
cd /path/to/your/project
differ
```

## Workflow

1. Give the LLM the content of `instruct.md` as its system prompt or first message.
2. Give the LLM the task and the current content of each file that it must change.
3. For each `### path` heading in the answer:
   1. Type the path in the path field. Press Tab to go to the diff area.
   2. Paste the code block. Differ ignores text outside the blocks, such as fence lines.
   3. Press Ctrl+S.
4. Read the status line. If it shows an error, differ did not change the file.
   Send the error to the LLM and ask for a corrected block.
5. Press Ctrl+R to clear the diff area. Press Ctrl+R again to clear the path.

| Key    | Action                                                 |
| ------ | ------------------------------------------------------ |
| Ctrl+S | Apply the blocks to the file                           |
| Ctrl+R | Clear the diff area. If it is empty, clear the path    |
| Ctrl+Q | Quit                                                   |

## Block format

```
<<<<<<<< SEARCH
exact lines from the current file
========
new lines
>>>>>>>> REPLACE
```

Each marker has exactly 8 characters. Each marker is on its own line.
`instruct.md` has the full rules and an example.

How differ applies blocks:

- SEARCH must match complete lines exactly. Differ changes only the first match.
- Differ applies the blocks in order. If one block fails, differ changes nothing.
- An empty REPLACE deletes the SEARCH lines.
- An empty SEARCH creates the file, or rewrites all of it. It must be the only block.
- SEARCH cannot contain a line that is exactly `========`.
- Differ cannot delete, rename, or move files.

## Tests

Run the tests in the differ directory:

```sh
uv run python -m unittest
```
