"""Generate config for given parameters."""
import argparse
import os

TEMPLATE_LOC = os.path.join(os.path.abspath(os.path.dirname(__file__)), "config_template.ini")


def main(args: argparse.Namespace) -> None:
    """

    :param args:
    :return:
    """
    with open(TEMPLATE_LOC) as f:
        template = f.read()

    replacements = {
        "{repo_loc}": os.path.abspath(args.repo_loc),
        "{blocks_stats_loc}": os.path.abspath(args.stats_loc),
        "{blocks_bookkeeping_loc}": os.path.abspath(args.bookkeeping_loc),
        "{blocks_tokens_loc}": os.path.abspath(args.tokens_loc),
        "{extensions}": " ".join(args.extensions)
    }
    for replace in replacements.items():
        template = template.replace(replace[0], replace[1])
    with open(args.output, "w") as f:
        f.write(template)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repo-loc", required=True, help="File location with list of paths to zipped code.")
    parser.add_argument("-o", "--output", required=True, help="Path to store generated config file.")
    parser.add_argument("-s", "--stats-loc", required=True, help="PATH_stats_folder.")
    parser.add_argument("-b", "--bookkeeping-loc", required=True, help="PATH_bookkeeping_folder.")
    parser.add_argument("-t", "--tokens-loc", required=True, help="PATH_tokens_folder.")
    parser.add_argument("-e", "--extensions", required=True, nargs="+", help="File extensions to use.")
    args = parser.parse_args()
    main(args)
