import glob
import os
import shutil
import zipfile


def extract_zipfile(name, subdir='files'):
    if os.path.isfile(name) and zipfile.is_zipfile(name):
        zf = zipfile.ZipFile(name, 'r')
        target_path = os.path.join(os.path.dirname(name), subdir)
        # clean directory
        abs_path = os.path.abspath(target_path)
        if os.path.exists(abs_path):
            shutil.rmtree(abs_path)
        os.makedirs(abs_path)
        zf.extractall(abs_path)
        return abs_path


def zipfile_find_file(file, ext):
    with zipfile.ZipFile(file, 'r') as zipObj:
        for elem in zipObj.namelist():
            if elem.endswith('.%s' % ext):
                return elem


def find_file(dir, ext):
    if dir is None:
        raise Exception("Invalid directory")
    files = glob.glob('%s/*.%s' % (dir, ext))
    return files[0]
