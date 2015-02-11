typedef struct {
  long f1;
  float f2;
  float f3;
  float f4;
  float f5;
} stRawData;

__kernel void ma(__global unsigned int* raw,
                 __global float* ma,
                 __global unsigned int* ma_length)
{
  
}

__kernel void test_donothing(const int aRange,
                             __global stRawData* aIn,
                             __global stRawData* aOut)
{
  unsigned int gid = get_global_id(0);
  int startIdx = gid - aRange + 1;
  if (startIdx < 0) {
    startIdx = 0;
  }
  float nCount = (gid-startIdx)+1;
  float f2temp = 0.0;
  float f3temp = 0.0;
  float f4temp = 0.0;
  float f5temp = 0.0;
  for (unsigned int i = startIdx; i <= gid; i++) {
    f2temp += aIn[i].f2;
    f3temp += aIn[i].f3;
    f4temp += aIn[i].f4;
    f5temp += aIn[i].f5;
  }
  f2temp /= nCount;
  f3temp /= nCount;
  f4temp /= nCount;
  f5temp /= nCount;
  aOut[gid].f1 = aIn[gid].f1;
  aOut[gid].f2 = f2temp;
  aOut[gid].f3 = f3temp;
  aOut[gid].f4 = f4temp;
  aOut[gid].f5 = f5temp;
}
