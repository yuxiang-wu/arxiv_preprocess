import os
import shutil
import os.path as osp
from detex import Detexer
from preprocess import run
# import pdb

# pdb.set_trace()
# def process_all(tex_dir, txt_dir):
#     if not osp.exists(txt_dir):
#         os.mkdir(txt_dir)
#     detexer = Detexer()
#     for filename in os.listdir(tex_dir):
#         if filename.find('.tex') != -1:
#             old_file = osp.join(tex_dir, filename)
#             new_file = osp.join(txt_dir, filename.replace('tex', 'txt'))
#             detexer.detex_file(old_file, new_file)

with open('input/s3cmd_ls.log', 'r') as f:
    files = f.readlines()[2:]

file_list = []
for line in files:
    file_list.append(line.split()[3])

for line in file_list:
    filename = line[15:]
    if filename >= 'arXiv_src_1201_002.tar' and filename < 'arXiv_src_1602_020.tar':
        arxiv_batch = filename[10:-4]
        txt_path = osp.join('output', arxiv_batch, 'brief')
        if osp.exists(txt_path):
            shutil.rmtree(txt_path)
        try:
            run(osp.join('input', filename), osp.join(
                'output', arxiv_batch), mode='brief')
            # process_all('output/' + arxiv_batch + '/tex', 'result/' + arxiv_batch)
        except:
            # raise
            continue
        # else:
            # os.system('s3cmd get --requester-pays --force ' + filename + ' /export/data/ywubw/data/arxiv/')
            # process_all('output/' + arxiv_batch + '/tex', 'result/' + arxiv_batch)
