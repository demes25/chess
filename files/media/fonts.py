# Demetre Seturidze
# Chess
# Alphabets

from typing import Tuple, Dict, List 
from pathlib import Path 
import pygame as pg 
from files.media.tools import Surface, new_surface, isolate_alpha_blend
from files.media.schemes import Color 
from collections import UserDict


# we load an ALPHABET, as well as some additional metadata.
# the alphabet MUST be monospaced and have a set size ratio. 
class Alphabet(UserDict):
    ASCII = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
    ASCII_COUNT = len(ASCII)

    # saves a template for the given font size, includes divisors if so wanted
    # the general font template 
    @staticmethod
    def template(pixels : Tuple[int, int], include_placeholders : bool = True, path : str | Path | None = None) -> Surface:
        width, height = pixels 
        total_width = width * Alphabet.ASCII_COUNT

        template = new_surface((total_width, height))

        if include_placeholders:
            # creates a default placeholder
            placeholder = new_surface(pixels)

            single_pixel = new_surface((1, 1))
            single_pixel.fill((127, 127, 127))

            Y_VAL = height-1

            for X_VAL in range(width-1):
                placeholder.blit(single_pixel, (X_VAL, Y_VAL))
                
            placeholder.blit(single_pixel, (0, Y_VAL-1))

            for X_VAL in range(0, total_width, width):
                template.blit(placeholder, (X_VAL, 0))
        
        if path is not None:
            pg.image.save(template, path)

        return template 


    def __init__(
        self, 
        path : str | Path, # the file name of the font file. should be an image with dimensions (font_width * 95, font_height)
                           # which is a contiguous image of all writable symbols in ASCII.
    ):  
        # we load the font image
        font_image = pg.image.load(path)
        font_rect = font_image.get_rect()

        # find the dimensions of each letter

        font_height = self.pixel_height = font_rect.height 

        # if the font_width is not a multiple of 95, this does not fit our requirements
        if font_rect.width % Alphabet.ASCII_COUNT != 0:
            raise Exception('Alphabet image width must be a multiple of 95.')
        
        font_width = self.pixel_width = font_rect.width//Alphabet.ASCII_COUNT


        # store the specs per-letter
        self.pixels = (font_width, font_height) # the dimensions of the font, in pixels.

        # the rect which we will use to parse the letters of the alphabet
        letter_rect = pg.rect.Rect(0, 0, font_width, font_height)

        super().__init__()

        # we store the alphabet
        for char in Alphabet.ASCII:
            self.data[char] = font_image.subsurface(letter_rect)    
            letter_rect.left += font_width

    
    def __setitem__(self, _, __):
        raise Exception('Alphabet objects are immutable.')
    

    def get_scaled(
        self,
        pixels : Tuple[int, int] | None, # pixel-dimensions height of each letter
    ) -> Dict[str, Surface]:
        
        if pixels is None:
            return self.data.copy()
        else:    
            return {
                char : pg.transform.scale(letter, size=pixels) for char, letter in self.items()
            }
        
    

# carries an instance of alphabet which is colored and sized in some way.
class Font(UserDict):
    def __init__(
        self,
        alphabet_or_path : str | Path | Alphabet, # the alphabet object or the path to its generating image
        fontsize : int, # pixel height of each letter
    ):
        
        super().__init__()

        if isinstance(alphabet_or_path, Alphabet): 
            self.alphabet = alphabet_or_path
        else:
            self.alphabet = Alphabet(alphabet_or_path)

        self.set(
            fontsize=fontsize
        )
    
    def __setitem__(self, _, __):
        raise Exception('Font entries are immutable.')
    
    def set(
        self,
        fontsize : int
    ):  
        self.pixel_height = fontsize
        self.pixel_width = (self.alphabet.pixel_width * fontsize) // self.alphabet.pixel_height
        
        self.pixels = (self.pixel_width, self.pixel_height)

        self.gap_size = fontsize // self.alphabet.pixel_height # we leave gaps, equivalent to one alphabet-pixel in between.

        self.data = self.alphabet.get_scaled(pixels=self.pixels)

    
    def render(
        self,
        text : str,
        color : Color | None = None,
        opacity : int = 255,
        background_color : Color | None = None
    ):
        
        letter_and_gap = self.pixel_width + self.gap_size
        width = letter_and_gap * len(text) - self.gap_size
        surface = new_surface(dims=(width, self.pixel_height))

        X = 0

        for char in text:
            surface.blit(self[char], (X, 0))
            X += self.pixel_width + self.gap_size
        
        surface = isolate_alpha_blend(surface=surface, color=color, opacity=opacity)

        if background_color is not None:
            background = new_surface(dims=(width, self.pixel_height))
            background.fill(background_color)
            background.blit(surface, (0, 0))
            return background
        
        else:
            return surface
    
    
    def as_lines(self, text : str, letters_per_line : int) -> List[str]:
        lines = []

        while text != '':
            if len(text) > letters_per_line:
                candidate = text[:letters_per_line]
                text = text[letters_per_line:]
            else:
                candidate = text
                text = ''

            if '\n' in candidate:
                candidate, remainder = candidate.split('\n', maxsplit=1)

                text = remainder + text 
            elif len(text) > 0:
                if text[0] == ' ':
                    text = text[1:]
                elif len(candidate) > 0:
                    for i in range(len(candidate)-1, 0, -1):
                        if candidate[i] == ' ':
                            text = candidate[i+1:] + text
                            candidate = candidate[:i]
                            break
            
            if len(text) > 0 or len(candidate) > 0:
                lines.append(candidate)
        
        return lines

       
        
# carries a buffer that dynamically writes onto a fixed-width object.
class TextEntry:
    def __init__(
        self, 
        font : Font, 
        pixel_width : int, # a fixed width for the font environment

        color : Color | None = None,
        opacity : int = 255
    ):
        self.letter_width = (pixel_width // (font.pixel_width + font.gap_size))
        self.pixel_width =  self.letter_width * (font.pixel_width + font.gap_size)

        self.font = font 

        self.string : str = ''
        
        self.pointer = 0
        self.pointer_coords = (0, 0)

        self.lengths = []

        self.surface = new_surface((self.pixel_width, self.pixel_height))

        self.color = color 
        self.opacity = opacity
    
    @property
    def pixel_height(self) -> int:
        return max(len(self.lengths), 1) * (self.font.pixel_height + self.font.gap_size) - self.font.gap_size

    def pointer_to_coord(self, pointer : int) -> Tuple[int, int]:
        y_coord = 0

        for l in self.lengths:
            if pointer > l:
                pointer -= l
                y_coord += self.font.pixel_height + self.font.gap_size
        
        x_coord = pointer * (self.font.pixel_width + self.font.gap_size) - self.font.gap_size

        return (x_coord, y_coord)

    def coord_to_pointer(self, coords : Tuple[int, int]):
        x_coord, y_coord = coords

        height = y_coord // (self.font.pixel_height + self.font.gap_size)

        pointer = x_coord // (self.font.pixel_width + self.font.gap_size)
        if height > 0:
            pointer += sum(self.lengths[:height])


    def update(self):
        lines = self.font.as_lines(self.string, self.letter_width)
        self.lengths = [len(line) for line in lines]

        Y = 0
        surface = new_surface((self.pixel_width, self.pixel_height))

        for line in lines:
            surface.blit(
                self.font.render(line), (0, Y)
            )
            Y += (self.font.pixel_height + self.font.gap_size)

        self.surface = isolate_alpha_blend(surface, color=self.color, opacity=self.opacity)

    def register(self, event : pg.event.Event):
        if event.type == pg.TEXTINPUT:
            text = event.text
            
            self.string = self.string[:self.pointer] + text + self.string[self.pointer:]
            self.pointer += len(text)

            self.update()


        elif event.type == pg.KEYDOWN and event.key == pg.K_BACKSPACE and self.pointer > 0:
            remainder = self.string[self.pointer:]
            self.pointer -= 1

            self.string = self.string[:self.pointer] + remainder

            self.update()
    

    def register_text(self, text : str):
        self.string = self.string[:self.pointer] + text + self.string[self.pointer:]
        self.pointer += len(text)

        self.update()


class TextRecord:
    def __init__(
        self, 
        font : Font,
        pixel_width : int, # a fixed width for the environment
        text_gap_ratio : float = 5.0 # the ratio of the gap between texts to the gap between lines
    ):
        self.letter_width = (pixel_width // (font.pixel_width + font.gap_size))
        
        self.pixel_width =  self.letter_width * (font.pixel_width + font.gap_size)
        self.pixel_height = 0

        self.surface = new_surface((self.pixel_width, font.pixel_height))
        self.font = font 

        self._additional_gap = int(text_gap_ratio*font.gap_size)


    def register(self, string : str, color : Color | None = None, opacity : int = 255):
        lines = self.font.as_lines(string, letters_per_line=self.letter_width)

        height_per_letter = self.font.pixel_height + self.font.gap_size

        add_height = len(lines) * height_per_letter + self._additional_gap

        current_height = self.pixel_height
        updated_surface = new_surface((self.pixel_width, self.pixel_height + add_height))

        if current_height != 0:
            updated_surface.blit(self.surface, (0, 0))
        
        for line in lines:
            line_surface = self.font.render(line, color=color, opacity=opacity)

            updated_surface.blit(line_surface, (0, current_height))
            current_height += height_per_letter

        self.surface = updated_surface
        self.pixel_height += add_height
            
        



