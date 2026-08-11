import errno
import logging
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from functools import singledispatch, singledispatchmethod
from getpass import getuser
from pathlib import Path
from shutil import which
from subprocess import DEVNULL, CompletedProcess, run
from typing import Any

import xarray
import yaml

from .types import PathLike

logger = logging.getLogger(__name__)


# hsmget, available on GFDL PPAN, will make it faster, easier, and safer
# to read data from /archive.
# To use this, run `module load hsm/1.3.0` beforehand.
@dataclass
class HSMGet:
    archive: Path = Path('/')  # this will duplicate paths used by frepp
    ptmp: Path = Path('/ptmp') / getuser()
    tmp: Path = Path(os.environ.get('TMPDIR', ptmp))

    @property
    def _hsmget_str(self) -> str | None:
        res = which('hsmget')
        if res is None:
            possible_hsmget = Path('/home/fms/local/opt/hsm/1.3.0/bin/hsmget')
            if possible_hsmget.exists():
                # This seems to be the only way to get the module to stick
                res = f'module load hsm/1.3.0 && {possible_hsmget}'
            else:
                logger.info(
                    'Not using hsmget. If running on GFDL analysis, run '
                    '`module load hsm/1.3.0` to enable using hsmget. '
                )
        if res is not None and not self._dirs_exist():
            logger.warning(
                'hsmget was found but archive, ptmp, and/or tmp were not. '
                'Check your paths. Not using hsmget.'
            )
            res = None
        return res

    def _dirs_exist(self) -> bool:
        return self.archive.is_dir() and self.ptmp.is_dir() and self.tmp.is_dir()

    def _run(
        self, cmd: str, stdout: int = DEVNULL, stderr: int = DEVNULL
    ) -> CompletedProcess:
        # This will escape things like (1) in the file name
        # so that it can be run as a shell command.
        esc = re.sub(r'([\(\)])', r'\\\1', cmd)
        return run(esc, shell=True, check=True, stdout=stdout, stderr=stderr)

    @singledispatchmethod
    def __call__(self, path_or_paths: Any, **kwargs: Any) -> Any:
        raise TypeError(
            'Unsupported type for path to hsmget. Expected str, Path, or list[Path]'
        )

    @__call__.register
    def _call_str(self, path: str, **kwargs: Any) -> Path:
        cast_path = Path(path)
        return self.__call__(cast_path, **kwargs)

    @__call__.register
    def _call_path(self, path: Path, **kwargs: Any) -> Path:
        if self._hsmget_str is None:
            return path
        relative = path.relative_to(self.archive)
        # hsmget will do the dmget first and this is fine since it's one file
        cmd = (
            f'{self._hsmget_str} -q -a {self.archive} -w {self.tmp} -p {self.ptmp} '
            f'{relative}'
        )
        self._run(cmd, **kwargs)
        return self.tmp / relative

    @__call__.register(list)
    def _call_path_list(self, paths: list[Path], **kwargs: Any) -> list[Path]:
        if self._hsmget_str is None:
            return paths
        # dmget all files with one dmget command.
        p_str = ' '.join([p.as_posix() for p in paths])
        self._run(f'dmget {p_str}')
        relative = [p.relative_to(self.archive) for p in paths]
        rel_str = ' '.join(map(str, relative))
        cmd = (
            f'{self._hsmget_str} -q -a {self.archive} -w {self.tmp} -p {self.ptmp} '
            f'{rel_str}'
        )
        self._run(cmd, **kwargs)
        return [self.tmp / r for r in relative]

    @__call__.register(Iterable)
    def _call_path_iterable(self, paths: Iterable[Path], **kwargs: Any) -> list[Path]:
        cast_paths = list(paths)
        return self.__call__(cast_paths, **kwargs)


_hsmget = HSMGet()


@singledispatch
def open_var(
    pp_root: Any, kind: str, var: str, hsmget: HSMGet = _hsmget
) -> xarray.DataArray:
    raise TypeError('Unsupported type for pp_root. Expected Path or Iterable[Path]')


@open_var.register
def _open_var_pathlike(
    pp_root: PathLike | str, kind: str, var: str, hsmget: HSMGet = _hsmget
) -> xarray.DataArray:
    freq = 'daily' if 'daily' in kind else 'monthly'
    pp_dir = Path(pp_root) / 'pp' / kind / 'ts' / freq
    if not pp_dir.is_dir():
        raise FileNotFoundError(
            errno.ENOENT, 'Could not find post-processed directory', str(pp_dir)
        )
    # Get all of the available post-processing chunk directories
    # (assuming chunks in units of years)
    available_chunks = list(pp_dir.glob('*yr'))
    if len(available_chunks) == 0:
        raise FileNotFoundError(
            errno.ENOENT, 'Could not find post-processed chunk subdirectory'
        )
    # Sort from longest to shortest chunk
    sorted_chunks = sorted(
        available_chunks, key=lambda x: int(x.name[0:-2]), reverse=True
    )
    for chunk in sorted_chunks:
        # Look through the available chunks and return for the
        # largest chunk that has file(s).
        matching_files = list(chunk.glob(f'{kind}.*.{var}.nc'))
        # Treat 1 and > 1 files separately, though the > 1 case
        # could probably handle both.
        if len(matching_files) > 1:
            tmpfiles = hsmget(sorted(matching_files))
            return xarray.open_mfdataset(tmpfiles, decode_timedelta=True)[
                var
            ]  # Avoid FutureWarning about decode_timedelta
        elif len(matching_files) == 1:
            tmpfile = hsmget(matching_files[0])
            return xarray.open_dataset(tmpfile, decode_timedelta=True)[
                var
            ]  # Avoid FutureWarning about decode_timedelta
    raise FileNotFoundError(
        errno.ENOENT,
        'Could not find any post-processed files. Check if frepp failed.',
    )


@open_var.register(Iterable)
def _open_var_pathiterable(
    pp_root: Iterable[PathLike],
    kind: str,
    var: str,
    hsmget: HSMGet = _hsmget,
    concat_dim: str = 'time',
) -> xarray.DataArray:
    """For an iterable of post-processed paths, open each separately and concat."""
    return xarray.concat(
        [open_var(p, kind, var, hsmget=hsmget) for p in pp_root], dim=concat_dim
    )


def load_config(config_path: PathLike) -> Any:
    """Load the configuration file."""
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            logger.info(f'Loaded configuration from {config_path}')
            return config
    except Exception as e:
        logger.error(f'Error loading configuration from {config_path}: {e}')
        raise
