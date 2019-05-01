import re
import sys
import unittest
import hashlib

from . import tokenizing


REGEX = re.compile('.+?@@::@@+\d')


class TestParser(unittest.TestCase):
    # Input is something like: @#@print@@::@@1,include@@::@@1,sys@@::@@1
    def assert_common_properties(self, list_tokens_string):
        self.assertTrue(list_tokens_string.startswith('@#@'))

        if len(list_tokens_string) > 3:
            split = list_tokens_string[3:].split(',')
            for pair in split:
                self.assertTrue(REGEX.match(pair))

    def test_line_counts_1(self):
        input_str = """ line 1
                        line 2
                        line 3 """
        (final_stats, _, _) = tokenizing.tokenize_files(input_str)
        (_, lines, LOC, SLOC) = final_stats

        self.assertEqual(lines, 3)
        self.assertEqual(LOC, 3)
        self.assertEqual(SLOC, 3)

    def test_line_counts_2(self):
        input_str = """ line 1
                        line 2
                        line 3
                    """
        (final_stats, _, _) = tokenizing.tokenize_files(input_str)
        (_, lines, LOC, SLOC) = final_stats

        self.assertEqual(lines, 3)
        self.assertEqual(LOC, 3)
        self.assertEqual(SLOC, 3)

    def test_line_counts_3(self):
        input_str = """ line 1

                    // line 2
                    line 3 
                """
        (final_stats, _, _) = tokenizing.tokenize_files(input_str)
        (_, lines, LOC, SLOC) = final_stats

        self.assertEqual(lines, 5)
        self.assertEqual(LOC, 3)
        self.assertEqual(SLOC, 2)

    def test_comments(self):
        input_str = "// Hello\n // World"
        (final_stats, final_tokens, _) = tokenizing.tokenize_files(input_str)
        (_, lines, LOC, SLOC) = final_stats
        (tokens_count_total, tokens_count_unique, _, tokens) = final_tokens

        self.assertEqual(lines, 2)
        self.assertEqual(LOC, 2)
        self.assertEqual(SLOC, 0)

        self.assertEqual(tokens_count_total, 0)
        self.assertEqual(tokens_count_unique, 0)
        self.assert_common_properties(tokens)

    def test_multiline_comment(self):
        input_str = '/* this is a \n comment */ /* Last one */ '
        (final_stats, final_tokens, _) = tokenizing.tokenize_files(input_str)
        (_, lines, LOC, SLOC) = final_stats
        (tokens_count_total, tokens_count_unique, _, tokens) = final_tokens

        self.assertEqual(lines, 2)
        self.assertEqual(LOC, 2)
        self.assertEqual(SLOC, 0)

        self.assertEqual(tokens_count_total, 0)
        self.assertEqual(tokens_count_unique, 0)
        self.assert_common_properties(tokens)

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
        (final_stats, final_tokens, _) = tokenizing.tokenize_files(string)
        (_, lines, LOC, SLOC) = final_stats
        (tokens_count_total, tokens_count_unique, token_hash, tokens) = final_tokens

        self.assertEqual(lines, 12)
        self.assertEqual(LOC, 11)
        self.assertEqual(SLOC, 9)

        self.assertEqual(tokens_count_total, 27)
        self.assertEqual(tokens_count_unique, 21)
        self.assert_common_properties(tokens)

        hard_tokens = {'int@@::@@4', 'void@@::@@1', 'cstdio@@::@@1', 'action@@::@@1', 'static@@::@@1', 'key@@::@@1',
                       'glfw_key_callback@@::@@1', 'mod@@::@@1', 'if@@::@@1', 'glfw3@@::@@1', 'scancode@@::@@1',
                       'h@@::@@1', 'GLFW_INCLUDE_GLU@@::@@1', 'input_event_queue@@::@@2', 'GLFW@@::@@1', 'push@@::@@1',
                       'inputaction@@::@@1', 'include@@::@@3'}
        this_tokens = set(tokens[3:].split(','))
        self.assertTrue(len(hard_tokens - this_tokens), 0)

        m = hashlib.md5()
        m.update(tokens[3:])
        self.assertEqual(m.hexdigest(), token_hash)


if __name__ == '__main__':
    unittest.main()
