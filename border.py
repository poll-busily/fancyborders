# Copyright 2023, Paul Beesley
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image

import anyconfig
import argparse
import logging
import math

confs = []

parser = argparse.ArgumentParser(description='Add title and copyright to image for print')
parser.add_argument('path', type=str, help='Input file path (not modified in place)')
parser.add_argument('title', type=str, help='Image title (centered)')
parser.add_argument('year', type=str, default='',help='Year of shot')
parser.add_argument('--configs', type=str, default=[], nargs='+',help='Which output configuration(s) to run')

def load_configs(configs_list):
    for conf_name in configs_list:
        conf = anyconfig.load(f"profiles/{conf_name}.toml")
        confs.append(conf)
    
    if not configs_list:
        logging.warning('Using default configuration as none was specified')
        conf_default = anyconfig.load("profiles/default.toml")
        confs.append(conf_default)

def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    args = parser.parse_args()
    load_configs(args.configs)

    for conf in confs:
        logging.info(f"Running config: {conf['name']}")

        file_path = Path(args.path)
        logging.info(f'\tInput image:{file_path}')
        filename = file_path.name
        filename_with_suffix = filename.replace(file_path.suffix, f'{conf["output"]["suffix"]}')
        output_path = file_path.with_name(filename_with_suffix + '.jpg')
        logging.info(f'\tOutput image:{output_path}')

        with Image(filename=file_path) as input_image:
            input_w = input_image.width
            input_h = input_image.height
            logging.info(f"\tInput resolution: {input_w}x{input_h}")

            border_bottom_px = math.trunc((input_h + input_w) * conf['border']['bottom_scale'])
            border_other_px = math.trunc((input_h + input_w) * conf['border']['top_side_scale'])
            logging.debug(f"\tBorders: {border_bottom_px}px at bottom, {border_other_px}px around")

            with input_image.clone() as output_image:
                output_image.border(conf['border']['color'], int(border_other_px), int(border_bottom_px))
                output_image.crop(left=0, top = math.trunc(border_bottom_px * 0.5)) # The top border will be the same as the bottom otherwise

                with Drawing() as ctx:
                    ctx.font = conf['font']['name']
                    ctx.font_family = conf['font']['family']
                    ctx.font_size = (input_w + input_h) * conf['font']['scale_factor_title']
                    ctx.fill_color = Color(conf['font']['color'])
                    ctx.gravity = "south"
                    ctx.font_weight = conf['font']['weight']
                    output_image.annotate(args.title, ctx, 0, math.trunc(border_bottom_px * 0.39))

                with Drawing() as ctx2:
                    ctx2.font = conf['font']['name']
                    ctx2.font_family = conf['font']['family']
                    ctx2.font_size = (input_w + input_h) * conf['font']['scale_factor_metadata']
                    ctx2.fill_color = Color(conf['font']['color'])
                    ctx2.gravity = "south_west"
                    ctx2.font_weight = conf['font']['weight']
                    output_image.annotate(conf['author']['name'], ctx2, border_other_px, math.trunc(border_bottom_px * 0.55))
                    output_image.annotate("© " + args.year, ctx2, border_other_px, math.trunc(border_bottom_px * 0.31))

                if (conf['resize']['enable']):
                    logging.info(f"\tResizing to {conf['resize']['megapixels']} megapixels ")
                    pixels = conf['resize']['megapixels'] * 1000000
                    input_pixels = input_w * input_h
                    if input_pixels < pixels:
                        logging.warning('\t\tInput image is smaller than output - you are scaling up!')
                    output_image.transform('',f'{pixels}@')

                match conf['output']['codec']:
                    case 'jpeg':
                        output_image.compression_quality = int(conf['output']['quality'])
                        output_image.format = 'jpeg'
                    case 'png':
                        output_image.format = 'png'
                    case 'tiff':
                        output_image.format = 'tiff'
                    case _:
                        logging.warning("\tUnrecognised output format: using PNG")
                        output_image.format = 'png'
                
                output_image.save(filename=output_path)
                logging.info(f'\tSaved output image successfully')
            
    logging.info("All done!")

if __name__ == "__main__":
    main()