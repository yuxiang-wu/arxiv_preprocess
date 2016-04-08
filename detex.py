import re
import regex


class Detexer(object):
    TITLE = 'title'
    ABSTRACT = 'abstract'
    BODY = 'body'
    INLINE_FORM = 'inline_fm'  # inline formula
    OUTLINE_FORM = 'outline_fm'  # outline formula
    CITE = 'cite'
    FIGURE = 'figure'
    REF = 'ref'
    THEOREM = 'theorem'
    PROOF = 'proof'
    TABLE = 'table'
    BEGIN_ITEM = 'beginItem'
    END_ITEM = 'endItem'
    BEGIN_ENUM = 'beginEnum'
    END_ENUM = 'endEnum'
    ITEM = 'item'

    def __init__(self):
        self.content = ''
        self.title = ''
        self.abstract = ''
        self.body = ''

        self.preprocess_list = [
            (re.compile(r'\%(.*)\n'), '\n'),  # remove comments
            (re.compile(r'\n{2,}'), '\n'),  # remove consecutive empty lines
        ]

        self.common_list = [
            # process inline formulas
            (re.compile(r'\$.*?\$', re.MULTILINE | re.DOTALL), self._to_special(self.INLINE_FORM)),
            (self._create_command_pattern('cite[tp]?'), self._to_special(self.CITE)),  # process citations
            (self._create_command_pattern('(eq)?ref'), self._to_special(self.REF)),  # replace references
        ]

        self.body_list = []
        # self.body_list.append((re.compile(r'(.*)\\maketitle', re.MULTILINE | re.DOTALL), ''))
        # delete formatting commands
        format_commands = ['textbf', 'textit', 'textrm', 'textsc', 'emph', 'tiny', 'small']
        for command in format_commands:
            # replace with inner content of the command
            self.body_list.append((self._create_command_pattern(command), r'\2'))
        delete_words = [r'\\par', r'\\\\', r'\\bigskip', r'\\newpage', r'\\textquote\w*', r'\\noindent']
        for word in delete_words:
            self.body_list.append((re.compile(word), ''))

        # replace sections
        self.body_list.append((re.compile(r'\\section\s*(\[[^\[\]]*\])?\s*{(.*)}'), self._to_special(r'section{\2}')))
        # replace subsections
        self.body_list.append(
            (re.compile(r'\\subsection\s*(\[[^\[\]]*\])?\s*{(.*)}'), self._to_special(r'subsection{\2}')))
        # and subsubsections...
        self.body_list.append(
            (re.compile(r'\\subsubsection\s*(\[[^\[\]]*\])?\s*{(.*)}'), self._to_special(r'subsubsection{\2}')))

        self.body_list.append((self._create_command_pattern('label'), ''))  # delete labels
        self.body_list.append((re.compile(r'\\footnote\s*{[^{}]*}', re.MULTILINE), ''))  # delete footnotes

        # replace outline formulas
        self.body_list.append(
            (re.compile(r'\\\[(.*?)\\\]', re.MULTILINE | re.DOTALL), self._to_special(self.OUTLINE_FORM)))
        self.body_list.append(
            (re.compile(r'\$\$(.*?)\$\$', re.MULTILINE | re.DOTALL), self._to_special(self.OUTLINE_FORM)))
        formular_list = ['align', 'equation', 'multline', 'eqnarray']
        for formular in formular_list:
            self.body_list.append((re.compile(r'\\begin{' + formular + r'\*?}(.*?)\\end{' + formular + r'\*?}',
                                              re.MULTILINE | re.DOTALL), self._to_special(self.OUTLINE_FORM)))

        # replace figures
        self.body_list.append((re.compile(r'\\begin{figure\*?}(.*?)\\end{figure\*?}', re.MULTILINE | re.DOTALL),
                               self._to_special(self.FIGURE)))

        # replace tables
        self.body_list.append((re.compile(r'\\begin{tabularx?\*?}(.*?)\\end{tabularx?\*?}', re.MULTILINE | re.DOTALL),
                               self._to_special(self.TABLE)))
        self.body_list.append((re.compile(r'\\begin{table\*?}(.*?)\\end{table\*?}', re.MULTILINE | re.DOTALL),
                               self._to_special(self.TABLE)))

        # replace theorems and proofs
        self.body_list.append((re.compile(r'\\begin{theorem\*?}(.*?)\\end{theorem\*?}', re.MULTILINE | re.DOTALL),
                               self._to_special(self.THEOREM)))
        self.body_list.append((re.compile(r'\\begin{proof\*?}(.*?)\\end{proof\*?}', re.MULTILINE | re.DOTALL),
                               self._to_special(self.PROOF)))

        preserve_list = ['lemma', 'remark', 'center', 'proposition', 'widetext', 'corollary']
        for environment in preserve_list:
            self.body_list.append((re.compile(r'\\begin{' + environment + r'\*?}(.*?)\\end{' + environment + r'\*?}',
                                              re.MULTILINE | re.DOTALL), r'\1'))

        # process itemize and enumerate
        self.body_list.append((re.compile(r'\\begin{itemize\*?}'), self._to_special(self.BEGIN_ITEM)))
        self.body_list.append((re.compile(r'\\end{itemize\*?}'), self._to_special(self.END_ITEM)))
        self.body_list.append((re.compile(r'\\begin{enumerate\*?}'), self._to_special(self.BEGIN_ENUM)))
        self.body_list.append((re.compile(r'\\end{enumerate\*?}'), self._to_special(self.END_ENUM)))
        self.body_list.append((re.compile(r'\\item\s*(\[.*?\])?'), self._to_special(self.ITEM)))

    def _to_special(self, word):
        left = '<<'
        right = '>>'
        return left + word + right

    def _check_not_empty(self, content):
        """
        Check whether a string contains only whitespaces
        :param content: string to be checked
        :return: True if input contains non-whitespace characters
        """
        empty_pattern = re.compile(r'\s+', re.MULTILINE)
        if re.sub(empty_pattern, '', content):
            return True
        else:
            return False

    def _subsitute(self, sub_list, part=None):
        if part == self.TITLE:
            for regular_exp, rep in sub_list:
                self.title = re.sub(regular_exp, rep, self.title)
        elif part == self.ABSTRACT:
            for regular_exp, rep in sub_list:
                self.abstract = re.sub(regular_exp, rep, self.abstract)
        elif part == self.BODY:
            for regular_exp, rep in sub_list:
                self.body = re.sub(regular_exp, rep, self.body)
        else:
            for regular_exp, rep in sub_list:
                self.content = re.sub(regular_exp, rep, self.content)

    def _create_command_pattern(self, command):
        """
        Helper function: create a matching pattern for latex command
        :param command: command name
        :return: compiled re and group id
        """
        re_string = r'\\' + command + r'\s*(\[[^\[\]]*\]){0,2}\s*{([^{}]*)}'
        return re.compile(re_string)

    def _pre_process(self):
        self._subsitute(self.preprocess_list)

    def _get_title(self):
        # get title
        title_pattern = regex.compile(r'\\[tT]itle\s*({(([^{}]*|(?1))*)})', regex.MULTILINE)
        title_match = regex.search(title_pattern, self.content)
        if title_match:
            self.title = title_match.group(2)
        else:
            raise DetexError("no title is found")
        # process title
        self._subsitute(self.common_list, self.TITLE)
        # checking
        if self._check_not_empty(self.title):
            return self.title
        else:
            raise DetexError("empty title")

    def _get_abstract(self):
        # get abstract
        abstract_pattern = re.compile(r'\\begin{abstract}(.+?)\\end{abstract}', re.MULTILINE | re.DOTALL)
        abstract_match = re.search(abstract_pattern, self.content)
        if abstract_match:
            self.abstract = abstract_match.group(1)
        else:
            odd_pattern = regex.compile(r'\\[aA]bstract\s*({(([^{}]*|(?1))*)})', regex.MULTILINE)
            odd_match = regex.search(odd_pattern, self.content)
            if odd_match:
                self.abstract = odd_match.group(2)
            else:
                raise DetexError('no abstract is found')
        # process abstract
        self._subsitute(self.common_list, self.ABSTRACT)
        # checking
        if self._check_not_empty(self.abstract):
            return self.abstract
        else:
            raise DetexError('empty abstract')

    def _get_body(self):
        body_pattern = re.compile(r'(\\section{(.+))\\end{document}', re.MULTILINE | re.DOTALL)
        body_match = re.search(body_pattern, self.content)
        if body_match:
            self.body = body_match.group(1)
        else:
            raise DetexError('no body is found')

        start = self.body.find(r'\maketitle')
        if start >= 0:
            self.body = self.body[start + len(r'\\maketitle'):]

        self._subsitute(self.common_list, self.BODY)
        self._subsitute(self.body_list, self.BODY)

        if self._check_not_empty(self.body):
            return self.body
        else:
            raise DetexError('body is empty')

    def detex(self, content=None):
        """
        Convert a tex file to plain text
        :param content: tex file string
        :return: plain text string, return None if it failed
        """
        if content:
            self.content = content
        else:
            if not self.content:
                raise DetexError('empty content')

        self._pre_process()

        try:
            title_string = self._get_title()
        except DetexError:
            title_string = ''  # title is not necessary

        try:
            abstract_string = self._get_abstract()
            body_string = self._get_body()
        except DetexError as e:
            raise e

        output = self._to_special(self.TITLE) + '\n' + title_string + '\n\n' \
                 + self._to_special(self.ABSTRACT) + '\n' + abstract_string + '\n\n' \
                 + self._to_special(self.BODY) + '\n' + body_string + '\n'
        return output

    def detex_file(self, input_file, output_file):
        with open(input_file, 'r') as f1:
            content = f1.read()
        try:
            text = self.detex(content)
        except DetexError as e:
            print "Failed when processing %s: %s" % (input_file, e)
        else:
            with open(output_file, 'w+') as f2:
                f2.write(text)
            print 'Finished processing %s.' % input_file


class DetexError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr('DetexError: ' + self.value)


if __name__ == '__main__':
    detexer = Detexer()
    print detexer.detex_file('output/tex/1602.09009.tex', 'output/txt/1602.09009.txt')
