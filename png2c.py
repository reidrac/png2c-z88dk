#!/usr/bin/env python
"""
png2c.py
Copyright (C) 2014 by Juan J. Martinez - usebox.net

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""
__version__ = "1.0"

from argparse import ArgumentParser
from PIL import Image

COLORS = ( (0, 0, 0),
           (0, 0, 205), (0, 0, 255),
           (205, 0, 0), (255, 0, 0),
           (205, 0, 205), (255, 0, 255),
           (0, 205, 0), (0, 255, 0),
           (0, 205, 205), (0, 255, 255),
           (205, 205, 0), (255, 255, 0),
           (205, 205, 205), (255, 255, 255),
           )

ATTR_I = ( 0x00, 0x01, 0x01 | 0x40, 0x02, 0x02 | 0x40,
           0x03, 0x03 | 0x40, 0x04, 0x04 | 0x40, 0x05, 0x05 | 0x40,
           0x06, 0x06 | 0x40, 0x07, 0x07 | 0x40,)

ATTR_P = ( 0x00, 0x08, 0x08 | 0x40, 0x10, 0x10 | 0x40,
           0x18, 0x18 | 0x40, 0x20, 0x20 | 0x40, 0x28, 0x28 | 0x40,
           0x30, 0x30 | 0x40, 0x38, 0x38 | 0x40,)

C2I = dict(zip(COLORS, ATTR_I))
C2P = dict(zip(COLORS, ATTR_P))

BASE = 150

def main():

    parser = ArgumentParser(description="Image conversion tool for Z88DK and SP1.lib",
                            epilog="Copyright (C) 2014 Juan J Martinez <jjm@usebox.net>",
                            )

    parser.add_argument("--version", action="version", version="%(prog)s "  + __version__)
    parser.add_argument("-b", "--base", dest="base", default=BASE, type=int,
                        help="base character (default: %d)" % BASE)
    parser.add_argument("-i", "--id", dest="id", default="tiles", type=str,
                        help="variable name (default: tiles)")
    parser.add_argument("--no-print-string", dest="no_pstring", action="store_true",
                        help="don't include the print string")

    parser.add_argument("image", help="image to convert")

    args = parser.parse_args()

    try:
        image = Image.open(args.image)
    except IOError:
        parser.error("failed to open the image")

    (w, h) = image.size

    if w % 8 or h % 8:
        parser.error("%s size is not multiple of 8")

    if not isinstance(image.getpixel((0, 0)), tuple):
        parse.error("only RGB(A) images are supported")

    # so we support both RGB and RGBA images
    data = list(zip(list(image.getdata(0)), list(image.getdata(1)), list(image.getdata(2))))

    for c in data:
        if c not in COLORS:
            parser.error("invalid color %r in image" % (c,))

    out = ""
    tiles = {}
    attrib = {}
    print_str = []
    cur_attr = None
    for y in range(0, h, 8):
        for x in range(0, w, 8):
            byte = []
            attr = []
            for j in range(8):
                row = 0
                for i in range(8):
                    if data[x + i + (j + y) * w] != COLORS[0]:
                        row |= 1 << (7 - i)
                    if data[x + i + (j + y) * w] not in attr:
                        attr.append(data[x + i + (j + y) * w])
                byte.append(row)

            if len(attr) > 2:
                parser.error("more than 2 colors in an attribute block in (%d, %d)" % (x, y))
            elif len(attr) < 2:
                attr.append(COLORS[0])

            if attr[0] == COLORS[0] and attr[1] != COLORS[0]:
                attr[0], attr[1] = attr[1], attr[0]

            byte_i = tuple(byte + attr)
            if byte_i not in tiles:
                attrib[byte_i] = attr
                tiles[byte_i] = len(tiles)
                if out:
                    out += ",\n"
                out += ', '.join(["%d" % b for b in byte])

            if cur_attr != attrib[byte_i]:
                ink, paper = attrib[byte_i]
                print_str.extend([20, C2I[ink] | C2P[paper]])
                cur_attr = attrib[byte_i]

            print_str.append(tiles[byte_i] + args.base)
        print_str.append(13)

    print_str.append(0)

    print_out = ""
    for part in range(0, len(print_str), 8):
        if print_out:
            print_out += ",\n"
        print_out += ', '.join(["%d" % c for c in print_str[part:part + 8]])

    # header
    print("""
/* png2c.py %s
 *
 * %s (%sx%s)
 * %s x %s (%s unique)
 *
 * base: %s
 */
""" % (__version__, args.image, w, h, w / 8, h / 8, len(tiles), args.base,))

    if not args.no_pstring:
        print("uchar p%s[] = {\n%s\n};" % (args.id, print_out,))

    print("""\
#define %s_BASE %d
#define %s_LEN %d
uchar %s[] = {\n%s\n};
 """ % (args.id.upper(),args.base, args.id.upper(), len(tiles),
        args.id, out,))

if __name__ == "__main__":
    main()

