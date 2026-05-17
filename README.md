# file-gallery-py

A static site generator that turns your files, directories, and macOS Finder icon positions into a website. 

This is a lightweight Python rewrite of [file-gallery](https://github.com/inchkev/file-gallery) by [inchkev](https://github.com/inchkev).

## 1. Setup & installation

Open your terminal and run these commands step by step:

```bash
# Clone the repository and enter the directory
git clone https://github.com/thsr/file-gallery-py.git
cd file-gallery-py

# Create a Python virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

## 2. Grow Your First Garden

Generate the website by running the script in your current directory:

```bash
python cultivate.py .
```

This reads your files and creates an `index.html` file. Open `index.html` in your web browser to see your site.

## 3. Make incremental changes

To update your site, follow this loop:

1. Add new files or folders to your directory.
2. Move them around in macOS Finder.
3. Rerun `python cultivate.py .` in your terminal.
4. Refresh your browser to see the changes.

## Configuration

The minimum set of files you'll need to keep is:

- `cultivate.py` the main script lives here
- `template.html.j2` the layout lives here
- `.gardenignore` add file or folder names here to hide them from the generated website
- `.gitignore` same, but files or folders here also don't get versionned if you are using Git
- `requirements.txt` the required Python packages live here

## How layouts work

The script displays your files in one of two ways:

*   **Formal (Default)**: Files are arranged in a neat, alphabetical grid.
*   **Natural (Freeform)**: Files appear on the website exactly where you placed them in the macOS Finder window (Icon view, read below).

**To use the Natural layout:**
1. Open the folder in macOS Finder.
2. Use the Icon view (Cmd+1).
3. Right click and set "Sort By" to "None".
4. Manually drag and drop every visible file to a specific position.
5. Run `python cultivate.py .`. The script automatically forces macOS to save these exact `.DS_Store` coordinates to build your freeform layout.

## Supported content

*   **Images**: jpeg, png, webp, gif, apng, svg, bmp, ico
*   **Videos**: mp4, webm
*   **Audio**: mp3, wav, ogg, m4a
*   **Markdown**: `.md` files are parsed into formatted HTML.
*   **Raw Text**: Files with no extension have their raw text displayed (useful for headers).
*   **Other**: All other files appear as downloadable links.
*   **Subdirectories**: The script traverses up to three folders deep, generating an `index.html` for each one.

## License and attribution

*   `cultivate.py` is licensed under the [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0). 
*   `template.html.j2` styles are licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
*   If you publish a site, keep the attribution link to https://kevin.garden/ or https://file.gallery/ in the HTML source.

## Changelog

**[2026-05-17] Added verbose debugging mode**
* Introduced a new `-v` or `--verbose` command line argument to toggle debug outputs

**[2026-05-17 updates] .DS_Store Parsing Fixes & Finder Sync Enhancement**
*   **Fixed `.DS_Store` Import Error**: Corrected module import to `from ds_store import DSStore`.
*   **Added `force_ds_store_update` Feature**: Added a pre-run AppleScript hook to force macOS Finder to flush its memory cache and save icon positions to `.DS_Store` immediately.

**[2026-05-17 initial Python rewrite] Ported from JavaScript (inchkev/file-gallery)**
*   **Complete Rewrite**: Ported the core static site generator from JavaScript/Node.js to Python.
*   **Templating Engine**: Migrated HTML generation to `Jinja2`.
*   **Dependency Replacements**: Replaced JavaScript dependencies with Python equivalents (PIL, pathspec, markdown, ds-store).
*   **Concurrency**: Added `ThreadPoolExecutor` for asynchronous, parallel file parsing.
*   **Type Hinting & Dataclasses**: Refactored core logic to use Python `dataclasses` and strong typing.

## To do

- [ ] Custom templates in folders