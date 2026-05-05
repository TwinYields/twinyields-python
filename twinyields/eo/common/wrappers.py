#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 11:05:36 2021

@author: Olli Nevalainen (Finnish Meteorological Institute)
"""
import sys
from .sentinel2 import S2_FILTER1
from .. import aws_cog

def get_s2_qi_and_data(aoi, req_params, qi_threshold=None, qi_filter=S2_FILTER1):
    items = aws_cog.search_s2_cogs(aoi, req_params)
    if items is None:
        qi_df = None
    else:
        qi_df = aws_cog.cog_get_s2_quality_info(aoi, req_params, items)

    if qi_df is None or qi_df.empty:
        print("No new observations for area %s" % aoi.name)
        dataset = None
    else:
        print("Retrieving S2 data...")
        dataset = aws_cog.cog_get_s2_band_data(
            aoi,
            req_params,
            items,
            qi_df,
            qi_threshold=qi_threshold,
            qi_filter=qi_filter,
        )

    return qi_df, dataset
