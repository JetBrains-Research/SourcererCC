import os

for filename in os.listdir("blocks_stats"):
    readfile = os.path.join("blocks_stats", filename)
    with open(readfile, "r", encoding="utf-8") as file_book:
        with open(os.path.join("blocks_stats", filename.replace("file", "block")), 'w', encoding="utf-8") as block_info:
            with open(os.path.join("files_stats", filename), "w", encoding="utf-8") as file_info:
                for line in file_book:
                    if line.startswith('b'):
                        block_info.write(line)
                    elif line.startswith('f'):
                        file_info.write(line)
                    else:
                        print("error", line)

    print("Done with: ", readfile)
