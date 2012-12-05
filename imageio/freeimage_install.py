# -*- coding: utf-8 -*-

""" This module contains the code for loading the freeimage library,
and downloading it when necessary.

"""

import os
import sys
import shutil
try:
    from urllib2 import urlopen
except ImportError:
    try:
        from urllib.request import urlopen # Py3k
    except ImportError:
        # If we cannot import this, there is still a chance things work
        # Sometimes this happens when frozen because cannot import email
        urlopen = None 

LOCALDIR = os.path.abspath(os.path.dirname(__file__))

# Where to get the downloadable files
# Note that we hardcode the filenames. In theory we could make a text file
# that lists the most up-to-date libraries, but the current approach is
# much easier, and its probably enough to just change the filenames to
# the latest libs available at each release.
BASE_ADDRESS = 'http://bitbucket.org/almarklein/imageio/downloads/'

FILES = ['README.txt', 'FreeImage-License.txt']

LIBRARIES = {
    ('darwin', 32): 'libfreeimage-3.15.1-osx10.6.dylib',
    ('darwin', 64): 'libfreeimage-3.15.1-osx10.6.dylib',
    ('win32', 32): 'FreeImage-3.15.1-win32.dll',
    ('win32', 64): 'FreeImage-3.15.1-win64.dll'
}

def _download(url, dest, timeout=20):
    print('Downloading: %s' % url)
    dest_f = open(dest, 'wb')
    # Open connection
    try:
        remote = urlopen(url, timeout=timeout)
    except TypeError:
        raise RuntimeError('urlopen not available.')
    except IOError:
        dest_f.close()
        os.remove(dest)
        raise RuntimeError('Could not find %s.' % url)
    # Download
    try:
        shutil.copyfileobj(remote, dest_f)
    except:
        dest_f.close()
        os.remove(dest)
        raise RuntimeError('Could not download %s to %s.' %(url, dest))
    finally:
        remote.close()
    # Close local file
    dest_f.flush()
    dest_f.close()


def get_key_for_available_lib(bits=None):
    """ Get key (platform, bits) for the current system.
    Returns None if there is no downloadable lib for this key.
    """
    if bits is None:
        bits = 64 if sys.maxsize > 2**32 else 32
    key = (sys.platform, bits)
    if key in LIBRARIES:
        return key
    else:
        return None


def retrieve_files(lib_dir, selection=None):
    """ Make sure the freeimage lib is present. It is downloaded
    if necessary. If selection is None, will retreieve only what is needed
    for this system. If selection is 32 or 64, will download that version
    of the library, for this system. If selection is 'all', will download
    *all* available binaries.
    
    """
    # Check
    bits = None
    if selection in [32,64]:
        bits = selection
    elif selection in [None, 'all']:
        pass
    else:
        raise ValueError("Invalid value for selection: must be None, 32, 64 or 'all'.")
    
    if selection == 'all':
        # We want to download all files
        files = list(FILES)
        for key, library in LIBRARIES.items():
            files.append(library)
    else:
        # We only want to download the one for this system
        key = get_key_for_available_lib(bits)
        if key is None:
            # Silent return. It is up to the caller to check and raise if necessary
            return
        library = LIBRARIES[key]
        print('Found: %s for %d-bit %s systems at %s' % (library, key[1], 
                key[0], BASE_ADDRESS))
        # Select files to download
        files = list(FILES)
        files.append(library)
    
    # Download all files and put them in the lib dir
    for fname in files:
        src = BASE_ADDRESS+fname
        dest = os.path.join(lib_dir, fname)
        if not os.path.exists(dest):
            _download(src, dest)


# Store some messages as constants
MSG_NOLIB_DOWNLOAD = 'Attempting to download the FreeImage library.'
MSG_NOLIB_LINUX = 'Install FreeImage (libfreeimage3) via your package manager or build from source.'
MSG_NOLIB_OTHER = 'Please install the FreeImage library.'


def load_freeimage():
    """ Load the freeimage libraray. If it cannot be found, will attempt
    to download it and then try again.
    """
    # Lazy imports, so that this module can be imported as a loose module
    # (by setup.py) as long as this function is not called.
    from imageio.findlib import load_lib
    from imageio.freeze import resource_dir
    
    # Get lib dirs
    lib_dir = resource_dir('imageio', 'lib')
    lib_dirs = [lib_dir, resource_dir('imageio', '')]
    
    # Load library
    lib_names = ['freeimage', 'libfreeimage']
    exact_lib_names = ['FreeImage', 'libfreeimage.dylib', 
                        'libfreeimage.so', 'libfreeimage.so.3']
    
    try:
        lib, fname = load_lib(exact_lib_names, lib_names, lib_dirs)
    except OSError:
        # Could not load. Get why
        e_type, e_value, e_tb = sys.exc_info(); del e_tb
        load_error = str(e_value)
        # Can we download? If not, raise error.
        if get_key_for_available_lib() is None:
            if sys.platform.startswith('linux'):
                err_msg = load_error + '\n' + MSG_NOLIB_LINUX
            else:
                err_msg = load_error + '\n' + MSG_NOLIB_OTHER
            raise OSError(err_msg)
        # Yes, it seems so! Try it and then try loading again
        print(load_error + '\n' + MSG_NOLIB_DOWNLOAD)
        retrieve_files(lib_dir)
        lib, fname = load_lib(exact_lib_names, lib_names, lib_dirs)
        # If we get here, we did a good job!
        print('FreeImage library deployed succesfully.')
    
    # Return library and the filename where it's loaded
    return lib, fname


if __name__ == '__main__':
    # Retieve *all* downloadable libraries
    from imageio.freeze import resource_dir
    retrieve_files(resource_dir('imageio', 'lib'), 'all')