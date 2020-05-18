#!/usr/bin/env python3
"""
One liner to launch clone detector from end to end.
How-to-use:
Build image: `docker build -t  plagiate .`
Launch pipeline:
`docker run --rm -v ~/test/input:/input -v ~/test/output:/output plagiate -e .csx .cs -m versus -f a.zip`
Explanation:
* `-v ~/test/input:/input` - attach volume with archived repositories
* `-v ~/test/output:/output` - attach volume to store results
* `-e .csx .cs` - file extensions for C# (for different languages will be different)
* `-m versus` - plagiate detector compare one repositories against others
* `-f a.zip` - list of repositories (only one element in plagiated pair should be from this list)
"""
import argparse
import glob
import logging as log
import os
import re
import subprocess
import sys
from typing import List

from attrdict import AttrDict

# add current dir to make prettify_results.py available
CURR_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(CURR_DIR)
# add path to "tokenizers" directory
TOKENIZERS_DIR = os.path.join(CURR_DIR, "tokenizers")
sys.path.append(TOKENIZERS_DIR)

from tokenizers.generate_config import main as generate_config_main
from prettify_results import pipeline as prettier_main

CLONE_DETECTOR_DIR = os.path.join(CURR_DIR, "clone-detector")


class AwesomeFormatter(log.Formatter):
    """
    logging.Formatter which adds colors to messages and shortens thread ids.
    """

    GREEN_MARKERS = [" ok", "ok:", "finished", "complete", "ready",
                     "done", "running", "success", "saved"]
    GREEN_RE = re.compile("|".join(GREEN_MARKERS))

    def formatMessage(self, record: log.LogRecord) -> str:
        """Convert the already filled log record to a string."""
        level_color = "0"
        text_color = "0"
        fmt = ""
        if record.levelno <= log.DEBUG:
            fmt = "\033[0;37m" + log.BASIC_FORMAT + "\033[0m"
        elif record.levelno <= log.INFO:
            level_color = "1;36"
            lmsg = record.message.lower()
            if self.GREEN_RE.search(lmsg):
                text_color = "1;32"
        elif record.levelno <= log.WARNING:
            level_color = "1;33"
        elif record.levelno <= log.CRITICAL:
            level_color = "1;31"
        if not fmt:
            fmt = "\033[" + level_color + \
                  "m%(levelname)s\033[0m:%(name)s:\033[" + text_color + \
                  "m%(message)s\033[0m"
        return fmt % record.__dict__


def get_archives(dir_loc: str, archive_ext: str = ".zip") -> List[str]:
    """
    Find all archives in a given directory.
    :param dir_loc: directory with archives.
    :param archive_ext: extension for archive like ".zip".
    :return: list of absolute archive locations.
    """
    archive_locs = glob.glob(os.path.join(dir_loc, "*" + archive_ext))
    return archive_locs


def main(args: argparse.Namespace) -> None:
    """
    Full SourcererCC pipeline in one call:
    * generate config for tokenizer
    * launch tokenizer
    * prepare input & configs for `clone-detector`
    * launch `clone-detector`
    * postprocess results
    * prettify
    :param args: arguments for pipeline.
    :return: None.
    """
    # * generate config for tokenizer
    log.info("Starting: generate config for tokenizer")
    tokenizer_output = os.path.join(args.output, "tokens")
    os.makedirs(tokenizer_output, exist_ok=True)
    tokenizer_attr = AttrDict()
    # `-s`, `-b`, `-t`:  `stats_folder`, `bookkeeping_folder`, `tokens_folder`
    tokenizer_attr.stats_loc = os.path.join(tokenizer_output, "stats_folder")
    tokenizer_attr.bookkeeping_loc = os.path.join(tokenizer_output, "bookkeeping_folder")
    tokenizer_attr.tokens_loc = os.path.join(tokenizer_output, "tokens_folder")
    # `-o`: config location
    tokenizer_attr.output = os.path.join(tokenizer_output, "config.ini")
    # `-e`: extensions
    tokenizer_attr.extensions = args.extensions
    # `-r`: repository list should be generated from shared volume
    tokenizer_attr.repo_loc = os.path.join(tokenizer_output, "repos.txt")
    with open(tokenizer_attr.repo_loc, "w") as f:
        f.write("\n".join(get_archives(args.input)))
    generate_config_main(tokenizer_attr)
    log.info("Finished: generate config for tokenizer")

    # * launch tokenizer
    log.info("Starting: tokenization")
    tokenize_cmd = "python3 -m tokenizers.block_level_tokenizer -i {conf_loc}".format(conf_loc=tokenizer_attr.output)
    tokenize_cmd = tokenize_cmd.split()
    print(tokenize_cmd)  # debug
    subprocess.check_call(args=tokenize_cmd, cwd=CURR_DIR)
    log.info("Finished: tokenization")


    # * prepare input & configs for `clone-detector`
    log.info("Starting: prepare input & configs for `clone-detector`")
    clone_detector_input = os.path.join(CLONE_DETECTOR_DIR, "input", "dataset", "blocks.file")
    clone_detector_input_dir = os.path.join(CLONE_DETECTOR_DIR, "input", "dataset")
    os.makedirs(clone_detector_input_dir)

    prepare_cmd = "cat {tokens} > {clone_input}".format(tokens=os.path.join(tokenizer_attr.tokens_loc, "*"),
                                                        clone_input=clone_detector_input)

    subprocess.check_call(prepare_cmd, shell=True)
    subprocess.check_call(["ls", clone_detector_input])
    log.debug("HERE" * 20)

    runnodes_template = os.path.join(CLONE_DETECTOR_DIR, "templates", "runnodes.sh")
    runnodes_loc = os.path.join(CLONE_DETECTOR_DIR, "runnodes.sh")
    with open(runnodes_template) as f:
        template = f.read()
        thresh_arg = "{threshold}".format(threshold=str(args.threshold * 10))
        runnodes_content = template.replace("{THRESHOLD_ARGUMENTS}", thresh_arg)
    with open(runnodes_loc, "w") as f:
        f.write(runnodes_content)

    sourcerer_properties_template = os.path.join(CLONE_DETECTOR_DIR, "templates", "sourcerer-cc.properties")
    sourcerer_properties_loc = os.path.join(CLONE_DETECTOR_DIR, "sourcerer-cc.properties")
    with open(sourcerer_properties_template) as f:
        template = f.read()
        properties_content = template.replace("{MIN_TOKENS}", str(args.min_tokens)).replace("{MAX_TOKENS}",
                                                                                            str(args.max_tokens))
        log.debug(properties_content)
    with open(sourcerer_properties_loc, "w") as f:
        f.write(properties_content)
    log.info("Finished: prepare input & configs for `clone-detector`")

    # * launch `clone-detector`
    log.info("Starting: `clone-detector`")
    clone_detector_cmd = "python3 controller.py".split()
    subprocess.check_call(clone_detector_cmd, cwd=CLONE_DETECTOR_DIR)
    log.info("Finished: `clone-detector`")

    # * postprocess results
    log.info("Starting: postprocess results")
    clone_detector_output = os.path.join(CLONE_DETECTOR_DIR, "NODE_*", "output*", "query_*")
    result_pairs = os.path.join(tokenizer_output, "result.pairs")
    postprocess_cmd = "cat {output} > {pairs}".format(output=clone_detector_output, pairs=result_pairs)
    subprocess.check_call(postprocess_cmd, shell=True)
    log.info("Finished: postprocess results")

    # * prettify
    log.info("Starting: prettify")
    prettier_attr = AttrDict()
    prettier_attr.results_file = result_pairs
    prettier_attr.stats_files = tokenizer_attr.stats_loc
    prettier_attr.output = os.path.join(args.output, "pretty")
    prettier_attr.bookkeeping_folder = tokenizer_attr.bookkeeping_loc
    prettier_attr.mode = args.mode
    prettier_attr.filter = args.filter

    prettier_main(prettier_attr)

    log.info("Finished: prettify")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", default="/output/", help="Output directory to store results of the pipeline. "
                                                                   "(be careful when using in docker - you should "
                                                                   "specify path in docker)")
    # tokenizer's arguments
    parser.add_argument("-i", "--input", default="/input/", help="Input directory with archived repositories. "
                                                                 "(be careful when using in docker - you should "
                                                                 "specify path in docker)")
    parser.add_argument("-e", "--extensions", required=True, nargs="+", help="File extensions to use.")
    # clone detector's arguments
    parser.add_argument("-t", "--threshold", type=float, default=0.8, help="Similarity threshold for clone detector.")
    parser.add_argument("--min-tokens", type=int, default=40, help="Minimum number of tokens in function "
                                                                   "(if less - function will be skipped).")
    parser.add_argument("--max-tokens", type=int, default=50000000, help="Maximum number of tokens in function "
                                                                         "(if more - function will be skipped).")
    # prettier's arguments
    parser.add_argument("-m", "--mode", default="all-to-all", choices=["all-to-all", "versus"],
                        help="Mode - if `all-to-all` no filtering will be applied, "
                             "if `versus` - result pair should contain only 1 repository from given list of "
                             "repositories.")
    parser.add_argument("-f", "--filter", nargs="*", help="List of repositories (archive names without path) "
                                                          "that will be used for filtering "
                                                          "in case of selected mode `versus`")

    args = parser.parse_args()

    if args.threshold < 0 or args.threshold > 1:
        raise ValueError("Threshold should be in range 0~1, got {threshold}".format(args.threshold))
    if args.min_tokens < 0 or args.max_tokens <= 0 or args.min_tokens >= args.max_tokens:
        raise ValueError("Please check arguments: min_tokens ({min_tokens}) and max_tokens ({max_tokens})".format(
            min_tokens=args.min_tokens, max_tokens=args.max_tokens))

    if args.mode == "versus" and not args.filter:
        print(args.filter)
        raise ValueError("In case of `versus` mode - args `--filter` required.")

    log.basicConfig()
    log.getLogger().setLevel("DEBUG")
    handler = log.getLogger().handlers[0]
    handler.setFormatter(AwesomeFormatter())
    main(args)
