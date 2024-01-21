"""
    Includes sphinx extensions useful for all robotpy projects
"""


def setup(app):
    from . import pybind11_fixer

    app.setup_extension(pybind11_fixer.__name__)
    app.setup_extension("sphinx_automodapi.smart_resolver")
    app.setup_extension(rtd_patch.__name__)
