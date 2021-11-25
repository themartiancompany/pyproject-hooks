from __future__ import absolute_import, division, unicode_literals

import re

import pytest

from pep517 import meta

pep517_needs_python_3 = pytest.mark.xfail(
    'sys.version_info < (3,)',
    reason="pep517 cannot be built on Python 2",
)


def test_meta_for_this_package():
    dist = meta.load('.')
    assert re.match(r'[\d.]+', dist.version)
    assert dist.metadata['Name'] == 'pep517'


def test_classic_package(tmpdir):
    (tmpdir / 'setup.py').write_text(
        'from distutils.core import setup; setup(name="foo", version="1.0")',
        encoding='utf-8',
    )
    dist = meta.load(str(tmpdir))
    assert dist.version == '1.0'
    assert dist.metadata['Name'] == 'foo'


def test_meta_output(capfd):
    """load shouldn't emit any output"""
    meta.load('.')
    captured = capfd.readouterr()
    assert captured.out == captured.err == ''
