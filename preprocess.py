import tarfile, sys, os, gzip
import os.path as osp
from detex import Detexer


def unzip(input_file, output_dir):
    """
    :param input_file: path of input file
    :param output_dir: output directory of tex files
    :return: number of successful unzip, and tex file dir
    """
    count = 0
    gz_file_dir = osp.join(output_dir, 'gz')
    tex_file_dir = osp.join(output_dir, 'tex')
    tar = tarfile.open(input_file, 'r')
    for item in tar:
        if item.name.find('.gz') != -1:
            arxiv_id = osp.split(item.name)[-1][:-3]  # remove file type
            target_file = osp.join(tex_file_dir, arxiv_id + '.tex')
            if os.path.exists(target_file):
                continue

            tar.extract(item, gz_file_dir)
            gz_path = osp.join(gz_file_dir, item.name.replace('/', os.sep))  # for windows
            try:
                gz_files = tarfile.open(gz_path, 'r|gz')
            except tarfile.TarError:
                try:
                    gzip_open = gzip.open(gz_path, 'r')
                    write_file = open(osp.join(tex_file_dir, arxiv_id + '.tex'), 'w')
                    write_file.writelines(gzip_open.readlines())
                    gzip_open.close()
                    write_file.close()
                    count += 1
                    continue
                except:
                    print "Warning: failed to process " + arxiv_id
                    continue
            else:
                for src_file in gz_files:
                    if src_file.name.find('.tex') != -1:
                        gz_files.extract(src_file, tex_file_dir)
                        src_file_path = osp.join(tex_file_dir, src_file.name)
                        if is_document(src_file_path):
                            os.rename(src_file_path, target_file)
                            count += 1
                            break
                        else:
                            os.remove(src_file_path)
                gz_files.close()
        else:
            print "Ignoring " + item.name
    tar.close()
    return count


def is_document(path):
    with open(path, 'r') as f:
        content = f.read()
    begin = content.find('\\begin{document}') != -1
    end = content.find('\\end{document}') != -1
    return begin & end


def preprocess(output_dir):
    tex_file_dir = osp.join(output_dir, 'tex')
    text_file_dir = osp.join(output_dir, 'txt')
    detexer = Detexer()
    if not osp.exists(text_file_dir):
        os.mkdir(text_file_dir)
    for filename in os.listdir(tex_file_dir):
        if filename.find('.tex') != -1:
            old_file = osp.join(tex_file_dir, filename)
            new_file = osp.join(text_file_dir, filename.replace('tex', 'txt'))
            detexer.detex_file(old_file, new_file)
    return


def main(input_file, output_dir):
    print "Processing " + input_file + "..."
    count = unzip(input_file, output_dir)
    print "Finished processing %d files." % (count,)
    print "Start preprocessing ..."
    preprocess(output_dir)
    print "Done."


if __name__ == "__main__":
    # if not len(sys.argv) == 3:
    #     print "Usage: python preprocess.py <input tar file> <output dir>"
    # main(sys.argv[1], sys.argv[2])
    main('input/arXiv_src_1602_019.tar', 'output')
