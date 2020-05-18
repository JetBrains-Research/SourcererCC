#!/usr/bin/env python3
"""Transform SourcererCC results into machine-readable format JSON."""
import argparse
from argparse import ArgumentParser
from collections import defaultdict, namedtuple
import datetime as dt
import json
import os
import sys
from typing import Callable, Dict, Iterator, Generator, List, Set, Tuple, Union
import zipfile

from tqdm import tqdm

# block information available after parsing result file from SourcererCC with pairs
PairBlock = namedtuple("PairBlock", ["proj_id", "block_id"])
# helper structures
Block = namedtuple("Block", ["project", "filepath", "start_line", "end_line", "content"])
BlockMeta = namedtuple("BlockMeta", ["project", "filepath", "start_line", "end_line"])


def convert_block2meta(block: Block) -> BlockMeta:
    """
    Convert Block to BlockMeta.
    :param block: block that should be converted.
    :return: metainformation of block only (without content).
    """
    return BlockMeta(project=block.project, filepath=block.filepath, start_line=block.start_line,
                     end_line=block.end_line)


def get_line_iterator(filename: str) -> Iterator[str]:
    """
    Return line (without newline) iterator for filename.
    :param filename: path to file.
    :return: line iterator.
    """
    with open(filename, encoding="utf-8") as file_descr:
        for line in file_descr:
            yield line.strip("\n")


def get_result_pairs(results_file: str, filter_f: Callable = None) -> List[Tuple[PairBlock, PairBlock]]:
    """
    Parse result file with pairs from SourcererCC and return (filtered) pairs.
    :param results_file: path to file with result from SourcererCC.
    :param filter_f: filter function - if None - no filtering.
    :return: list of tuples where each tuple contains Block for first and second element in pair.
    """
    if filter_f is None:
        def filter_f(): return True

    result_pairs = []
    for i, line in enumerate(get_line_iterator(results_file)):
        proj_id1, block_id1, proj_id2, block_id2 = line.split(",")
        if filter_f(proj_id1, proj_id2):
            result_pairs.append((PairBlock(proj_id=proj_id1, block_id=block_id1),
                                 PairBlock(proj_id=proj_id2, block_id=block_id2)))
    print("Number of pairs in result file %s and number of pairs after filtering %s" % (format(i + 1, ","),
                                                                                        format(len(result_pairs))))
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


def get_raw_metainfo(metainfo_filepath: str, filter_ids: Set[str], extension: str = ".stats") -> Dict:
    """
    Read file with meta information from SourcererCC and return dictionary {block_id: metainformation}.
    :param metainfo_filepath: path to file with metainformation from SourcererCC.
           Usually it's stored at paths like `stats_folder/files-stats-*.stats`.
    :param filter_ids: only for these block/project ids metainformation will be extracted.
    :param extension: file extension - default one from SourcererCC is '.stats'.
    :return: dictionary {block_id: metainformation} where metainfromation comes from _parse_block_line/_parse_file_line.
    """
    files = get_files(path=metainfo_filepath, extension=extension)
    metainfo = {}
    for stats_file in tqdm(files, desc="Extracting metainformation from files"):
        for line in get_line_iterator(stats_file):
            line_parts = line.split(",")
            block_id = line_parts[2]
            if line.startswith("f"):
                stats = _parse_file_line(line_parts[1:])
            elif line.startswith("b"):
                stats = _parse_block_line(line_parts[1:])
                # block_id consists of 2 parts - relative_id & file_id
                stats["relative_id"] = block_id[:5]
                stats["file_id"] = block_id[5:]
            if block_id in filter_ids or stats["project_id"] in filter_ids:
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
        for block_id in tqdm(block_ids, desc="processing project", leave=False):
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


def get_block_metainfo(metainfo_filepath: str, proj_block_ids: Set[PairBlock]) -> Dict[str, Block]:
    """
    Read block metainformation and create mapping {block_id: metainformation}.
    :param metainfo_filepath: path to file with metainformation from SourcererCC.
           Usually it's stored at paths like `stats_folder/files-stats-*.stats`.
    :param proj_block_ids: set of `PairBlock`s to use.
    :return: dictionary {block_id: metainformation}.
    """
    # optimize reading metainformation - read only metainformation for required proj_ids and block_ids
    uniq_block_ids = set()
    for proj_block in proj_block_ids:
        uniq_block_ids.add(proj_block.proj_id)
        uniq_block_ids.add(proj_block.block_id)
    raw_metainfo = get_raw_metainfo(metainfo_filepath=metainfo_filepath, filter_ids=uniq_block_ids)
    # aggregate blocks per project - optimize archive opening
    proj2block_ids = defaultdict(set)
    for block in proj_block_ids:
        proj2block_ids[block.proj_id].add(block.block_id)
    # create mapping from block_id to metainfo as Block namedtuple.
    block2metainfo = {}
    for proj in tqdm(proj2block_ids, desc="Extracting contents per repository"):
        update_block2metainfo(raw_metainfo=raw_metainfo, block_ids=proj2block_ids[proj], block2metainfo=block2metainfo)
    return block2metainfo


def dump_connected_component(output_dir: str, connected_component: Dict, cc_id: int) -> None:
    """
    Create subdirectory, save JSON with connected component and html with statistics about connected component and
    several examples of pairs.
    :param output_dir: base directory to store results.
    :param connected_component: connected component.
    :param cc_id: id of connected component.
    :return: None.
    """
    res_dir = os.path.join(output_dir, "cc_%s" % cc_id)
    os.makedirs(res_dir, exist_ok=True)  # it should not exist
    json_loc = os.path.join(res_dir, "connected_component.json")
    with open(json_loc, "w") as f:
        json.dump(connected_component, f)
    # TODO: add converter to html


def _get_project_ids(project_names: Set[str], bookkeeping_folder: str):
    proj_ids = set()

    files = get_files(path=bookkeeping_folder, extension=".projs")
    for file in files:
        with open(file) as f:
            for line in f:
                proj_id, archive_path = line.strip().split(",")
                archive_name = os.path.basename(archive_path.replace('"', ""))
                if archive_name in project_names:
                    proj_ids.add(proj_id)
    return proj_ids


def main(results_file: str, stats_files: str, filter_repos: Union[List[str], None] = None,
         bookkeeping_folder: str = None) \
        -> Generator[Tuple[Dict, int], None, None]:
    """
    Convert SourcererCC output format to JSON.
    :param results_file: result file with pairs from SourcererCC.
    :param stats_files: meta information for blocks from SourcererCC - different ids, paths, start/end line, etc.
    :param bookkeeping_folder: meta information for blocks from SourcererCC - mapping {project_id: archive_path}.
    :param filter_repos: Repositories that should be used for filtering. If None - no filtering will be applied.
    :return: generator with one JSON per row.
    """
    # parse results of SourcererCC
    print("Extracting metainformation...")
    # filtration
    if filter_repos:
        filter_repos = set(filter_repos)
        proj_ids = _get_project_ids(project_names=filter_repos, bookkeeping_folder=bookkeeping_folder)

        def _is_good_pair(pr1, pr2):
            check1 = pr1 in proj_ids
            check2 = pr2 in proj_ids
            # only one should be in filtered repositories
            return check1 != check2
    else:
        def _is_good_pair(pr1, pr2): return True

    pairs = get_result_pairs(results_file, filter_f=_is_good_pair)

    blocks_to_use = set()
    for pair in pairs:
        blocks_to_use.add(pair[0])
        blocks_to_use.add(pair[1])
    blocks_info_map = get_block_metainfo(stats_files, blocks_to_use)

    # find connected components
    print("Finding connected components...")
    ccc = ConnectedCodeClones()
    for pair in tqdm(pairs, desc="Find connected components"):
        el1 = blocks_info_map[pair[0].block_id]
        el2 = blocks_info_map[pair[1].block_id]
        # yield json.dumps((el1, el2))
        ccc.union(block1=el1, block2=el2)
    print("Number of unique connected components %s" % ccc.n_connected_components())
    if ccc.n_connected_components() == 0:
        print("No connected components found! Finished")
        exit()

    # postprocessing of ConnectedCodeClones
    # store each connected component separately. It should contain 3 items
    # contents: {content_id: content}
    # blocks: {block_id: (BlockMeta, content_id)}
    # pairs: [(block_id1, block_id2), ...]
    print("Postprocessing connected components...")
    pairs.sort(key=lambda pair: ccc.get_block_parent(blocks_info_map[pair[0].block_id]))

    def _new_cc():
        # new connected component
        new_cc = {"contents": {}, "blocks": {}, "pairs": []}
        content2id = {}
        block2id = {}
        return new_cc, content2id, block2id

    current_cc_id = ccc.get_block_parent(blocks_info_map[pairs[0][0].block_id])
    current_cc, content2id, block2id = _new_cc()
    for pair in tqdm(pairs, desc="Postprocess connected components"):
        el1 = blocks_info_map[pair[0].block_id]
        el2 = blocks_info_map[pair[1].block_id]
        if ccc.get_block_parent(el1) != ccc.get_block_parent(el2):
            raise ValueError("Expected parents to be equal.")
        cc_id = ccc.get_block_parent(el1)
        if cc_id != current_cc_id:
            yield current_cc, current_cc_id
            current_cc_id = cc_id
            current_cc, content2id, block2id = _new_cc()

        for el in [el1, el2]:
            # update contents
            if content2id.setdefault(el.content, len(content2id)) not in current_cc["contents"]:
                current_cc["contents"][content2id[el.content]] = el.content
            # update blocks
            meta = convert_block2meta(el)
            if block2id.setdefault(meta, len(block2id)) not in current_cc["blocks"]:
                current_cc["blocks"][block2id[meta]] = (meta, content2id[el.content])
        # update pairs
        current_cc["pairs"].append((block2id[convert_block2meta(el1)], block2id[convert_block2meta(el2)]))
    yield current_cc, current_cc_id


class WeightedQuickUnionPathCompressionUF:
    """
    Class that implements functionality for connected components.
    """

    def __init__(self, n_components: int = 0):
        self.parent = []
        self.size = []
        for i in range(n_components):
            self.add_component()

    def n_components(self):
        assert len(self.parent) == len(self.size), \
            "n_parents (%s) != n_sizes (%s)" % (len(self.parent), len(self.size))
        return len(self.parent)

    def add_component(self):
        """
        Add new component.
        """
        self.parent.append(len(self.parent))  # parent is itself
        self.size.append(1)

    def union(self, id1: int, id2: int):
        """
        Union 2 components with indexes id1 & id2.

        :param id1: index of first component.
        :param id2: index of second component.
        """
        p1 = self.find(id1)
        p2 = self.find(id2)
        if p1 == p2:
            return  # nothing to do - common parent already
        # put smallest subtree below biggest
        if self.size[p1] > self.size[p2]:
            self.parent[p2] = p1
            self.size[p1] += self.size[p2]
        else:
            self.parent[p1] = p2
            self.size[p2] += self.size[p1]

    def validate(self, index: int) -> bool:
        """
        Check that index is valid. If not - raise ValueError.

        :param index: index to check.
        """
        if not (0 <= index < len(self.parent)) or not (type(index) == int):
            raise ValueError("Not valid index %s with type %s, size of parents list is %s" %
                             (index, type(index), len(self.parent)))

    def find(self, index: int) -> int:
        """
        Find parent for given index.

        :param index: index of element to search.
        :return: index of parent.
        """
        self.validate(index)
        root = index
        while root != self.parent[root]:
            self.parent[root] = self.parent[self.parent[root]]
            root = self.parent[root]
        return root

    def connected(self, id1: int, id2: int) -> bool:
        """
        Check if 2 components are connected.

        :param id1: index of first component.
        :param id2: index of second component.
        :return: True if connected and False if not connected.
        """
        return self.find(id1) == self.find(id2)


class ConnectedCodeClones:
    """Union-Find adapted for code clones."""
    def __init__(self, n_components: int = 0):
        self.uf = WeightedQuickUnionPathCompressionUF(n_components=n_components)
        self._content2meta = defaultdict(set)  # {content: set((project, filepath, start_line, end_line), ...)
        self._content2id = {}  # unique id per content
        self._id2block = {}

    def n_connected_components(self) -> int:
        """
        Number of unique connected components.
        :return: Number of unique connected components
        """
        parents = set()
        for content in self._content2id:
            parents.add(self.uf.find(self._content2id[content]))
        return len(parents)

    def add_block(self, block: Block) -> None:
        """
        Check if block is already presented. If not - increase number of components and store metadata for new one.
        :param block: object that contains "project", "filepath", "start_line", "end_line", "content".
        :return: None.
        """
        if block.content not in self._content2meta:
            self.uf.add_component()
            self._content2id[block.content] = self.uf.parent[-1]
        self._content2meta[block.content].add(BlockMeta(project=block.project, filepath=block.filepath,
                                                        start_line=block.start_line, end_line=block.end_line))

    def block2id(self, block: Block):
        return self._content2id[block.content]

    def get_block_parent(self, block: Block) -> int:
        """
        Return parent id.
        :param block: object that contains "project", "filepath", "start_line", "end_line", "content".
        :return: parent id.
        """
        return self.uf.find(self.block2id(block))

    def union(self, block1: Block, block2: Block) -> None:
        """
        Connect 2 blocks.
        :param block1: object that contains "project", "filepath", "start_line", "end_line", "content".
        :param block2: object that contains "project", "filepath", "start_line", "end_line", "content".
        :return: None.
        """
        self.add_block(block1)
        self.add_block(block2)
        self.uf.union(self.get_block_parent(block1), self.get_block_parent(block2))


def pipeline(args: argparse.Namespace) -> None:
    """

    :param args: all required arguments to launch pipeline.
    :return: None.
    """
    start_time = dt.datetime.now()
    res = main(results_file=args.results_file, stats_files=args.stats_files, filter_repos=args.filter,
               bookkeeping_folder=args.bookkeeping_folder)
    if args.output is None:
        for connected_component, _ in res:
            print(connected_component)
    else:
        for connected_component, cc_id in res:
            dump_connected_component(output_dir=args.output, connected_component=connected_component, cc_id=cc_id)
    print("Duration:", dt.datetime.now() - start_time)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-r", "--results-file", required=True, help="File with results of SourcererCC (results.pairs).")
    parser.add_argument("-s", "--stats-files", required=True, help="File or folder with stats files (*.stats).")

    parser.add_argument("-o", "--output", default=None,
                        help="Output directory. If None - print JSONs, else - create subdirectory for each connected "
                             "component, save JSON and html.")
    parser.add_argument("-m", "--mode", default="all-to-all", choices=["all-to-all", "versus"],
                        help="Mode - if `all-to-all` no filtering will be applied, "
                             "if `versus` - result pair should contain only 1 repository from given list of "
                             "repositories.")
    parser.add_argument("-f", "--filter", nargs="*", help="List of repositories (archive names without path) "
                                                          "that will be used for filtering "
                                                          "in case of selected mode `versus`")
    parser.add_argument("-b", "--bookkeeping-folder", default="", type=str, help="File or folder with bookkeeping files"
                                                                                 "(proj_id to archive path mapping).")

    args = parser.parse_args()

    if args.mode == "versus":
        if not args.filter or not args.bookkeeping_folder:
            print(args.filter)
            print(args.b)
            raise ValueError("In case of `versus` mode - both args `--filter` and `--bookkeeping-folder` required.")

    pipeline(args)
