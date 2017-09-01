from contextlib import contextmanager
import io
import json
import os
from os.path import dirname, abspath, join as pjoin
import pytoml
import shutil
from subprocess import check_call
import sys
from tempfile import mkdtemp

from . import compat

_in_proc_script = pjoin(dirname(abspath(__file__)), '_in_process.py')

@contextmanager
def tempdir():
    td = mkdtemp()
    try:
        yield td
    finally:
        shutil.rmtree(td)

class UnsupportedOperation(Exception):
    """May be raised by build_sdist if the backend indicates that it can't."""

class Pep517HookCaller(object):
    def __init__(self, source_dir):
        self.source_dir = source_dir
        with open(pjoin(source_dir, 'pyproject.toml')) as f:
            self.pyproject_data = pytoml.load(f)
        buildsys = self.pyproject_data['build-system']
        self.build_sys_requires = buildsys['requires']
        self.build_backend = buildsys['build-backend']

    def get_requires_for_build_wheel(self, config_settings):
        return self._call_hook('get_requires_for_build_wheel', {
            'config_settings': config_settings
        })

    def prepare_metadata_for_build_wheel(self, metadata_directory, config_settings):
        return self._call_hook('prepare_metadata_for_build_wheel', {
            'metadata_directory': metadata_directory,
            'config_settings': config_settings,
        })

    def build_wheel(self, wheel_directory, config_settings, metadata_directory=None):
        return self._call_hook('build_wheel', {
            'wheel_directory': wheel_directory,
            'config_settings': config_settings,
            'metadata_directory': metadata_directory,
        })

    def get_requires_for_build_sdist(self, config_settings):
        return self._call_hook('get_requires_for_build_sdist', {
            'config_settings': config_settings
        })

    def build_sdist(self, sdist_directory, config_settings):
        return self._call_hook('build_sdist', {
            'sdist_directory': sdist_directory,
            'config_settings': config_settings,
        })


    def _call_hook(self, hook_name, kwargs):
        env = os.environ.copy()
        env['PEP517_BUILD_BACKEND'] = self.build_backend
        with tempdir() as td:
            compat.write_json({'kwargs': kwargs}, pjoin(td, 'input.json'),
                              indent=2)

            # Run the hook in a subprocess
            check_call([sys.executable, _in_proc_script, hook_name, td],
                       cwd=self.source_dir, env=env)

            data = compat.read_json(pjoin(td, 'output.json'))
            if data.get('unsupported'):
                raise UnsupportedOperation
            return data['return_val']

