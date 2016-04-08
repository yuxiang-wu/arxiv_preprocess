import re


# process input string, remove non-text content, add tags
def process(x, section):
    ignore = 0
    string = ''
    i = 0
    x = x.strip()
    while i < len(x):
        char = x[i]
        # deal with $...$ or $$...$$
        # ok
        if char == '$':
            if ignore:
                if i < len(x) - 1 and x[i + 1] == '$':
                    i += 1
                ignore = 0
            else:
                if i < len(x) - 1 and x[i + 1] == '$':
                    i += 1
                ignore = 1
                string += '<<formula>>'
        elif ignore:
            i = i
        # ignore everything between {...}
        elif x[i] == '{':
            if not section:
                count = 1
                while count:
                    i += 1
                    if x[i] == '{' and x[i - 1] != '\\':
                        count += 1
                    if x[i] == '}':
                        count -= 1

            else:
                string += x[i]
        elif char == '\\':
            # lot of stuff here
            if i < len(x) - 1 and x[i + 1] == '\\':
                i += 1
                string += '\n'
            # ok
            elif i < len(x) - 4 and x[i + 1:i + 5] == "cite":
                string += '<<citation>>'
                while i < len(x) and x[i] != '}':
                    i += 1
            # not good when \begin{a \begin{a} \end{a}} \end{a} occurs
            # need to keep track of each begin like we did with {
            elif i < len(x) - 5 and x[i + 1:i + 7] == 'begin{':
                string += '<<'
                i += 7
                substring = ''
                while x[i] != '}':
                    substring += x[i]
                    i += 1
                string += substring
                string += '>> '
                subcontent = ''
                i += 1
                while x[i:i + 4] != '\\end' or x[i + 5:i + 5 + len(substring)] != substring:
                    #                    try:
                    subcontent += x[i]
                    i += 1
                while x[i] != '}':
                    i += 1
                if substring == 'enumerate' or substring == 'itemize' or substring == 'description':
                    # something wrong, when an item contains \begin{itemize}
                    try:
                        string += process(subcontent, 0)
                    except:
                        print 'sub ' + subcontent
                        exit(0)
            # ok
            elif i < len(x) - 3 and x[i + 1:i + 4] == 'ref':
                i += 4
                string += '<<ref>>'
                if x[i].isspace():
                    while x[i].isspace():
                        i += 1
                if x[i] == '{':
                    count = 1
                while count:
                    i += 1
                    if x[i] == '{':
                        count += 1
                    if x[i] == '}':
                        count -= 1
            elif i < len(x) - 3 and x[i + 1:i + 5] == 'item':
                i += 5
                string += '<<item>>'
            # not above cases, we ignore everything after\
            ##############################
            # many different situations:
            # \word { {} }
            # \[...]
            # better rewrite this part
            else:
                i += 1
                while i < len(x) and x[i].isspace():
                    i += 1
                if i == len(x):
                    return string
                # if (...)
                if x[i] == '(':
                    count = 1
                    i += 1
                    while count:
                        if x[i] == '(':
                            count += 1
                        if x[i] == ')':
                            count -= 1
                        i += 1
                elif x[i] == '[':
                    count = 1
                    i += 1
                    while count:
                        if x[i] == '[':
                            count += 1
                        if x[i] == ']':
                            count -= 1
                        i += 1
                elif x[i] == '{':
                    count = 1
                    i += 1
                    while count:
                        if x[i] == '{':
                            count += 1
                        if x[i] == '}':
                            count -= 1
                        i += 1
                else:
                    while i < len(x) and not x[i].isspace() and x[i] != '\\' and x[i] != ')' and x[i] != ']':
                        if x[i] == '{':
                            count = 1
                            while i < len(x) and count:
                                i += 1
                                if x[i] == '{':
                                    count += 1
                                if x[i] == '}':
                                    count -= 1
                            break
                        i += 1
                    if i < len(x) and x[i].isspace():
                        if i < len(x) - 1 and x[i + 1] == '{':
                            while i < len(x) and x[i] != '}':
                                i += 1
                            i += 1
                    if i < len(x) and x[i] != '}':
                        i -= 1
                        #######################
        else:
            string += char

        i += 1
    return string


filehead = '1602.0'
for i in range(8512, 9009):
    filename = filehead + str(i)
    print filename
    try:
        f = open(filename, 'r')
    except:
        print 'no file'
        continue
    wf = open(filename + '.txt', 'w')

    try:
        content = f.read().decode('utf8')
    except:
        print 'can\'t open with utf8'
        continue

    ###########################
    # deal with title
    # ok
    wf.write('<<title>>\n')
    title = re.findall('\\\\title{(.*?)}', content)
    if title:
        title = title[0]
        title = process(title, 1)
        wf.write(title)
        wf.write('\n\n')
    ###########################

    ###########################
    # deal with abstract
    # ok
    mystr = ''
    find_abstract = 0
    for line in open(filename, 'r').readlines():
        line = line.strip() + ' '
        if line[0] == '%':
            continue
        if find_abstract:
            if r'\end{abstract}' in line:
                mystr = process(mystr, 1)
                wf.write(mystr)
                wf.write('\n\n')
                break
            else:
                if not line.isspace():
                    mystr += line
                else:
                    mystr += '\n'
        elif r'\begin{abstract}' in line:
            find_abstract = 1
            wf.write('<<abstract>>\n')
    ############################

    ############################
    # deal with section
    # read line by line, until section or subsection or subsubsection occurs in line
    # I assume the end a of a section is the start of another
    # should be ok
    mystr = ''
    section_record = 0
    lines = open(filename, 'r').readlines()
    k = 0
    while k < len(lines):
        line = lines[k]

        line = line.strip()
        if line and line[0] == '%':
            k += 1
            continue
        line = line.split('%', 1)[0]
        line = line + ' '
        if section_record:
            if r'\section' in line:
                mystr = process(mystr, 0)
                wf.write(mystr)
                wf.write('\n\n')
                section_record = 1
                mystr = "{"
                pos = 8
                while line[pos] != '{':
                    pos += 1
                count = 1
                pos += 1
                while count:
                    if line[pos] == '{':
                        count += 1
                    elif line[pos] == '}':
                        count -= 1
                    mystr += line[pos]
                    if pos == len(line) - 1:
                        pos = 0
                        k += 1
                        line = lines[k].strip()
                    else:
                        pos += 1
                wf.write('<<section>>')
                wf.write(process(mystr, 1))
                wf.write('\n')
                k += 1
                mystr = ""
                continue
            elif r'\subsection' in line:
                mystr = process(mystr, 0)
                wf.write(mystr)
                wf.write('\n\n')
                section_record = 1
                mystr = "{"
                pos = 11
                while line[pos] != '{':
                    pos += 1
                count = 1
                pos += 1
                while count:
                    if line[pos] == '{':
                        count += 1
                    elif line[pos] == '}':
                        count -= 1
                    mystr += line[pos]
                    if pos == len(line) - 1:
                        pos = 0
                        k += 1
                        line = lines[k].strip()
                    else:
                        pos += 1
                wf.write('<<subsection>>')
                wf.write(process(mystr, 1))
                wf.write('\n')
                k += 1
                mystr = ""
                continue
            elif r'\subsubsection' in line:
                mystr = process(mystr, 0)
                wf.write(mystr)
                wf.write('\n\n')
                section_record = 1
                mystr = "{"
                pos = 14
                while line[pos] != '{':
                    pos += 1
                count = 1
                pos += 1
                while count:
                    if line[pos] == '{':
                        count += 1
                    elif line[pos] == '}':
                        count -= 1
                    mystr += line[pos]
                    if pos == len(line) - 1:
                        pos = 0
                        k += 1
                        line = lines[k].strip()
                    else:
                        pos += 1
                wf.write('<<subsubsection>>')
                wf.write(process(mystr, 1))
                wf.write('\n')
                k += 1
                mystr = ""
                continue
            else:
                if not line.isspace():
                    mystr += line
                else:
                    mystr += '\n'
        # the first section
        if r'\section' in line:
            section_record = 1
            mystr += line[8:-1]
            wf.write('<<section>>')
            if line[-1] != '}':
                k += 1
                while not lines[k].isspace() and lines[k][-1] != '}':
                    mystr += lines[k]
                    k += 1
            wf.write(process(mystr, 1))
            wf.write('\n')
            mystr = ""
        # useless, won't start with subsection
        elif r'\subsection' in line:
            section_record = 1
            mystr = ""
            wf.write('<<subsection>>')
            wf.write(process(line[11:-1], 1))
            wf.write('\n')

        k += 1
    mystr = process(mystr, 0)
    wf.write(mystr)
    wf.write('\n')
    ############################


    wf.close()
    f.close()
