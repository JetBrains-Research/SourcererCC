import os
import re
import unittest

from block_tokenizer import Tokenizer
from utils import md5_hash


REGEX = re.compile(r".+@@::@@\d+")
tokenizer = Tokenizer("block_config.ini")


class TestParser(unittest.TestCase):
    def run_on_test_file(self, file_name):
        """ Test tokenizer on file which can break tokenizer due to recursion limit """
        source_content = ""
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name), "r", encoding="utf-8") as fd:
            source_content = fd.read()
        return tokenize_files(source_content)

    def assert_common_properties(self, list_tokens_string):
        """ Input is something like: @#@print@@::@@1,include@@::@@1,sys@@::@@1 """
        self.assertTrue(list_tokens_string.startswith('@#@'))

        if len(list_tokens_string) > 3:
            split = list_tokens_string[3:].split(',')
            for pair in split:
                self.assertTrue(REGEX.match(pair))

    def assert_line_counts(self, res, lines, LOC, SLOC):
        (final_stats, _, _) = res
        (_, actual_lines, actual_LOC, actual_SLOC) = final_stats

        self.assertEqual(actual_lines, lines)
        self.assertEqual(actual_LOC, LOC)
        self.assertEqual(actual_SLOC, SLOC)

    def assert_tokenization_results(self, res, lines, LOC, SLOC, total_tokens, unique_tokens):
        (_, final_tokens, _) = res
        (actual_tokens_count_total, actual_tokens_count_unique, _, tokens) = final_tokens

        self.assert_line_counts(res, lines=lines, LOC=LOC, SLOC=SLOC)

        self.assertEqual(actual_tokens_count_total, total_tokens)
        self.assertEqual(actual_tokens_count_unique, unique_tokens)
        self.assert_common_properties(tokens)

    def test_line_counts_1(self):
        input_str = """ line 1
                        line 2
                        line 3 """
        res = tokenize_files(input_str)
        self.assert_line_counts(res, lines=3, LOC=3, SLOC=3)

    def test_line_counts_2(self):
        input_str = """ line 1
                        line 2
                        line 3
                    """
        res = tokenize_files(input_str)
        self.assert_line_counts(res, lines=4, LOC=3, SLOC=3)

    def test_line_counts_3(self):
        input_str = """ line 1

                    // line 2
                    line 3 
                """
        res = tokenize_files(input_str)
        self.assert_line_counts(res, lines=5, LOC=3, SLOC=2)

    def test_comments(self):
        input_str = """// Hello
         // World"""
        res = tokenize_files(input_str)
        self.assert_tokenization_results(res, lines=2, LOC=2, SLOC=0, total_tokens=0, unique_tokens=0)

    def test_multiline_comment(self):
        input_str = '/* this is a \n comment */ /* Last one */ '
        res = tokenize_files(input_str)
        self.assert_tokenization_results(res, lines=2, LOC=2, SLOC=0, total_tokens=0, unique_tokens=0)

    def test_simple_file(self):
        string = u"""#include GLFW_INCLUDE_GLU
                     #include <GLFW/glfw3.h>
                     #include <cstdio>

                     /* Random function */
                     static void glfw_key_callback(int key, int scancode, int action, int mod){
                       if(glfw_key_callback){
                         // Comment here
                         input_event_queue->push(inputaction);   
                       }
                       printf("%s", "asciiじゃない文字");
                     }"""
        res = tokenize_files(string)
        (_, final_tokens, _) = res
        (_, _, token_hash, tokens) = final_tokens
        self.assert_tokenization_results(res, lines=12, LOC=11, SLOC=9, total_tokens=27, unique_tokens=21)

        hard_tokens = {'int@@::@@4', 'void@@::@@1', 'cstdio@@::@@1', 'action@@::@@1', 'static@@::@@1', 'key@@::@@1',
                       'glfw_key_callback@@::@@2', 'mod@@::@@1', 'if@@::@@1', 'glfw3@@::@@1', 'scancode@@::@@1',
                       'h@@::@@1', 'GLFW_INCLUDE_GLU@@::@@1', 'input_event_queue@@::@@1', 'GLFW@@::@@1', 'push@@::@@1',
                       'inputaction@@::@@1', 'include@@::@@3', 'asciiじゃない文字@@::@@1', 'printf@@::@@1', 's@@::@@1'}
        tokens_str = tokens[3:]
        self.assertSetEqual(set(tokens_str.split(',')), set(hard_tokens))
        self.assertEqual(md5_hash(tokens_str), token_hash)

    def test_recursion_limit_light(self):
        """ Test tokenizer on file which can break tokenizer because of lots of
        string concatenations and therefore recursion limit """
        self.run_on_test_file("tests/RecursionLimit.java")

    def test_recursion_limit_heavy(self):
        """ Test tokenizer on file with more string concatenations """
        self.run_on_test_file("tests/RecursionLimit2.java")

    def test_wrong_syntax_error(self):
        """ Test tokenizer not failing on constructions like String[]::new """
        self.run_on_test_file("tests/SyntaxError.java")

    def test_unicode_comments(self):
        """ Test tokenizer working with non-ascii chars in comments """
        res = self.run_on_test_file("tests/UnicodeComments.java")

        self.assert_tokenization_results(res, lines=10, LOC=10, SLOC=5, total_tokens=14, unique_tokens=13)

    def test_unicode_methodname(self):
        """ Test tokenizer working with non-ascii chars in methodnames """
        res = self.run_on_test_file("tests/UnicodeMethodName.java")
        self.assert_tokenization_results(res, lines=9, LOC=8, SLOC=8, total_tokens=20, unique_tokens=16)

    def test_string_literal(self):
        """ Test tokenizer working with non-ascii chars in string literals """
        res = self.run_on_test_file("tests/UnicodeStringLiteral.java")
        self.assert_tokenization_results(res, lines=6, LOC=6, SLOC=6, total_tokens=21, unique_tokens=17)

if __name__ == '__main__':
    unittest.main()
