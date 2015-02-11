#ifndef __MA_H__
#define __MA_H__

#include "price_data.h"
float ma_g(__global PriceData* raw, unsigned int start, unsigned int count,
         const char field);
float ma_l(__local PriceData* raw, unsigned int start, unsigned int count,
         const char field);
float ma(PriceData* raw, unsigned int start, unsigned int count,
         const char field);
#endif
