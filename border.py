# Copyright 2023, Paul Beesley
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
from typing import List
from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image

import anyconfig
import argparse
import logging
import math

parser = argparse.ArgumentParser(description='Give your image a lovely border with a title and creator info')
parser.add_argument('path', type=str, help='Input file path')
parser.add_argument('title', type=str, help='Image title')
parser.add_argument('year', type=str, default='',help='Copyright year')
parser.add_argument('--profiles', type=str, default=[], nargs='+',help='Which output profile(s) to run')

'''
Get the names of profiles from the command line args and load each .toml file
'''
def load_profiles(profile_list: List[str]):
    profiles = []

    for profile_name in profile_list:
        profile = anyconfig.load(f"profiles/{profile_name}.toml")
        profiles.append(profile)
    
    if not profile_list:
        logging.warning('Using default profile as none was specified')
        profile_default = anyconfig.load("profiles/default.toml")
        profiles.append(profile_default)

    return profiles


'''
Processes the input image and produces a bordered output image according to profile settings
'''
def run_profile(profile, args):
    logging.info(f"Running profile: {profile['name']}")

    file_path = Path(args.path)
    logging.info(f'\tInput image:{file_path}')
    filename = file_path.name
    # This strips the extension (e.g. .jpg) and adds the chosen suffix (e.g. _b) but the output extension
    # is not added until later
    filename_with_suffix = filename.replace(file_path.suffix, f'{profile["output"]["suffix"]}')

    with Image(filename=file_path) as input_image:
        input_w = input_image.width
        input_h = input_image.height
        logging.info(f"\tInput resolution: {input_w}x{input_h}")

        # Compute the absolute pixel values for the bottom border (which may be thicker) and for the other three borders
        border_bottom_px = math.trunc((input_h + input_w) * profile['border']['bottom_scale'])
        border_other_px = math.trunc((input_h + input_w) * profile['border']['top_side_scale'])
        logging.debug(f"\tBorders: {border_bottom_px}px at bottom, {border_other_px}px around")

        # The input image is cloned to avoid manipulating the input file
        with input_image.clone() as output_image:
            output_image.border(profile['border']['color'], int(border_other_px), int(border_bottom_px))
            output_image.crop(left=0, top = math.trunc(border_bottom_px * 0.5)) # The top border will be the same as the bottom otherwise

            # Write the image title, centered
            with Drawing() as ctx:
                ctx.font = profile['font']['name']
                ctx.font_family = profile['font']['family']
                ctx.font_size = (input_w + input_h) * profile['font']['scale_factor_title']
                ctx.fill_color = Color(profile['font']['color'])
                ctx.gravity = "south"
                ctx.font_weight = profile['font']['weight']
                output_image.annotate(args.title, ctx, 0, math.trunc(border_bottom_px * 0.39))

            # TODO: It's probably possible to re-use the existing drawing context above...
            # Write the photographer name and copyright fields, bottom-left
            with Drawing() as ctx2:
                ctx2.font = profile['font']['name']
                ctx2.font_family = profile['font']['family']
                ctx2.font_size = (input_w + input_h) * profile['font']['scale_factor_metadata']
                ctx2.fill_color = Color(profile['font']['color'])
                ctx2.gravity = "south_west"
                ctx2.font_weight = profile['font']['weight']
                output_image.annotate(profile['author']['name'], ctx2, border_other_px, math.trunc(border_bottom_px * 0.55))
                output_image.annotate("© " + args.year, ctx2, border_other_px, math.trunc(border_bottom_px * 0.31))

            # Scale the output if resizing was requested
            if (profile['resize']['enable']):
                logging.info(f"\tResizing to {profile['resize']['megapixels']} megapixels ")
                pixels = profile['resize']['megapixels'] * 1000000
                input_pixels = input_w * input_h
                if input_pixels < pixels:
                    logging.warning('\t\tInput image is smaller than output - you are scaling up!')
                output_image.transform('',f'{pixels}@')

            match profile['output']['codec']:
                case 'jpeg':
                    output_image.compression_quality = int(profile['output']['quality'])
                    output_image.format = 'jpeg'
                    output_path = file_path.with_name(filename_with_suffix + '.jpg')
                case 'png':
                    output_image.format = 'png'
                    output_path = file_path.with_name(filename_with_suffix + '.png')
                case 'tiff':
                    output_image.format = 'tiff'
                    output_path = file_path.with_name(filename_with_suffix + '.tif')
                case _:
                    logging.warning("\tUnrecognised output format: using PNG")
                    output_image.format = 'png'
                    output_path = file_path.with_name(filename_with_suffix + '.png')
            
            logging.info(f'\tOutput image:{output_path}')
            output_image.save(filename=output_path)
            logging.info(f'\tSaved output image successfully')


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    # Read command line args then load specified profile files
    args = parser.parse_args()
    profiles = load_profiles(args.profiles)

    # Each loaded profile is run once on the input image
    for profile in profiles:
        run_profile(profile, args)
            
    logging.info("All done!")

if __name__ == "__main__":
    main()