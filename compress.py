#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
# from progressbar import ProgressBar
import re
from optparse import OptionParser
import json

MAX_WIDTH = 720

parser = OptionParser()
parser.add_option('-c', '--compress', dest='compress', action='store_true')
parser.add_option('-i', '--ignore', dest='ignore_pattern')
parser.add_option('-v', '--verbose', action='store_true')
(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARN)
compress = options.compress
ignore_pattern = options.ignore_pattern

if len(args) != 1:
    sys.stderr.write("Usage: %s target_dir\n" % sys.argv[0])
    sys.exit(2)

BASE_DIR = args[0]

# def shellquote(s):
#   import pipes
#   return pipes.quote(s)


def is_movie(possible_movie):
    #   movie_exts = [
    #       '.ts', '.mp4', '.avi', '.mkv', '.iso', '.img', '.wmv', '.mov']
    movie_exts = [b'.ts', b'.mp4', b'.mkv', b'.iso', b'.img', b'.wmv', b'.mov']
    basefile, ext = os.path.splitext(possible_movie)
    ext = ext.lower()

    logging.debug(f"Checking to see if {ext} is in {movie_exts}")
    if ext in movie_exts:
        return True
    else:
        return None


def touch(filepath):
    open(filepath, 'a').close()


def get_avinfo(filename):

    #   filename = shellquote(filename)

    raw_info = subprocess.check_output([
        "ffprobe", "-v", "quiet", "-print_format", "json", "-show_format",
        "-show_streams", filename
    ])
    try:
        info = json.loads(raw_info)['streams']
    except Exception as e:
        logging.error("%s" % e)
        logging.error("No luck running ffmpeg on %s" % filename)
        sys.exit(2)
        return None

    for item in info:
        try:
            if item['codec_name'] in [
                    'ansi',
            ]:
                return None
        except Exception as e:
            logging.error("Exception: %s" % e)
            continue
    return info


def get_compressed_marker(full_path):

    base, orig_filename = os.path.split(full_path)
    new_filename = b".compressed." + orig_filename + b".marked"
    compressed_marker = os.path.join(base, new_filename)
    return compressed_marker


def main():
    all_video_files = []

    for filename in subprocess.check_output(["find", BASE_DIR, "-type",
                                             "f"]).split(b"\n"):
        filename = filename.strip()
        if filename == b"":
            continue

        logging.debug(f"Examining {filename} for compression")

        # Is this a normalization file?
        if filename.endswith(b"normalizing"):
            logging.debug("Skipping %s since it's normalizing" % filename)
            continue

        # Did we already compress this?
        compressed_marker = get_compressed_marker(filename)
        if os.path.exists(compressed_marker):
            logging.debug(
                f"Skipping {filename}, since {compressed_marker} exists")
            continue

        # Skip
        if ignore_pattern and re.match(
                ignore_pattern, filename, flags=re.IGNORECASE):
            logging.debug(
                f"Skipping {filename} because it matches {ignore_pattern}")
            continue

        # Completed file
        completed_file = "%s/.compression_completed" % os.path.dirname(
            filename)

        if os.path.exists(completed_file):
            logging.debug(
                f"Skipping {filename} because {completed_file} exists")
            continue

        if is_movie(filename):
            logging.debug(f"Adding {filename} to video file list")
            all_video_files.append(filename)
        else:
            logging.debug(f"{filename} is not a movie file")

    # all_video_files_count = len(all_video_files)

    compressable_video_files = []
    for filename in all_video_files:
        info = get_avinfo(filename)
        if not info:
            continue

        width = 0
        for item in info:
            if 'width' in item:
                width = item['width']
                if width > MAX_WIDTH:
                    if filename not in compressable_video_files:
                        compressable_video_files.append(filename)
        basefile, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext in ['.avi', '.mp4', '.iso', '.ts', '.img', '.wmv']:
            if filename not in compressable_video_files:
                compressable_video_files.append(filename)

    compressable_video_files.sort()
    # Unique these bitches up
    compressable_video_files_count = len(compressable_video_files)

    for i in range(compressable_video_files_count):
        filename = compressable_video_files[i]

        # TODO:  Fix this
        basedir, original_filename = os.path.split(filename)
        original_filename_base, original_extension = os.path.splitext(
            original_filename)

        transitional_filename = b"%s.mkv.normalizing" % original_filename_base
        transitional_filename_full = os.path.join(basedir,
                                                  transitional_filename)

        post_filename = b"%s%s" % (original_filename_base, b'.mkv')
        post_filename_full = os.path.join(basedir, post_filename)

        cmd_parts = [
            b'HandBrakeCLI',
            b'--encoder',
            b'x264',
            b'--format',
            b'av_mkv',
            b'--main-feature',
            b'--preset',
            b'Roku 720p30 Surround',
            b'--subtitle-lang-list=eng',
            b'--subtitle-default=none',
            b'--subtitle-burned=none',
            b'-i',
            filename,
            b'-o',
            transitional_filename_full,
        ]
        cmd = b" ".join(cmd_parts)
        if compress:
            logging.warn("Compressing %s (%s of %s)" %
                         (filename, i + 1, compressable_video_files_count))
            logging.debug(cmd)

        else:
            logging.warn(f"Going to compress {filename}")

        # Actual compression
        if compress:

            subprocess.check_call(cmd_parts)

            if not os.path.exists(transitional_filename_full):
                logging.error(
                    "New file is not created...where'd it go?  Quitting...\n")
                sys.exit(2)

            marker_file = get_compressed_marker(post_filename_full)
            touch(marker_file)

            os.remove(filename)
            os.rename(transitional_filename_full, post_filename_full)


if __name__ == '__main__':
    sys.exit(main())
