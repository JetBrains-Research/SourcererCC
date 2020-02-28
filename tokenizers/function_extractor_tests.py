import unittest
import os

from .function_extractor import FunctionExtractor


def read_file(filename):
    res = None
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), filename), "r", encoding="utf-8") as fd:
        res = fd.read()
    return res

class TestParser(unittest.TestCase):
    def test_c_file(self):
        string = read_file("tests/fun.c")
        fun_body = """static void glfw_key_callback(int key, int scancode, int action, int mod){
  if(glfw_key_callback){
    // Comment here
    input_event_queue->push(inputaction);
  }
  printf("%s", "asciiじゃない文字");
}"""
        fun_lines, fun = FunctionExtractor.get_functions(string, "c")
        self.assertEqual(fun_lines, [(4, 10)])
        self.assertEqual(fun, [fun_body])

    def test_c_file_with_main(self):
        string = read_file("tests/main.c")
        fun_body = """static void glfw_key_callback(int key, int scancode, int action, int mod){
  if(glfw_key_callback){
    // Comment here
    input_event_queue->push(inputaction);   
  }
  printf("%s", "asciiじゃない文字");
}"""
        main_body = """int main() {
  printf("Hello, world!");
  return 0;
}"""
        fun_lines, fun = FunctionExtractor.get_functions(string, "c")
        self.assertEqual(fun_lines, [(4, 10), (12, 15)])
        self.assertEqual(fun, [fun_body, main_body])

    def test_cpp_file(self):
        string = read_file("tests/fun.cpp")
        fun_body = """void dfs(int v) {
    for (int to : g[v]) {
        t.push_back(to);
        dfs(to);
    }
}"""
        fun_lines, fun = FunctionExtractor.get_functions(string, "cpp")
        self.assertEqual(fun_lines, [(6, 11)])
        self.assertEqual(fun, [fun_body])

    def test_cpp_file_with_main(self):
        string = read_file("tests/main.cpp")
        fun_body = """void dfs(int v) {
    for (int to : g[v]) {
        t.push_back(to);
        dfs(to);
    }
}"""
        main_body = """int main() {
    int n;
    cin >> n;
    g = vector<vector<int>>(n);
    for (int i = 0; i < n; i++) {
        g[i].append(i);
    }
    return 0;
}"""
        fun_lines, fun = FunctionExtractor.get_functions(string, "cpp")
        self.assertEqual(fun_lines, [(8, 13), (15, 23)])
        self.assertEqual(fun, [fun_body, main_body])

    def test_java_file(self):
        string = read_file("tests/main.java")
        main_body = """public static void main(String[] args) {
        System.out.println(приветМир());
    }"""
        fun_body = """private static String приветМир() {
    	return "Hello, World!";
    }"""
        fun_lines, fun = FunctionExtractor.get_functions(string, "java")
        self.assertEqual(fun_lines, [(1, 3), (5, 7)])
        self.assertEqual(fun, [main_body, fun_body])

    def test_csharp_file(self):
        string = read_file("tests/fun.cs")
        prop_body = "public static WindowsElement Window => session.FindElementByClassName();"
        fun_body = """public int AddNumbers(int number1, int number2) {
            int result = number1 + number2;
            return result;
        }"""
        fun_lines, fun = FunctionExtractor.get_functions(string, "c_sharp")
        self.assertEqual(fun_lines, [(7, 7), (13, 16)])
        self.assertEqual(fun, [prop_body, fun_body])

    def test_csharp_file_with_main(self):
        string = read_file("tests/main.cs")
        prop_body = "public static WindowsElement Window => session.FindElementByClassName();"
        fun_body = """public int AddNumbers(int number1, int number2) {
            int result = number1 + number2;
            return result;
        }"""
        main_body = """public static void int main(String[] args) {
            return 0;
        }"""
        fun_lines, fun = FunctionExtractor.get_functions(string, "c_sharp")
        self.assertEqual(fun_lines, [(6, 6), (10, 13), (17, 19)])
        self.assertEqual(fun, [prop_body, fun_body, main_body])
