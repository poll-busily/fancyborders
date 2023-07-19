from __future__ import print_function
from wand.image import Image
from wand.color import Color
from wand.font import Font
from wand.drawing import Drawing
from pathlib import Path

import argparse
import sys
import math
import os

border_bottom_pct = 0.025
#border_color = Color('#F7F6F3')
border_color = Color('#FFFFFF')
signature_color = Color('#898989')
# handwriting = Font('handwriting.ttf', color=signature_color)

parser = argparse.ArgumentParser(description='Add title and copyright to image for print')
parser.add_argument('path', type=str, help='Input file path (not modified in place)')
parser.add_argument('title', type=str, help='Image title (centered)')
parser.add_argument('year', type=str, default='',help='Year of shot')
parser.add_argument('--web', action='store_true', required=False, help='Create a smaller, lower quality product image')

def main():
    args = parser.parse_args()

    file_path = Path(args.path)
    filename = file_path.name
    filename_no_ext = filename.replace(file_path.suffix, '')
    output_filename = file_path.with_name(filename_no_ext + '_b.jpg')
    output_filename_web = file_path.with_name(filename_no_ext + '_b_sml.jpg')

    with Image(filename=file_path) as input_image:
        input_w = input_image.width
        input_h = input_image.height
        print(f"Input image: {filename} @ {input_w}x{input_h}")

        border_bottom_px = math.trunc((input_h + input_w) * border_bottom_pct)
        border_other_px = math.trunc(border_bottom_px * 0.55)
        print(f"Borders: {border_bottom_px}px at bottom, {border_other_px}px around")

        with input_image.clone() as output_image:
            output_image.border(border_color, int(border_other_px), int(border_bottom_px))
            output_image.crop(left=0, top = math.trunc(border_bottom_px * 0.6))

            # output_image.caption("Paul Beesley Photography",
            #                      gravity='south',
            #                      left=0,
            #                      top=math.trunc(output_image.height * 0.94),
            #                      font=handwriting,
            #                      width = math.trunc(input_image.width),
            #                      height= math.trunc(border_bottom_px * 0.65))

            with Drawing() as ctx:
                ctx.font = 'DejaVu Sans Oblique'
                ctx.font_family = 'DejaVu Sans'
                ctx.font_size = (input_w + input_h) * 0.006
                ctx.fill_color = signature_color
                ctx.gravity = "south"
                ctx.font_weight = 10
                output_image.annotate(args.title, ctx, 0, math.trunc(border_bottom_px * 0.39))

            with Drawing() as ctx2:
                ctx2.font = 'DejaVu Sans Oblique'
                ctx2.font_family = 'DejaVu Sans'
                ctx2.font_size = (input_w + input_h) * 0.0045
                ctx2.fill_color = signature_color
                ctx2.gravity = "south_west"
                ctx2.font_weight = 10
                output_image.annotate("Paul Beesley Landscape Photography", ctx2, border_other_px, math.trunc(border_bottom_px * 0.55))
                output_image.annotate("© " + args.year, ctx2, border_other_px, math.trunc(border_bottom_px * 0.31))

            output_image.compression_quality = 99
            output_image.format = 'jpeg'
            output_image.save(filename=output_filename)
            print(f"Saved full-size output to: {output_filename}")
            
            if (args.web):
                megapixels = 3
                pixels = megapixels * 1000000
                print(f"Resizing to {megapixels} megapixels ")
                output_image.transform('',f'{pixels}@')
                output_image.compression_quality = 65
                output_image.save(filename=output_filename_web)
                print(f"Saved small output to: {output_filename_web}")
                

if __name__ == "__main__":
    main()