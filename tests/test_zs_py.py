from zs import __version__

from zs.text.token_info_lib import Identifier


def test_version():
    assert __version__ == '0.1.0'


def test_identifier():
    Identifier(None)
