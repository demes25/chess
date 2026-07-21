# Demetre Seturidze
# Chess
# Engine Setup

from netlib.filecaster import here, Path

from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension 

sources = [
    str(Path(here("src"), f"{filename}.cpp")) for filename in [
        "bindings"
    ]
]

ext_modules = [
    Pybind11Extension(
        "engine",
        sources=sources,
        cxx_std=20
    )
]

setup(
    name="engine",
    ext_modules=ext_modules,
)

