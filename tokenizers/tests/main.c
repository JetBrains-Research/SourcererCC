#include GLFW_INCLUDE_GLU
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
}
