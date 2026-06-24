# Demetre Seturidze
# Chess
# Tools -- for loading and manipulating assets

from typing import Tuple, Callable, Any
from files.media.schemes import Color
import pygame as pg
from pathlib import Path 

Sound = pg.mixer.Sound
Surface = pg.surface.Surface 

# iterates through files of the given extension, yields the file stem name and the path object.
# applies func before yielding if specified
def file_iter(dir : Path, ext : str, func : Callable[[Path], Any] | None = None):
    if func is None:
        for path in Path(dir).glob(f'*.{ext}'):
            yield (path.stem, path)
    else:
        for path in Path(dir).glob(f'*.{ext}'):
            yield (path.stem, func(path))

# iterates through all files with a given extension in the given directory and returns a dictionary of them,
# keyed by the 'stems' (i.e. extensionless names) of the files in question
def dict_from_dir(dir : Path, ext : str, func : Callable[[Path], Any] | None = None):
    return {name : obj for name, obj in file_iter(dir=dir, ext=ext, func=func)}

# creates a blank transparent surface of the given dimensions
def new_surface(dims : Tuple[int, int]):
    return Surface(dims, pg.SRCALPHA)

# returns a function that loads images and scales them to the given dimension
def surface_loader(dims : Tuple[int, int]):
    def _load(path : Path):
        return pg.transform.scale(pg.image.load(path), dims)
    return _load 

# tints an image in-place (and returns)
def tint(surface : Surface, color : Color | None = None, opacity : int = 255) -> Surface:
    if color is not None:
        surface.fill((*color, opacity), special_flags=pg.BLEND_RGBA_MULT)
    return surface

# Creates a copy where all visible pixels take on target_color.
# The original alpha channel is multiplied by alpha_scale.
def isolate_alpha_blend(surface : Surface, color : Color | None = None, opacity : int = 255):
    # 1. Copy the surface to preserve the original asset
    isolated = surface.copy()
    
    if color is not None:
         # 2. Zero out the RGB channels, leaving the original alpha intact
        isolated.fill((0, 0, 0, 255), special_flags=pg.BLEND_RGBA_MULT)

        # 3. Add your fixed color into the RGB channels (ignoring alpha for now)
        isolated.fill(color + (0,), special_flags=pg.BLEND_RGBA_ADD)
    
    # 4. Scale the alpha channel
    if opacity < 255:
        alpha_mask = pg.Surface(isolated.get_size(), pg.SRCALPHA)
        alpha_mask.fill((255, 255, 255, opacity))
        isolated.blit(alpha_mask, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
        
    return isolated

