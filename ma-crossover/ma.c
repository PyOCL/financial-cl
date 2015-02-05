typedef struct {
  long f1;
  double f2;
  double f3;
  double f4;
  double f5;
} stRawData;

__kernel void ma(__global unsigned int* raw,
                 __global float* ma,
                 __global unsigned int* ma_length)
{
  
}

__kernel void test_donothing(__global stRawData* in,
                             __global stRawData* out)
{
  unsigned int gid = get_global_id(0);
  out[gid] = in[gid];
}