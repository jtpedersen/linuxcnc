import os
import shutil
import json
import sqlite3
from subprocess import call
from bs4 import BeautifulSoup
from pathlib import Path

name = "Linuxcnc_GCode"
root = Path(f"{name}.docset")
ds_root = root / "Contents/Resources"
doc_folder = ds_root / "Documents"
db_path = ds_root / "docSet.dsidx"

def create_directories():
    if root.exists():
        shutil.rmtree(root)
    doc_folder.mkdir(parents=True, exist_ok=True)

def create_info_plist():
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>{name}</string>
    <key>CFBundleName</key>
    <string>{name}</string>
    <key>DocSetPlatformFamily</key>
    <string>{name}</string>
    <key>isDashDocset</key>
    <true/>
</dict>
</plist>
"""
    plist_path = root / "Contents" / "Info.plist"
    with open(plist_path, "w") as plist_file:
        plist_file.write(plist_content)

def initialize_sqlite_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);")
    cursor.execute("CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);")
    conn.commit()
    conn.close()

def generate_html_from_adoc():
    # Assuming you have asciidoctor installed and *.adoc files in the current directory
    call(["asciidoctor", "-D", doc_folder, "-B", ".", "*.adoc"])
def parse(html_file):
    with open(html_file, "r") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Find all h2 and div tags that contain G-code, M-code, or O-code entries
    for tag in soup.find_all(["h2", "div"], id=True):
        tag_id = tag["id"]
        name = tag.text.strip()
        path = f"{html_file.name}#{tag_id}"

        # Determine the type based on the id prefix
        if "gcode:" in tag_id or  "mcode:" in tag_id or "ocode:" in tag_id:
            yield name, path

def add_db_entries():
    # Connect to the database
    con = sqlite3.connect(db_path)


    # Example function to parse and insert entries
    def parse_and_insert(html_file, ds_type):
        for name, path in parse(html_file):
            con.execute(
                "INSERT INTO searchIndex(name, type, path) VALUES (?, ?, ?)",
                (name, ds_type, path),
            )


    parse_and_insert(doc_folder / "g-code.html", "Command")
    parse_and_insert(doc_folder / "m-code.html", "Command")
    parse_and_insert(doc_folder / "o-code.html", "Guide")
    parse_and_insert(doc_folder / "other-code.html", "Command")
    parse_and_insert(doc_folder / "overview.html", "Guide")

    # Commit changes and close the database
    con.commit()
    con.close()

def copy_to_local():
    dst = Path("/home/jacob/.local/share/Zeal/Zeal/docsets")
    final_destination = dst / f"{name}.docset"

    # Check if the destination directory already exists
    if final_destination.exists():
        # If it exists, remove it to avoid errors
        shutil.rmtree(final_destination)

    # Copy the entire docset directory tree to the destination
    shutil.copytree(root, final_destination)
    print(f"Docset '{root}' copied to '{final_destination}'.")    

def create_meta_json():
    meta=dict()
    meta["name"] = name
    meta["revision"] = 0
    meta["title"] = name
    meta["version"] = "Linuxcnc"

    meta_path = root / "meta.json"
    print(f"{meta_path} has {meta}")
    with open(meta_path, 'w') as meta_file:
        meta_file.write(json.dumps(meta))
    
    
def main():
    create_directories()

    create_info_plist()
    create_meta_json()
    
    # Initialize SQLite database
    initialize_sqlite_db()
    
    # Generate HTML from AsciiDoc files
    generate_html_from_adoc()

    add_db_entries()

    copy_to_local()


if __name__ == "__main__":
    main()
