# fish-tools
unpacking script for the Melbourne House "FISH" Tone Library file format used in Test Drive Unlimited

### usage: 
>python3 FISH-tools.py [dir] 

where [dir] contains .tla files to unpack. [dir] is recursivley searched for sub-[dir]s containing .tla (i.e. sound/us/folder/file.tla)

### Description:
This tool is designed to unpack the .tla "ToneLibraryArchive"(?)
format used by Melbourne House/Atari for the PS2 and PSP versions of
Test Drive Unlimited.
    
### Editorial notes:
The PSP and PS2 disc images of TDU contain a packaged file format \*.PCK
with a "file magic" of "MHPF". 

\*.TLA files have a magic signature of
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

