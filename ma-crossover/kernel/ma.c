#include "ma.h"

float ma_g(__global PriceData* raw, unsigned int start, unsigned int count,
         const char field)
{
  float result = 0;
  unsigned int end = start + count;
  for (unsigned int i = start; i < end; i++) {
    switch (field) {
      case 'o':
        result += raw[i].open;
        break;
      case 'h':
        result += raw[i].high;
        break;
      case 'l':
        result += raw[i].low;
        break;
      case 'c':
        result += raw[i].close;
        break;
    }
  }
  return result / count;
}

float ma_l(__local PriceData* raw, unsigned int start, unsigned int count,
         const char field)
{
  float result = 0;
  unsigned int end = start + count;
  for (unsigned int i = start; i < end; i++) {
    switch (field) {
      case 'o':
        result += raw[i].open;
        break;
      case 'h':
        result += raw[i].high;
        break;
      case 'l':
        result += raw[i].low;
        break;
      case 'c':
        result += raw[i].close;
        break;
    }
  }
  return result / count;
}

float ma(PriceData* raw, unsigned int start, unsigned int count,
         const char field)
{
  float result = 0;
  unsigned int end = start + count;
  for (unsigned int i = start; i < end; i++) {
    switch (field) {
      case 'o':
        result += raw[i].open;
        break;
      case 'h':
        result += raw[i].high;
        break;
      case 'l':
        result += raw[i].low;
        break;
      case 'c':
        result += raw[i].close;
        break;
    }
  }
  return result / count;
}
