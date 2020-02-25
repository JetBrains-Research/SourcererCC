
import unittest

from .function_extractor import FunctionExtractor


class TestParser(unittest.TestCase):
    def test_simple_file(self):
        string = """#include GLFW_INCLUDE_GLU
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
        fun_body = """static void glfw_key_callback(int key, int scancode, int action, int mod){
                       if(glfw_key_callback){
                         // Comment here
                         input_event_queue->push(inputaction);   
                       }
                       printf("%s", "asciiじゃない文字");
                     }"""
        fun_lines, fun = FunctionExtractor.get_functions(string, "cpp")
        self.assertSetEqual(fun_lines, [4, 10])
        self.assertEqual(fun, fun_body)

    def test_simple_file_with_main(self):
        string = """#include GLFW_INCLUDE_GLU
                     #include <GLFW/glfw3.h>
                     #include <cstdio>
                     /* Random function */
                     static void glfw_key_callback(int key, int scancode, int action, int mod){
                       if(glfw_key_callback){
                         // Comment here
                         input_event_queue->push(inputaction);   
                       }
                       printf("%s", "asciiじゃない文字");
                     }
                     
                     int main() {
                       printf("Hello, world!");
                       return 0;
                     }"""
        fun_body = """static void glfw_key_callback(int key, int scancode, int action, int mod){
                       if(glfw_key_callback){
                         // Comment here
                         input_event_queue->push(inputaction);   
                       }
                       printf("%s", "asciiじゃない文字");
                     }"""
        fun_lines, fun = FunctionExtractor.get_functions(string, "cpp")
        self.assertSetEqual(fun_lines, [4, 10])
        self.assertEqual(fun, fun_body)
