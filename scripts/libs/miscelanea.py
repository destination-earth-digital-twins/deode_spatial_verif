from glob import glob

def list_sorted_files(pattern):
    files = glob(pattern)
    files.sort()
    return files

def check_is_empty_dir(pattern):
    files = list_sorted_files(pattern)
    if len(files) > 0:
        return False
    else:
        return True

def str2bool(v):
    return v.lower() in ("yes", "true")
