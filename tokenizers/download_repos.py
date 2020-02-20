"""
Download repositories from given list and dump them to result directory.
"""
import argparse
from argparse import Namespace
import os
import subprocess
from typing import Union

from joblib import Parallel, delayed
from tqdm import tqdm


def download_repo(url: str, output_dir: str) -> Union[None, subprocess.SubprocessError]:
    """
    Download zipped repository to output directory.
    :param url: repository URL.
    :param output_dir: output directory.
    :return: None if nothing fails, else - exception object.
    """
    if url.endswith("/"):
        url = url[:-1]
    org, repo = url.split("/")[-2:]
    output = os.path.join(os.path.abspath(output_dir), "%s_+_%s.zip" % (org, repo))

    try:
        cmd = ("wget %s/zipball/master -O %s" % (url, output))
        print(cmd)
        cmd = cmd.split()

        subprocess.run(cmd, check=True)
        return output
    except subprocess.SubprocessError as exc:

        return exc, url


def main(args: Namespace) -> None:
    """
    Download zipped repositories and store them in output_dir.
    :param args: arguments from CLI.
    :return: none.
    """
    with open(args.input) as f:
        repos = f.read().split()
    os.makedirs(args.output_dir, exist_ok=True)
    repo_args = [{"url": repo, "output_dir": args.output_dir} for repo in repos]
    res = Parallel(n_jobs=args.ncores)(delayed(download_repo)(**arg) for arg in tqdm(repo_args))
    # exclude fails repositories
    new_res = []
    for r in res:
        if not isinstance(r, str):
            print("%s failed with exception %s" % (r[1], str(r[0])))
        else:
            new_res.append(r)
    with open(args.zip_txt, "w") as f:
        f.write("\n".join(new_res))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="File location with list of repositories.")
    parser.add_argument("-o", "--output-dir", required=True, help="Directory to store downloaded repositories.")
    parser.add_argument("-z", "--zip-txt", required=True, help="File location to store input file for tokenizer.")
    parser.add_argument("-n", "--ncores", default=1, help="Number of cores to use.", type=int)
    args = parser.parse_args()
    main(args)
