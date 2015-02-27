#include "price_data.h"
// TODO: find a way to include .h and compile with .c file.
#include "ma.c"

__kernel void test_donothing(const unsigned int aRange,
                             const unsigned int aRealSize,
                             __global PriceData* aIn,
                             __global PriceData* aOut)
{
  unsigned int gid = get_global_id(0);
  int startIdx = gid - aRange + 1;
  if (startIdx < 0 || gid >= aRealSize) {
    // we don't need to calculate ma without enough data.
    return;
  }

  aOut[gid].dataIndex = aIn[gid].dataIndex;
  aOut[gid].open = ma_g(aIn, startIdx, aRange, 'o');
  aOut[gid].high = ma_g(aIn, startIdx, aRange, 'h');
  aOut[gid].low = ma_g(aIn, startIdx, aRange, 'l');
  aOut[gid].close = ma_g(aIn, startIdx, aRange, 'c');
}
