import unittest
import os

from .function_extractor import FunctionExtractor


def read_file(filename):
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), filename), "r", encoding="utf-8") as fd:
        res = fd.read()
    return res

class TestParser(unittest.TestCase):
    def fun_case(self, lang, filename, fun_infos):
        content = read_file(filename)
        fun_lines, fun = FunctionExtractor.get_functions(content, lang)
        funcs_bounds = [(fun_info["start_line"], fun_info["end_line"]) for fun_info in fun_infos]
        self.assertEqual(fun_lines, funcs_bounds)
        funcs = [fun_info["body"] for fun_info in fun_infos]
        self.assertEqual(fun, funcs)
    
    def test_c_file(self):
        fun_body = """static void glfw_key_callback(int key, int scancode, int action, int mod){
  if(glfw_key_callback){
    // Comment here
    input_event_queue->push(inputaction);
  }
  printf("%s", "asciiじゃない文字");
}"""
        fun_infos = [{
            "body": fun_body,
            "start_line": 4,
            "end_line": 10
        }]
        self.fun_case("c", "tests/fun.c", fun_infos)

    def test_c_file_with_main(self):
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
        fun_infos = [{
            "body": fun_body,
            "start_line": 4,
            "end_line": 10
        },{
            "body": main_body,
            "start_line": 12,
            "end_line": 15
        }]
        self.fun_case("c", "tests/main.c", fun_infos)

    def test_cpp_file(self):
        fun_body = """void dfs(int v) {
    for (int to : g[v]) {
        t.push_back(to);
        dfs(to);
    }
}"""
        fun_infos = [{
            "body": fun_body,
            "start_line": 6,
            "end_line": 11
        }]
        self.fun_case("cpp", "tests/fun.cpp", fun_infos)

    def test_cpp_file_with_main(self):
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
        fun_infos = [{
            "body": fun_body,
            "start_line": 8,
            "end_line": 13
        },{
            "body": main_body,
            "start_line": 15,
            "end_line": 23
        }]
        self.fun_case("cpp", "tests/main.cpp", fun_infos)

    def test_java_file(self):
        main_body = """public static void main(String[] args) {
        System.out.println(приветМир());
    }"""
        fun_body = """private static String приветМир() {
    	return "Hello, World!";
    }"""
        fun_infos = [{
            "body": fun_body,
            "start_line": 1,
            "end_line": 3
        },{
            "body": main_body,
            "start_line": 5,
            "end_line": 7
        }]
        self.fun_case("java", "tests/main.java", fun_infos)

    def test_csharp_file(self):
        prop_body = "public static WindowsElement Window => session.FindElementByClassName();"
        fun_body = """public int AddNumbers(int number1, int number2) {
            int result = number1 + number2;
            return result;
        }"""
        fun_infos = [{
            "body": prop_body,
            "start_line": 7,
            "end_line": 7
        },{
            "body": main_body,
            "start_line": 13,
            "end_line": 16
        }]
        self.fun_case("c_sharp", "tests/fun.cs", fun_infos)

    def test_csharp_file_with_main(self):
        prop_body = "public static WindowsElement Window => session.FindElementByClassName();"
        fun_body = """public int AddNumbers(int number1, int number2) {
            int result = number1 + number2;
            return result;
        }"""
        main_body = """public static void int main(String[] args) {
            return 0;
        }"""
        fun_infos = [{
            "body": prop_body,
            "start_line": 6,
            "end_line": 6
        },{
            "body": fun_body,
            "start_line": 10,
            "end_line": 13
        },{
            "body": main_body,
            "start_line": 17,
            "end_line": 19
        }]
        self.fun_case("c_sharp", "tests/main.cs", fun_infos)
