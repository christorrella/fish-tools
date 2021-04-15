"""
Project: FISH-tools.py
Author: Chris Torrella
Date: April 15, 2021
Description:
    This tool is designed to unpack the .tla "ToneLibraryArchive"(?)
    format used by Melbourne House/Atari for the PS2 and PSP versions of
    Test Drive Unlimited.
editrial notes:
    The PSP and PS2 disc images of TDU contain a packaged file format *.PCK
    with a "file magic" of "MHPF". *.TLA files have a magic signature of
    "FISH", which I still don't understand the meaning of. (help me..?)
    The .tla file format is only publicly accessible after using a tool
    like mhpf-tools (https://github.com/christorrella/mhpf-tools)
    to extract the .tla, .tlb and .vac sound source files from a .PCK file.
    Interestingly, the PSP disc image released in the US contains the .vac and .tlb
    files that were likely combined to create the .tla archive format.
    Using .tlb and .vac files as a reference, and having written the mhpf-tools
    unpacker, it was relativley easy to write this script to extract the "tones"
    from .tla ToneLibrary archives.

    Writing the mhpf-tools was hard because there was zero documentation
    available that would have helped me understand the encoding and structure
    of these file formats. With .tla, it was fortunate that the PSP disc image
    had the .tlb and .vac files left on the dic on accident (these are not visible
    on the PS2 archive versions, and as is on the PSP disc, they take up vital space).

    Total time required to figure out the relationship between .tla, tlb and .vac files: ~12 hours
    Total time required to figure out offsets and meanings of integers/offsets in .tla: ~12 hours
    Total time required to write FISH-tools.py: ~24 hours

    Total time required to understand MHPF .pck format: ~1 year (lots of time off in-between looking)

    Future aspirations: make the conversion from RAW Compressed ADPCM to WAV automatic
    (I have no idea how sound files work, and ffmpeg isn't being very nice)
"""

import os, errno, sys, re

global header
global fi
global tone_info

class Header:
    def __init__(
                    self,
                    magic,
                    library_size,
                    version,
                    num_tones,
                    vac_file_source_str_len,
                    vac_file_source_str,
                    unknown,
                    magic2,
                    info_table_relative_offset,
                    data_table_length,
                    padding_len,
                    data_table_absolute_offset,
                    info_table_absolute_offset
                                                ):
        self.magic = magic
        self.library_size = library_size
        self.version = version
        self.num_tones = num_tones
        self.vac_file_source_str_len = vac_file_source_str_len
        self.vac_file_source_str = vac_file_source_str
        self.unknown = unknown
        self.magic2 = magic2
        self.info_table_relative_offset = info_table_relative_offset
        self.data_table_length = data_table_length
        self.padding_len = padding_len

        #for easy parsing later
        self.data_table_absolute_offset = data_table_absolute_offset
        self.info_table_absolute_offset = info_table_absolute_offset

    def __str__(self):
        return f"\
magic: {self.magic},\n\
library_size: {self.library_size},\n\
version: {self.version},\n\
num_tones: {self.num_tones},\n\
vac_file_source_str_len: {self.vac_file_source_str_len},\n\
vac_file_source_str: {self.vac_file_source_str},\n\
unknown: {self.unknown},\n\
magic2: {self.magic2},\n\
info_table_relative_offset: {self.info_table_relative_offset},\n\
data_table_length: {self.data_table_length},\n\
padding_len: {self.padding_len},\n\
data_table_absolute_offset: {self.data_table_absolute_offset},\n\
info_table_absolute_offset: {self.info_table_absolute_offset},\n\
"


def littleBytesToInt(bytes):
    return int.from_bytes(bytes, "little", signed=False)


def read_header():
    global fi

    magic = fi.read(18).decode("utf-8")
    library_size = littleBytesToInt(fi.read(4))
    version = littleBytesToInt(fi.read(4))
    num_tones = littleBytesToInt(fi.read(4))
    vac_file_source_str_len = littleBytesToInt(fi.read(4))
    vac_file_source_str = fi.read(vac_file_source_str_len).decode("utf-8")
    unknown = littleBytesToInt(fi.read(1))
    magic2 = fi.read(12).decode("utf-8")

    relative = fi.tell() #useful for finding absolute offset

    info_table_relative_offset = littleBytesToInt(fi.read(4))
    data_table_length = littleBytesToInt(fi.read(4))
    padding_len = littleBytesToInt(fi.read(4))

    #useful for parsing later
    data_table_absolute_offset = padding_len + fi.tell()
    info_table_absolute_offset = info_table_relative_offset + relative

    global header
    header = Header(
                    magic,
                    library_size,
                    version,
                    num_tones,
                    vac_file_source_str_len,
                    vac_file_source_str,
                    unknown,
                    magic2,
                    info_table_relative_offset,
                    data_table_length,
                    padding_len,
                    data_table_absolute_offset,
                    info_table_absolute_offset
                                                )

    if header.magic != "FISH~ToneLibrary\x00\x00":
        print("WARNING: File may not be a FISH~ToneLibrary: header magic corrupt. (Something smells, uh, not FISH-y)")

class Tone:
    def __init__(
                    self,
                    magic,
                    info_length,
                    version,
                    name_len,
                    name,
                    tone_data_relative_offset,
                    sample_rate,
                    loop,
                    root_note
                                                ):
        self.magic = magic
        self.info_length = info_length
        self.version = version
        self.name_len = name_len
        self.name = name
        self.tone_data_relative_offset = tone_data_relative_offset
        self.sample_rate = sample_rate
        self.loop = loop
        self.root_note = root_note

    def __str__(self):
        return f"\
magic: {self.magic},\n\
info_length: {self.info_length},\n\
version: {self.version},\n\
name_len: {self.name_len},\n\
name: {self.name},\n\
tone_data_relative_offset: {self.tone_data_relative_offset},\n\
tone_data_absolute_offset: {self.tone_data_absolute_offset},\n\
tone_data_size: {self.tone_data_size},\n\
sample_rate: {self.sample_rate},\n\
loop: {self.loop},\n\
root_note: {self.root_note},\n\
"

    def set_tone_data_size(self, tone_data_size):
        self.tone_data_size = tone_data_size

    def set_tone_data_absolute_offset(self, tone_data_absolute_offset):
        self.tone_data_absolute_offset = tone_data_absolute_offset

def read_tone_info_table():
    global fi
    global tone_info

    tone_info = []

    num_tones = header.num_tones
    info_table_absolute_offset = header.info_table_absolute_offset

    fi.seek(info_table_absolute_offset)

    for i in range(num_tones):
        magic = fi.read(7).decode("utf-8")
        info_length = littleBytesToInt(fi.read(4))
        version = littleBytesToInt(fi.read(4))
        name_len = littleBytesToInt(fi.read(4))
        name = fi.read(name_len).decode("utf-8")
        tone_data_relative_offset = littleBytesToInt(fi.read(4))
        sample_rate = littleBytesToInt(fi.read(4))
        loop = True if littleBytesToInt(fi.read(1)) == 1 else False
        root_note = littleBytesToInt(fi.read(4))

        tone = Tone(magic, info_length, version, name_len, name, tone_data_relative_offset, sample_rate, loop, root_note)
        tone_info.append(tone)

    #calculate absolute offsets for all tone data
    for tone in tone_info:
        tone.set_tone_data_absolute_offset(tone.tone_data_relative_offset + header.data_table_absolute_offset)

    #calculate sizes of tone data
    prev = 0
    for i in range(len(tone_info)-1):
        size = tone_info[i+1].tone_data_relative_offset - prev
        tone_info[i].set_tone_data_size(size)
        prev += size
    #calculate last size
    tone_info[-1].set_tone_data_size(header.info_table_absolute_offset - tone_info[-1].tone_data_absolute_offset)


def print_tone_info():
    for tone in tone_info:
        print(tone)

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def safe_open_w(path):
    #Open "path" for writing, creating any parent directories as needed.
    mkdir(os.path.dirname(path))
    return open(path, 'wb')

def extract_file(destination, start, size):
    #write each individual byte of a file, from the source, from the original, from original[start] to original[start+size]
    fo = safe_open_w("./" + destination)

    fi.seek(start, 0)

    for i in range(start, start+size):
        fo.write(fi.read(1))

    fo.close()

def unpack(dir):
    #takes each tone from tone_info and extracts it
    for tone in tone_info:
        destination = f"{dir}/{header.vac_file_source_str}/{tone.name} ({str(tone.sample_rate)} Hz).adpcm"
        start = tone.tone_data_absolute_offset
        size = tone.tone_data_size
        print(f"Extracting {destination} ...")
        extract_file(destination, start, size)

def traverse_input_dir(dir): # we store all the file names in this list
    filelist = []
    file_info = []

    for root, dirs, files in os.walk(dir):
    	for file in files:
            #append the file name to the list
    		filelist.append(os.path.join(root,file))

    # remove filesystem stuff we don't need and the containing directory

    for file in filelist:
        if not re.search("DS_Store", file) and file[-4:] == ".tla":
            file_info.append(file[len(dir):].replace("\\", "/"))
    return file_info

def main(input_dir):
    global fi

    for tla in traverse_input_dir(input_dir):

        fi = open(input_dir + "/" + tla, "rb")

        read_header()

        if "-v" in sys.argv:
            print(header)

        read_tone_info_table()

        if "-v" in sys.argv:
            print_tone_info()

        unpack(input_dir + re.search("^.*\/", tla).group(0)[:-1])

if __name__ == "__main__":

    if len(sys.argv) < 1 or sys.argv[1] == "-h":
        print("usage: FISH-tools.py [dir] \nwhere [dir] contains .tla files to unpack. [dir] is recursivley searched for sub-[dir]s containing .tla (i.e. sound/us/folder/file.tla)")
    else:
        main(sys.argv[1])
