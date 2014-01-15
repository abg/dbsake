#!/usr/bin/env python
from __future__ import print_function
import io
import os
import stat
import sys
import zipfile

def main():
    sink = io.BytesIO()
    print("Generating executable archive", file=sys.stderr)
    print(b"#!/usr/bin/env python     ", file=sink)
    archive = zipfile.ZipFile(file=sink,
                              mode='w',
                              compression=zipfile.ZIP_DEFLATED)
    archive.writestr("__main__.py", 
                     b"import sys\nsys.exit(__import__('dbsake').main())\n")
    
    basename = os.path.basename
    for dirpath, dirnames, filenames in os.walk('dbsake'):
        for name in filenames:
            if not name.endswith('.py') and basename(dirpath) != 'templates':
                 continue
            archive.write(os.path.join(dirpath, name))
    archive.close()

    with open('dbsake.zip', 'wb') as fileobj:
        os.fchmod(fileobj.fileno(), stat.S_IXUSR|stat.S_IRUSR|stat.S_IWUSR)
        fileobj.write(sink.getvalue())
    print("Executable created at ./dbsake.zip", file=sys.stderr)
        
if __name__ == '__main__':
    sys.exit(main())
