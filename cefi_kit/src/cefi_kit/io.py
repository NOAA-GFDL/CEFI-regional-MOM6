import errno
import logging
import os
import re
import yaml

import xarray
from pathlib import Path
from subprocess import run, DEVNULL
from shutil import which
from getpass import getuser
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# hsmget, available on GFDL PPAN, will make it faster, easier, and safer
# to read data from /archive.
# To use this, run `module load hsm/1.3.0` beforehand.
@dataclass
class HSMGet:
    archive: Path = Path('/') # this will duplicate paths used by frepp
    ptmp: Path = Path('/ptmp') / getuser()
    tmp: Path = Path(os.environ.get('TMPDIR', ptmp))

    def _run(self, cmd, stdout=DEVNULL, stderr=DEVNULL):
        # This will escape things like (1) in the file name
        # so that it can be run as a shell command.
        esc = re.sub(r'([\(\)])', r'\\\1', cmd)
        return run(esc, shell=True, check=True, stdout=stdout, stderr=stderr)

    def _dirs_exist(self):
        return self.archive.is_dir() and self.ptmp.is_dir() and self.tmp.is_dir()

    def __call__(self, path_or_paths):
        if which('hsmget') is None or not self._dirs_exist():
            # If hsmget or /archive, /ptmp, etc are not available, this will just return the input path(s).
            logger.info('Not using hsmget. If running on GFDL analysis, run `module load hsm/1.3.0` to enable using hsmget. ')
            return path_or_paths
        elif isinstance(path_or_paths, Path):
            # Find the file path on archive, relative to the root part of archive.
            # (This is how hsmget will want it).
            relative = path_or_paths.relative_to(self.archive)
            # hsmget will do the dmget first and this is fine since it's one file
            cmd = f'hsmget -q -a {self.archive} -w {self.tmp} -p {self.ptmp} {relative}'
            self._run(cmd)
            return (self.tmp / relative)
        elif iter(path_or_paths):
            # dmget all files with one dmget command.
            p_str = ' '.join([p.as_posix() for p in path_or_paths])
            self._run(f'dmget {p_str}')
            relative = [p.relative_to(self.archive) for p in path_or_paths]
            rel_str = ' '.join(map(str, relative))
            cmd = f'hsmget -q -a {self.archive} -w {self.tmp} -p {self.ptmp} {rel_str}'
            self._run(cmd)
            return [self.tmp / r for r in relative]
        else:
            raise Exception('Need a Path or iterable of Paths to get')


def open_var(pp_root, kind, var, hsmget=HSMGet()):
    if isinstance(pp_root, str):
        pp_root = Path(pp_root)
    freq = 'daily' if 'daily' in kind else 'monthly'
    pp_dir = pp_root / 'pp' / kind / 'ts' / freq
    if not pp_dir.is_dir():
        raise FileNotFoundError(errno.ENOENT, 'Could not find post-processed directory', str(pp_dir))
    # Get all of the available post-processing chunk directories (assuming chunks in units of years)
    available_chunks = list(pp_dir.glob('*yr'))
    if len(available_chunks) == 0:
        raise FileNotFoundError(errno.ENOENT, 'Could not find post-processed chunk subdirectory')
    # Sort from longest to shortest chunk
    sorted_chunks = sorted(available_chunks, key=lambda x: int(x.name[0:-2]), reverse=True)
    for chunk in sorted_chunks:
        # Look through the available chunks and return for the
        # largest chunk that has file(s).
        matching_files = list(chunk.glob(f'{kind}.*.{var}.nc'))
        # Treat 1 and > 1 files separately, though the > 1 case could probably handle both.
        if len(matching_files) > 1:
            tmpfiles = hsmget(sorted(matching_files))
            return xarray.open_mfdataset(tmpfiles, decode_timedelta=True)[var] # Avoid FutureWarning about decode_timedelta
        elif len(matching_files) == 1:
            tmpfile = hsmget(matching_files[0])
            return xarray.open_dataset(tmpfile, decode_timedelta=True)[var] # Avoid FutureWarning about decode_timedelta
    else:
        raise FileNotFoundError(errno.ENOENT, 'Could not find any post-processed files. Check if frepp failed.')


def load_config(config_path: str):
    """Load the configuration file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {e}")
        raise