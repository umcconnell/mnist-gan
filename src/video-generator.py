import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--figs', default='figs/',
                    help='directory containing training figures. Default is figs/')
parser.add_argument('-r', '--framerate', type=int, default=4,
                    help='amount figures shown per second. Default is 4')
parser.add_argument('-o', '--out', default='mnist-gan.mp4',
                    help='filename of video. Default is mnist-gan.mp4')

print("""
Video Generator Utility
=======================
Generate videos from your training images.
Note: This program requires ffmpeg on your machine.
""")

args = parser.parse_args()
command = "ffmpeg -framerate %i -pattern_type glob -i '%s*.png' -c:v libx264 %s" %\
          (args.framerate, args.figs, args.out)

print(command)
os.system(command)
