#include <stdio.h>

#ifndef TRIDENT_OUTPUT
#define TRIDENT_OUTPUT(id, typestr, value) value
#endif

int main(int argc, char *argv[]) {
  int x = atoi(argv[1]);
  int a = 214748364 ;
  int b;
  if (__trident_choice("L9", "bool", (int[]){x, a}, (char*[]){"x", "a"}, 2, (int*[]){}, (char*[]){}, 0))  {
      return -1;
  }
  b = x * a;
  TRIDENT_OUTPUT("b", "i32", b);
  return 0;
}
