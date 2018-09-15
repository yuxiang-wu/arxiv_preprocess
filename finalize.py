import os
import shutil
import os.path as osp
import cPickle
from collections import OrderedDict
import numpy
from multiprocessing import Pool
import nltk
import re

# content_idx = 1


def process_all(mode='all'):
    data = []
    file_count = 0
    output_dir = 'output'
    for directory in os.listdir(output_dir):
        print 'Entering ' + directory
        if mode == 'brief':
            txt_dir = osp.join(output_dir, directory, 'brief')
        else:
            txt_dir = osp.join(output_dir, directory, 'txt')

        if osp.exists(txt_dir):
            for fn in os.listdir(txt_dir):
                with open(osp.join(txt_dir, fn), 'r') as f:
                    lines = f.readlines()
                    try:
                        abstract = lines[4]
                        body = lines[7]
                        file_count += 1
                    except:
                        continue
                    data.append((fn, abstract, body))
                    print "Finished processing %s." % fn

    with open('arxiv.%s.pkl' % mode, 'w') as fo:
        cPickle.dump(data, fo)
    print "Totol %d files." % file_count
    return data


def merge(t):
    ol1 = t[0]
    ol2 = t[1]
    words = ol2.keys()
    freqs = ol2.values()
    for w in words:
        if w not in ol1:
            ol1[w] = 0
        ol1[w] += ol2[w]

    words = ol1.keys()
    freqs = ol1.values()
    count = len(words)
    sorted_idx = numpy.argsort(freqs)
    output_words = [words[ii] for ii in sorted_idx[::-1]]
    output = OrderedDict()
    for w in output_words:
        output[w] = ol1[w]
    return output


def build_dict(doc_list):
    word_freqs = OrderedDict()
    for doc in doc_list:
        print 'Processing ' + doc[0]
        line = doc[content_idx]
        try:
            words_in = nltk.word_tokenize(line)
        except:
            continue
        for w in words_in:
            if w not in word_freqs:
                word_freqs[w] = 0
            word_freqs[w] += 1

    return word_freqs


def build_all_dict(data, output, is_target=False):
    pool_size = 8
    batch_size = len(data) / pool_size
    batches = [data[i * batch_size:(i + 1) * batch_size]
               for i in range(pool_size - 1)]
    batches.append(data[(pool_size - 1) * batch_size:])

    global content_idx
    if is_target:
        content_idx = 1
    else:
        content_idx = 2

    p = Pool(pool_size)
    word_freqs = p.map(build_dict, batches)

    print 'Merging 8 lists'
    q = Pool(pool_size / 2)
    batches = [(word_freqs[2 * i], word_freqs[2 * i + 1])
               for i in range(pool_size / 2)]
    word_freqs = q.map(merge, batches)

    print 'Merging 4 lists'
    q = Pool(pool_size / 4)
    batches = [(word_freqs[2 * i], word_freqs[2 * i + 1])
               for i in range(pool_size / 4)]
    word_freqs = q.map(merge, batches)

    print 'Merging 2 lists'
    word_freqs = merge((word_freqs[0], word_freqs[1]))

    words = word_freqs.keys()
    freqs = word_freqs.values()
    print 'Sorting...'
    sorted_idx = numpy.argsort(freqs)
    sorted_words = [words[ii] for ii in sorted_idx[::-1]]

    print 'Converting...'
    worddict = OrderedDict()
    worddict['**eof**'] = 0
    worddict['**unk**'] = 1
    worddict['**p**'] = 2
    worddict['$'] = 3
    worddict['@'] = 4

    for ii, ww in enumerate(sorted_words):
        worddict[ww] = ii + 5

    if output:
        print 'Writing dictionary...'
        with open(output + '.dict.pkl', 'wb+') as f:
            cPickle.dump(worddict, f)
        print 'Writing word freqs...'
        with open(output + '.freq.pkl', 'wb+') as f:
            cPickle.dump(word_freqs, f)

    print 'Done'
    return worddict


def reduce_dict(words, worddict, maxlen):
    candidates = words[:5]
    count = 5
    p = re.compile(
        r'([_&=\|\[\]{}\^\\\+\?])|(\d+[:\-])|([:\-]\d+)|(\(\w+)|(\w+\))|(\w+\.\w*)|(^\d+$)|(\d+E\-?\d+)')
    for word in words[5:]:
        if re.search(p, word):
            continue
        candidates.append(word)
        count += 1
        if count >= maxlen:
            break
    new_worddict = OrderedDict()
    for ii, vv in enumerate(candidates):
        new_worddict[vv] = ii
    return new_worddict


def main(maxlen_src=3000, n_words_src=100000,
         maxlen_trg=200, n_words_trg=30000, update=False, mode='all'):
    arxivname = 'arxiv.%s' % mode

    if osp.exists(arxivname + '.pkl'):
        print 'Loading arxiv data...'
        with open(arxivname + '.pkl', 'r') as fi:
            data = cPickle.load(fi)
    else:
        data = process_all(mode)

    sourcename = 'arxiv.%s.source' % mode 
    if osp.exists(sourcename + '.dict.pkl'):
        print 'Loading arxiv source dictionary...'
        with open(sourcename + '.dict.pkl', 'r') as f:
            worddict_source = cPickle.load(f)
    else:
        worddict_source = build_all_dict(data, sourcename, False)

    targetname = 'arxiv.%s.target' % mode 
    if osp.exists(targetname + '.dict.pkl'):
        print 'Loading arxiv target dictionary...'
        with open(targetname + '.dict.pkl', 'r') as f:
            worddict_target = cPickle.load(f)
    else:
        worddict_target = build_all_dict(data, targetname, True)

    # update the dataset with corresponding maxlen and n_word
    if update:
        if osp.exists(arxivname + '.pkl'):
            with open(arxivname + '.pkl', 'rb') as f:
                data = cPickle.load(f)
            print 'Finish loading small arxiv'
        else:
            data = []
            for doc in data:
                if doc[2] > maxlen_trg or doc[4] > maxlen_src:
                    continue
                data.append(doc)
            print 'Updated smaller dataset contains %d documents' % len(data)

            with open(arxivname + '.pkl', 'wb+') as f:
                cPickle.dump(data, f)

        # reduce the source dictionary
        worddict_source = build_all_dict(data, None, False)
        words_source = worddict_source.keys()
        if len(words_source) > n_words_src:
            print "Reducing dictionary"
            worddict_source = reduce_dict(
                words_source, worddict_source, n_words_src)
        print 'Pickling...'
        with open(sourcename + '.dict.pkl', 'wb+') as f:
            cPickle.dump(worddict_source, f)

        # reduce the target dictionary
        worddict_target = build_all_dict(data, None, True)
        words_target = worddict_target.keys()
        if len(words_target) > n_words_trg:
            print "Reducing dictionary"
            worddict_target = reduce_dict(
                words_target, worddict_target, n_words_trg)
        print 'Pickling...'
        with open(targetname + '.dict.pkl', 'wb+') as f:
            cPickle.dump(worddict_target, f)


if __name__ == '__main__':
    main(update=True, mode='brief')
