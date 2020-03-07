#!/usr/bin/env python3
"""Transform SourcererCC results into machine-readable format JSON."""
from argparse import ArgumentParser
from collections import defaultdict, namedtuple
import datetime as dt
import json
import os
import sys
from typing import Dict, Iterator, Generator, List, Set, Tuple
import zipfile

from tqdm import tqdm

# block information available after parsing result file from SourcererCC with pairs
PairBlock = namedtuple("PairBlock", ["proj_id", "block_id"])
# block information available in JSON
Block = namedtuple("Block", ["project", "filepath", "start_line", "end_line", "content"])


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


def get_files(path: str, extension: str) -> Set[str]:
    """
    Get list of files with extension at given path.
    :param path: path to file or directory.
    :param extension: extension that will be used for filtering paths.
    :return: set of paths.
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


def _parse_file_line(line_parts):
    return {
        "project_id": line_parts[0],
        "file_path": line_parts[2],
        "file_hash": line_parts[3],
        "file_size": line_parts[4],
        "lines": line_parts[5],
        "LOC": line_parts[6],
        "SLOC": line_parts[7]
    }


def _parse_block_line(line_parts):
    return {
        "project_id": line_parts[0],
        "block_hash": line_parts[2],
        "block_lines": line_parts[3],
        "block_LOC": line_parts[4],
        "block_SLOC": line_parts[5],
        "start_line": int(line_parts[6]),
        "end_line": int(line_parts[7])
    }


def get_metainfo(metainfo_filepath: str, extension=".stats") -> Dict:
    """
    Read file with meta information from SourcererCC and return dictionary {block_id: metainformation}.
    :param metainfo_filepath: path to file with metainformation from SourcererCC.
           Usually it's stored at paths like `stats_folder/files-stats-*.stats`.
    :param extension: file extension - default one from SourcererCC is '.stats'.
    :return: dictionary {block_id: metainformation} where metainfromation comes from _parse_block_line/_parse_file_line.
    """
    files = get_files(path=metainfo_filepath, extension=extension)
    metainfo = {}
    for stats_file in files:
        for line in get_line_iterator(stats_file):
            line_parts = line.split(",")
            stats = {}
            block_id = line_parts[2]
            if line.startswith("f"):
                stats = _parse_file_line(line_parts[1:])
            elif line.startswith("b"):
                stats = _parse_block_line(line_parts[1:])
                # block_id consists of 2 parts - relative_id & file_id
                stats["relative_id"] = block_id[:5]
                stats["file_id"] = block_id[5:]
            metainfo[block_id] = stats
    return metainfo


def read_lines(archive: zipfile.ZipFile, start_line: str, end_line: str, filename: str) -> str:
    """
    Read lines from filename in archive.
    :param archive: opened archive.
    :param start_line: start line.
    :param end_line: end line.
    :param filename: path to file in archive.
    :return: content.
    """
    with archive.open(filename) as file:
        result = file.read().decode("utf-8").split("\n")
    return "\n".join(result[start_line - 1: end_line])


def split_sourcerercc_path(path: str) -> Tuple[str, str]:
    """
    Split SourcererCC path into archive location and file location in archive.
    Input: "master.zip/src/com/google/Hack.java"
    Output: ("master.zip", "src/com/google/Hack.java")
    :param path: SourcererCC path.
    :return: (archive location, path to file in archive).
    """
    split_index = path.find(".zip") + len(".zip")
    return path[:split_index], path[split_index + 1:]


def update_block2metainfo(raw_metainfo: Dict, block_ids: Iterator[str], block2metainfo: Dict[str, Block]) -> None:
    """
    Update mapping block_id to metainfo as Block namedtuple given raw metainformation, block_ids and dictionary to store
    results.
    :param raw_metainfo: metainformation in raw format.
    :param block_ids: iterator of block_ids and not generator! If it's generator - first element will be lost.
    :param block2metainfo: dictionary to store metainformation in final format.
    :return: None.
    """

    for block_id in block_ids:
        file_path = raw_metainfo[raw_metainfo[block_id]["file_id"]]["file_path"]
        repo_zip_filename, _ = split_sourcerercc_path(file_path.strip('"'))
        break
    with zipfile.ZipFile(repo_zip_filename) as repo_archive:
        for block_id in tqdm(block_ids, desc="processing project"):
            file_path = raw_metainfo[raw_metainfo[block_id]["file_id"]]["file_path"]
            repo_zip_filename, source_file = split_sourcerercc_path(file_path.strip('"'))
            start_line = raw_metainfo[block_id]["start_line"]
            end_line = raw_metainfo[block_id]["end_line"]
            code_content = read_lines(repo_archive, start_line, end_line, source_file)
            block_info = Block(project=os.path.basename(repo_zip_filename),
                               filepath=source_file,
                               start_line=start_line,
                               end_line=end_line,
                               content=code_content)
            block2metainfo[block_id] = block_info


def get_block_metainfo(metainfo_filepath: str, block_ids: Set[str]) -> Dict[str, Block]:
    """
    Read block metainformation and create mapping {block_id: metainformation}.
    :param metainfo_filepath: path to file with metainformation from SourcererCC.
           Usually it's stored at paths like `stats_folder/files-stats-*.stats`.
    :param block_ids: list of block ids to use.
    :return: dictionary {block_id: metainformation}.
    """
    raw_metainfo = get_metainfo(metainfo_filepath=metainfo_filepath)

    # aggregate blocks per project - optimize archive opening
    proj2block_ids = defaultdict(set)
    for block in block_ids:
        proj2block_ids[block.proj_id].add(block.block_id)
    # create mapping from block_id to metainfo as Block namedtuple.
    block2metainfo = {}
    for proj in tqdm(proj2block_ids, desc="projects"):
        update_block2metainfo(raw_metainfo=raw_metainfo, block_ids=proj2block_ids[proj], block2metainfo=block2metainfo)
    return block2metainfo


def main(results_file: str, stats_files: str) -> Generator[str, None, None]:
    """
    Convert SourcererCC output format to JSON.
    :param results_file: result file with pairs from SourcererCC.
    :param stats_files: meta information for blocks from SourcererCC - different ids, paths, start/end line, etc.
    :return: generator with one JSON per row.
    """
    pairs = get_results(results_file)
    blocks_to_use = []
    for pair in pairs:
        blocks_to_use.append(pair[0])
        blocks_to_use.append(pair[1])
    blocks_info_map = get_block_metainfo(stats_files, blocks_to_use)

    for pair in tqdm(pairs, desc="result preparation"):
        el1 = blocks_info_map[pair[0].block_id]
        el2 = blocks_info_map[pair[1].block_id]
        yield json.dumps((el1, el2))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-r", "--results-file", required=True, help="File with results of SourcererCC (results.pairs).")
    parser.add_argument("-s", "--stats-files", required=True, help="File or folder with stats files (*.stats).")
    parser.add_argument("-o", "--output", default=None, help="Output file location. If None - print JSONs, "
                                                             "else - write to file.")

    args = parser.parse_args()
    start_time = dt.datetime.now()

    res = main(args.results_file, args.stats_files)
    if args.output is None:
        for pair in res:
            print(pair)
    else:
        with open(args.output, "w") as f:
            for pair in res:
                f.write(res + "\n")
