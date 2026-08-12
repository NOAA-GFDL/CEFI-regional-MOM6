import errno
import os
from collections.abc import Iterable
from dataclasses import dataclass
from functools import singledispatch, singledispatchmethod
from getpass import getuser
from pathlib import Path
from shlex import quote
from shutil import which
from subprocess import DEVNULL, CompletedProcess, run
from typing import Any

import xarray
import yaml
from loguru import logger

from .types import PathLike


def _run_cmd(
    cmd: list[str], stdout: int = DEVNULL, stderr: int = DEVNULL
) -> CompletedProcess:
    """Replacement for subprocess.run to handle a few extra quirks.
    1. If a module is being loaded inline as part of the command using
    module load ... && cmd ..., we need to run this as a string in a login shell.
    To do that, in some cases the filename arguments need to be quoted
    (such as Filename (1).nc). In addition, tcsh (GFDL default) does this using -c,
    but bash and others use -lc.
    2. Default to sending all output to /dev/null, because hsmget writes verbose log
    messages to stderr even when told to be quiet.
    """
    if '&&' in cmd[0]:
        # quote arguments (file names), not the actual command
        quoted = map(quote, cmd[1:])
        cmd_str = f'{cmd[0]}  {" ".join(quoted)}'
        logger.debug('Rewrote cmd to: {c}', c=cmd_str)
        shell = os.environ.get('SHELL', '/bin/bash')
        logger.debug('Using shell: {s}', s=shell)
        flags = '-c' if 'csh' in shell else '-lc'
        res = run([shell, flags, cmd_str], check=True, stdout=stdout, stderr=stderr)
    else:
        res = run(cmd, check=True, stdout=stdout, stderr=stderr)
    return res


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
        res = which('hsmget')  # is hsmget already in path?
        if res is None:  # if it's not in path, try loading it
            possible_hsmget = Path('/home/fms/local/opt/hsm/1.3.0/bin/hsmget')
            if possible_hsmget.exists():
                # This seems to be the only way to get the module to stick
                res = f'module load hsm/1.3.0 && {possible_hsmget}'
                logger.info('Using hsmget with command {cmd}', cmd=res)
            else:
                logger.info(
                    'Not using hsmget. If running on GFDL analysis, run '
                    '`module load hsm/1.3.0` to enable using hsmget. '
                )
        # Check if hsmget was found, or found with a module load,
        # but the expected archive, ptmp, or tmp directories don't exist.
        if res is not None and not self._dirs_exist():
            logger.warning(
                'hsmget was found but archive, ptmp, and/or tmp were not. '
                'Check your paths. Not using hsmget.'
            )
            res = None
        return res

    @property
    def _hsmget_cmd(self) -> list[str]:
        if not isinstance(self._hsmget_str, str):
            raise TypeError('Unexpected hsmget command. Check if hsmget is in path.')
        return [
            self._hsmget_str,
            '-q',
            '-a',
            self.archive.as_posix(),
            '-w',
            self.tmp.as_posix(),
            '-p',
            self.ptmp.as_posix(),
        ]

    def _dirs_exist(self) -> bool:
        return self.archive.is_dir() and self.ptmp.is_dir() and self.tmp.is_dir()

    @singledispatchmethod
    def __call__(self, path: Any, **kwargs: Any) -> Any:
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
        logger.info('Retrieving {p} with hsmget', p=path.as_posix())
        relative = path.relative_to(self.archive).as_posix()
        # hsmget will do the dmget first and this is fine since it's one file
        _run_cmd([*self._hsmget_cmd, relative], **kwargs)
        return self.tmp / relative

    @__call__.register(list)
    def _call_path_list(self, paths: list[Path], **kwargs: Any) -> list[Path]:
        if self._hsmget_str is None:
            return paths
        logger.info('Retrieving {n} files with hsmget', n=len(paths))
        # dmget all files with one dmget command.
        _run_cmd(['dmget', *(p.as_posix() for p in paths)])
        relative = [p.relative_to(self.archive).as_posix() for p in paths]
        _run_cmd([*self._hsmget_cmd, *relative], **kwargs)
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
    logger.info('Looking for {var} in {pp_dir}', var=var, pp_dir=pp_dir)
    if not pp_dir.is_dir():
        raise FileNotFoundError(
            errno.ENOENT, 'Could not find post-processed directory', pp_dir.as_posix()
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
        logger.info(
            'Found {nf} files in {name} chunks', nf=len(matching_files), name=chunk.name
        )
        # Treat 1 and > 1 files separately, though the > 1 case
        # could probably handle both.
        # Include decode_timedelta=True to avoid FutureWarning
        if len(matching_files) > 1:
            tmpfiles = hsmget(sorted(matching_files))
            return xarray.open_mfdataset(tmpfiles, decode_timedelta=True)[var]
        elif len(matching_files) == 1:
            tmpfile = hsmget(matching_files[0])
            return xarray.open_dataset(tmpfile, decode_timedelta=True)[var]
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
