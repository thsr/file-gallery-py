# python defaults
import os
import sys
import json
import struct
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

# jinja templating
from jinja2 import Environment, FileSystemLoader
# get dimensions of image/videos
from PIL import Image, ImageOps
# fast glob matching / parse .gitignore files
import pathspec
# markdown parsing
import markdown
# ds_store parsing
from ds_store import DSStore


GARDEN_DIR = Path(__file__).parent.resolve()

TEMPLATE_FILE = 'template.html.j2'

TOP_PADDING_PX_FREEFORM = 50

VERBOSE = False

# parse .gitignore files
def load_ignores() -> pathspec.PathSpec:
    patterns = []
    for ignore_file in ['.gitignore', '.gardenignore']:
        filepath = GARDEN_DIR / ignore_file
        if filepath.exists():
            with open(filepath, 'r') as f:
                patterns.extend(f.read().splitlines())
    return pathspec.PathSpec.from_lines('gitwildmatch', patterns)

IGNORE_SPEC = load_ignores()


@dataclass
class FileItem:
    path: str
    name: str
    type: str
    size: str = ""
    contents: str = ""
    width: int = 0
    height: int = 0
    location: dict = field(default_factory=dict)


# formatting file sizes
def format_bytes(size: int) -> str:
    for unit in ['B', 'kB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1000.0:
            if unit == 'B':
                return f"{int(size)}{unit}"
            return f"{size:g}{unit}"
        size /= 1000.0
    return f"{size:g}PB"


def get_video_dimensions(filepath: str):
    try:
        cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
               '-show_entries', 'stream=width,height', '-of', 'json', filepath]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        info = json.loads(output)
        width = info['streams'][0]['width']
        height = info['streams'][0]['height']
        return width, height
    except Exception as err:
        print('Error reading video:', filepath)
        print(err)
        return 0, 0


def force_ds_store_update(folder_path: Path):
    """Forces macOS Finder to flush its memory cache to the .DS_Store file."""
    # Only run this on macOS
    if sys.platform != 'darwin':
        return
        
    # AppleScript to tell Finder to update the folder's disk representation
    script = f'''
    tell application "Finder"
        try
            set targetFolder to POSIX file "{folder_path.resolve()}" as alias
            update targetFolder
        end try
    end tell
    '''
    try:
        subprocess.run(['osascript', '-e', script], capture_output=True, check=True)
    except Exception as e:
        if VERBOSE:
            print(f"DEBUG: Failed to force Finder update for {folder_path}: {e}. Manually refresh .DS_Store by opening the folder in Finder and deleting index.html, then re-run the script.")


def parse_ds_store(filepath: Path) -> dict:
    """Parses a given .DS_Store file into a JSON-like dictionary mapping."""
    results = {}
    try:
        with DSStore.open(str(filepath), 'r') as d:
            for item in d:
                # DEBUG: Inspect the objects yielded by iterating over d
                if VERBOSE:
                    print(f"DEBUG: Yielded item type: {type(item)}")
                
                # Check if it's a DSStoreEntry object
                if hasattr(item, 'filename'):
                    if VERBOSE:
                        print(f"DEBUG:   Entry -> filename: {item.filename!r} | code: {item.code!r} | value: {item.value!r}")
                    
                    filename = item.filename
                    if filename not in results:
                        results[filename] = {}
                        
                    # We are only looking for icon location (Iloc) codes
                    if item.code == b'Iloc':
                        data = item.value
                        if isinstance(data, tuple) and len(data) >= 2:
                            x, y = data[:2]
                        else:
                            x, y = struct.unpack('>II', data[:8])
                        results[filename]['Iloc'] = {'x': x, 'y': y}
                else:
                    # Fallback just in case it yields a string
                    filename = item
                    if filename not in results:
                        results[filename] = {}
                    
                    entry = d[filename]
                    if b'Iloc' in entry:
                        data = entry[b'Iloc']
                        if isinstance(data, tuple) and len(data) >= 2:
                            x, y = data[:2]
                        else:
                            x, y = struct.unpack('>II', data[:8])
                        results[filename]['Iloc'] = {'x': x, 'y': y}
                        
    except Exception as e:
        print(f"Error parsing .DS_Store: {e}")
        return None
    return results


def cultivate_directory(file_name: str, dir_ds_store: dict, curr_path: Path, relative_path: str, depth: int) -> FileItem:
    # recurse! also, cultivate() returns directory length
    dir_loc = None
    if dir_ds_store and file_name in dir_ds_store:
        dir_loc = dir_ds_store[file_name].get('Iloc')
    elif dir_ds_store:
        if VERBOSE:
            print(f"DEBUG: Directory {file_name!r} NOT found in .DS_Store or missing Iloc")

    file_count = cultivate(
        curr_path,
        os.path.join(relative_path, file_name),
        file_name,
        depth - 1
    )

    item = FileItem(
        path=f"{file_name}/",
        name=f"{file_name}/",
        type='directory',
        contents='directory' if file_count == 0 else f"{file_count} item{'s' if file_count > 1 else ''}"
    )
    if dir_loc:
        item.location = dir_loc
    return item


def cultivate_file(file_name: str, curr_path: Path, dir_ds_store: dict) -> FileItem:
    file_path = curr_path / file_name
    stats = file_path.stat()
    file_info = FileItem(
        path=file_name,
        name=file_name,
        type='',
        size=format_bytes(stats.st_size)
    )

    if dir_ds_store and file_name in dir_ds_store and 'Iloc' in dir_ds_store[file_name]:
        file_info.location = dir_ds_store[file_name]['Iloc']
    elif dir_ds_store:
        if VERBOSE:
            print(f"DEBUG: File {file_name!r} NOT found in .DS_Store or missing Iloc")

    file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
    
    if file_ext in {'jpeg', 'jpg', 'png', 'webp', 'gif', 'apng', 'svg', 'bmp', 'ico'}:
        # image
        file_info.type = 'image'
        try:
            with Image.open(file_path) as img:
                # exif quirks with jpeg orientation info
                img = ImageOps.exif_transpose(img)
                file_info.width, file_info.height = img.size
        except Exception as err:
            print('Error reading image:', file_path)
            print(err)
            
    elif file_ext in {'mp4', 'webm'}:
        # video
        file_info.type = 'video'
        file_info.width, file_info.height = get_video_dimensions(str(file_path))
            
    elif file_ext in {'mp3', 'wav', 'ogg', 'm4a'}:
        # audio
        file_info.type = 'audio'
        
    elif file_ext == 'md':
        # markdown
        file_info.type = 'markdown'
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_info.contents = markdown.markdown(f.read())
        except Exception as err:
            print('Error reading file:', file_path)
            print(err)
            
    elif file_ext == '':
        # raw if no extension
        if file_name == 'LICENSE':
            # skip 'LICENSE' files
            file_info.type = 'other'
        else:
            file_info.type = 'raw'
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_info.contents = f.read()
            except Exception as err:
                print('Error reading file:', file_path)
                print(err)
                
    elif file_ext == 'txt':
        # don't render text files
        file_info.type = 'other'
    else:
        # other
        file_info.type = 'other'

    return file_info


"""
the house has a garden
"""
def cultivate(root_path: Path, relative_path: str = '.', curr_dir: str = '', depth: int = 3) -> int:
    if depth < 0:
        return 0

    curr_path = root_path / curr_dir
    if (curr_path / '.gardenkeep').exists():
        return 0

    dir_data = {
        'title': f"{relative_path}/" if relative_path != '.' else '',
        'files': []
    }

    render_freeform = False
    all_file_entries = list(curr_path.iterdir())

    # Force Finder to update the folder's .DS_Store before reading
    force_ds_store_update(curr_path)

    # Note: re-evaluate all_file_entries just in case .DS_Store was just created
    all_file_entries = list(curr_path.iterdir())

    # parse .DS_Store
    dir_ds_store = None
    if any(e.name == '.DS_Store' for e in all_file_entries):
        dir_ds_store = parse_ds_store(curr_path / '.DS_Store')
        if dir_ds_store is None:
            render_freeform = False
        else:
            # if we don't have an icvp dict (because parent reliance was removed),
            # assume true and rely on duck-typing 'Iloc' check below to catch formals.
            render_freeform = True
        
        if VERBOSE:
            print('DEBUG: parsed .DS_Store for', curr_path)
            print('DEBUG:', dir_ds_store)
            print('DEBUG: renderFreeform:', render_freeform)

    # split into filtered directories and files
    directories_to_process = []
    files_to_process = []
    for entry in all_file_entries:
        file_name = entry.name
        match_name = f"{file_name}/" if entry.is_dir() else file_name
        
        if IGNORE_SPEC.match_file(match_name) or IGNORE_SPEC.match_file(file_name):
            continue
            
        if entry.is_dir():
            directories_to_process.append(file_name)
        elif entry.is_file():
            files_to_process.append(file_name)

    # process them all asynchronously
    processed_files = []
    with ThreadPoolExecutor() as executor:
        dir_futures = [
            executor.submit(cultivate_directory, d, dir_ds_store, curr_path, relative_path, depth)
            for d in directories_to_process
        ]
        file_futures = [
            executor.submit(cultivate_file, f, curr_path, dir_ds_store)
            for f in files_to_process
        ]

        processed_files.extend(f.result() for f in dir_futures)
        processed_files.extend(f.result() for f in file_futures)

    processed_files.sort(key=lambda x: x.name)
    dir_data['files'] = processed_files

    if render_freeform:
        if VERBOSE:
            print(f"\nDEBUG: Validating freeform requirement for {curr_path}")
        for f in dir_data['files']:
            has_loc = hasattr(f, 'location') and bool(f.location)
            if VERBOSE:
                print(f"DEBUG:   File: {f.name!r} | has location? {has_loc} | location data: {getattr(f, 'location', None)}")

    if render_freeform and not all(hasattr(f, 'location') and f.location for f in dir_data['files']):
        if VERBOSE:
            print(f"DEBUG:   -> MISSING LOCATIONS! Reverting to formal (render_freeform = False)\n")
        render_freeform = False
    elif render_freeform:
        if VERBOSE:
            print(f"DEBUG:   -> ALL LOCATIONS PRESENT! Keeping freeform (render_freeform = True)\n")

    processed_file_count = len(dir_data['files'])

    # if freeform, do a hack to kinda "center" the contents
    if render_freeform:
        locations_x = [f.location['x'] for f in dir_data['files']]
        locations_y = [f.location['y'] for f in dir_data['files']]
        if locations_x and locations_y:
            min_location_x = min(locations_x)
            max_location_x = max(locations_x)
            min_location_y = min(locations_y)
            
            for file_info in dir_data['files']:
                file_info.location['x'] -= min_location_x
                file_info.location['y'] -= min_location_y
                file_info.location['y'] += TOP_PADDING_PX_FREEFORM
                
            dir_data['center_offset'] = (max_location_x - min_location_x) / 2.0

    dir_data['render_freeform'] = render_freeform

    # generate html file from associated template
    env = Environment(loader=FileSystemLoader(GARDEN_DIR))
    template = env.get_template(TEMPLATE_FILE)
    html = template.render(**dir_data)
    
    output_path = curr_path / 'index.html'

    # plant html file
    if processed_file_count > 0:
        try:
            print('Read', processed_file_count, 'of', len(all_file_entries), 'files from', relative_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print('\tPlanted', os.path.join(relative_path, 'index.html'), f"({'natural' if render_freeform else 'formal'})")
        except Exception as err:
            print(f"Could not plant {output_path}, skipping. Error:\n\t{err}")

    return processed_file_count


"""
the shed has a toolbox
"""
def cultivate_helper(root: Path):
    # check if directory provided is valid
    if not root.is_dir():
        print(f"invalid directory {root}", file=sys.stderr)
        return

    # plant
    cultivate(root, '.', '', depth=3)


if __name__ == "__main__":
    usage = ('how do we turn a directory into a garden?\n'
             'usage:      python cultivate.py [OPTIONS] DIR\n'
             'options:    -h, --help       print help\n'
             '            -v, --verbose    print debug information')

    if '-h' in sys.argv or '--help' in sys.argv:
        print(usage)
    else:
        if '-v' in sys.argv or '--verbose' in sys.argv:
            VERBOSE = True
        
        args = [arg for arg in sys.argv[1:] if arg not in ('-v', '--verbose')]

        if len(args) == 1:
            try:
                resolved_path = Path(args[0]).resolve()
                cultivate_helper(resolved_path)
            except Exception as err:
                print(f"invalid directory {args[0]}", file=sys.stderr)
                print(err, file=sys.stderr)
        else:
            print(usage)