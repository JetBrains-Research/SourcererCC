#!/usr/bin/env python3
"""Transform SourcererCC results into machine-readable format JSON."""
from argparse import ArgumentParser
from collections import defaultdict, namedtuple
import datetime as dt
import json
import os
import sys
from typing import Iterator, List, Tuple
import zipfile

from tqdm import tqdm

# block information available after parsing result file from SourcererCC with pairs
PairBlock = namedtuple("PairBlock", ["proj_id", "block_id"])


def get_line_iterator(filename: str) -> Iterator[str]:
    """
    Return line (without newline) iterator for filename.
    :param filename: path to file.
    :return: line iterator.
    """
    with open(filename, encoding="utf-8") as file_descr:
        for line in file_descr:
            yield line.strip("\n")


def get_results(results_file: str) -> List[Tuple[PairBlock, PairBlock]]:
    """
    Parse result file with pairs from SourcererCC.
    :param results_file: path to file with result from SourcererCC.
    :return: list of tuples where each tuple contains Block for first and second element in pair.
    """
    result_pairs = []
    for line in get_line_iterator(results_file):
        proj_id1, block_id1, proj_id2, block_id2 = line.split(",")
        result_pairs.append((PairBlock(proj_id=proj_id1, block_id=block_id1),
                             PairBlock(proj_id=proj_id2, block_id=block_id2)))
    return result_pairs


def filter_files(path, extension):
    """Get list of files in specified path with given extension.
    Return set of files with that extension in that directory
    (or that file if it is file with that extension)

    Arguments:
    path -- where to find files
    extension -- extension to filter files
    """
    res = set()
    if os.path.isdir(path):
        files_list = filter(lambda x: x.endswith(extension), os.listdir(path))
        res.update(map(lambda x: os.path.join(path, x), files_list))
    elif os.path.isfile(path):
        res.add(path)
    else:
        print(f"ERROR: '{path}' not found!")
        sys.exit()
    return res


def parse_file_line(line_parts):
    return {
        "project_id": line_parts[0],
        "file_path": line_parts[2],
        "file_hash": line_parts[3],
        "file_size": line_parts[4],
        "lines": line_parts[5],
        "LOC": line_parts[6],
        "SLOC": line_parts[7]
    }


def parse_block_line(line_parts):
    return {
        "project_id": line_parts[0],
        "block_hash": line_parts[2],
        "block_lines": line_parts[3],
        "block_LOC": line_parts[4],
        "block_SLOC": line_parts[5],
        "start_line": int(line_parts[6]),
        "end_line": int(line_parts[7])
    }


def get_stats_info(stats_files_path):
    """Parse stats.

    Return map where keys are block/file ids and values are maps such as
    in parse_file_line or parse_block_line functions

    Arguments:
    stats_files_path -- file or directory with stats
    """
    files = filter_files(stats_files_path, ".stats")
    stats_info = {}
    for stats_file in files:
        for line in get_line_iterator(stats_file):
            line_parts = line.split(",")
            stats = {}
            code_id = line_parts[2]
            if line.startswith("f"):
                stats = parse_file_line(line_parts[1:])
            elif line.startswith("b"):
                stats = parse_block_line(line_parts[1:])
                stats["relative_id"] = code_id[:5]
                stats["file_id"] = code_id[5:]
            stats_info[code_id] = stats
    return stats_info


def get_lines(repo_archive, start_line, end_line, source_filename):
    """Read specified lines of file from archive.

    Arguments:
    repo_archive -- project zip archive
    start_line -- first line number of code to read
    end_line -- last line number of code to read, -1 for all lines
    source_filename -- path to file to read
    """
    with repo_archive.open(source_filename) as source_file:
        result = source_file.read().decode("utf-8").split("\n")
    return "\n".join(result[start_line - 1: end_line])


def split_zip_file_path(file_path):
    """Split filename of source file in zip archive into zip filename and
    source filename. For example
        "master.zip/src/com/google/Hack.java"
    is split to
        "master.zip", "src/com/google/Hack.java"

    Arguments:
    file_path -- path to file inside zip archive
    """
    split_index = file_path.find(".zip") + len(".zip")
    return file_path[:split_index], file_path[split_index + 1:]


def get_block_info(stats, block_info):
    """Retrieve block info with file name and content of code block

    Arguments:
    stats -- stats map
    block_info -- map with block info from stats
    """
    file_path = stats[block_info["file_id"]]["file_path"]
    repo_zip_filename, source_file = split_zip_file_path(file_path.strip("\""))
    start_line = block_info["start_line"]
    end_line = block_info["end_line"]
    with zipfile.ZipFile(repo_zip_filename, "r") as repo_archive:
        code_content = get_lines(repo_archive, start_line, end_line, source_file)
    return {
        "project": os.path.basename(repo_zip_filename),
        "file": source_file,
        "start_line": start_line,
        "end_line": end_line,
        "content": code_content
    }


def update_info_map(stats, block_ids, blocks_info_map):
    for block_id in block_ids:
        file_path = stats[stats[block_id]["file_id"]]["file_path"]
        repo_zip_filename, _ = split_zip_file_path(file_path.strip("\""))
        break
    with zipfile.ZipFile(repo_zip_filename, "r") as repo_archive:
        for block_id in tqdm(block_ids, desc="processing project"):
            file_path = stats[stats[block_id]["file_id"]]["file_path"]
            repo_zip_filename, source_file = split_zip_file_path(file_path.strip("\""))
            start_line = stats[block_id]["start_line"]
            end_line = stats[block_id]["end_line"]
            code_content = get_lines(repo_archive, start_line, end_line, source_file)
            block_info = {
                "project": os.path.basename(repo_zip_filename),
                "file": source_file,
                "start_line": start_line,
                "end_line": end_line,
                "content": code_content
            }
            blocks_info_map[block_id] = block_info


def get_block_info_map(stats_files, blocks_to_use):
    """Get blocks info map from .stats files"""
    stats = get_stats_info(stats_files)

    # aggregate blocks per project - optimize archive opening
    proj2block_ids = defaultdict(set)
    for block in blocks_to_use:
        proj2block_ids[block.proj_id].add(block.block_id)
    blocks_info_map = {}
    for proj in tqdm(proj2block_ids, desc="projects"):
        update_info_map(stats=stats, block_ids=proj2block_ids[proj], blocks_info_map=blocks_info_map)
    return blocks_info_map


def prettify_sourcererCC_results(results_file: str, stats_files: str) -> List[Tuple]:
    """Print nice formatted results.

    Return map with results parameters in following json format:
        "block_id": {
            clones: [
                file: "{{full_file_path}}"
                start_line: {{first_line_of_block}}
                end_line: {{last_line_of_block}}
                content: "{{block_content}}"
            ]
            start_line: {{first_line_of_block}}
            end_line: {{last_line_of_block}}
            content: "{{block_content}}"
            file: "{{full_file_path}}"
        }

    Arguments:
    results_file -- file with SourcererCC results
    stats_files -- file or directory with stats files
    """
    pairs = get_results(results_file)
    blocks_to_use = []
    for pair in pairs:
        blocks_to_use.append(pair[0])
        blocks_to_use.append(pair[1])
    blocks_info_map = get_block_info_map(stats_files, blocks_to_use)

    for pair in tqdm(pairs, desc="result preparation"):
        el1 = blocks_info_map[pair[0].block_id]
        el1["proj_id"] = pair[0].proj_id
        el2 = blocks_info_map[pair[1].block_id]
        el2["proj_id"] = pair[1].proj_id
        print(json.dumps((el1, el2)))


# Print SourcererCC results conveniently
#
# statsFiles -- file or directory with blocks and files stats(*.stats)
# resultsFile -- file with results paris (first project id, first block/file,
# second project id, second block/file id) usually it is results.pairs
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-r", "--results-file", required=True, help="File with results of SourcererCC (results.pairs).")
    parser.add_argument("-s", "--stats-files", required=True, help="File or folder with stats files (*.stats).")

    args = parser.parse_args()
    start_time = dt.datetime.now()

    prettify_sourcererCC_results(args.results_file, args.stats_files)
