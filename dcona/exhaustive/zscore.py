import numpy as np
import pandas as pd
import scipy.stats

import sys
import time
import tqdm
import json

import time

# Import python package
import core.extern
import core.utils

# Arg parser
import argparse


# Argument parser
parser = argparse.ArgumentParser()
parser.add_argument("config_path")
args = parser.parse_args()

# Load config file
CONFIG_PATH = args.config_path
config = json.load(open(CONFIG_PATH, "r"))

DATA_PATH = config["data_path"]
DESCRIPTION_PATH = config["description_path"]
# INTERACTION_PATH = config["interaction_path"]
OUTPUT_DIR_PATH = config["output_dir_path"]

REFERENCE_GROUP = config["reference_group"]
EXPERIMENTAL_GROUP = config["experimental_group"]

CORRELATION = config["correlation"]
ALTERNATIVE = config["alternative"]
SCORE = config["score"]

REPEATS_NUMBER = config["repeats_number"]
PROCESS_NUMBER = config["process_number"]

FDR_THRESHOLD = config["fdr_treshold"]

core.utils.check_directory_existence(OUTPUT_DIR_PATH)

# Main part
data_df = pd.read_csv(DATA_PATH, sep=",", index_col=0)
description_df = pd.read_csv(DESCRIPTION_PATH, sep=",")

if (CORRELATION == "spearman"):
    correlation = core.extern.spearmanr
elif (CORRELATION == "pearson"):
    correlation = core.extern.pearsonr
elif (CORRELATION == "spearman_test"):
    CORRELATION = "spearman"
    correlation = core.extern.spearmanr_test

interaction_df=None
source_indexes=None
target_indexes=None

reference_indexes = description_df.loc[
    description_df["Group"] == REFERENCE_GROUP,
    "Sample"
].to_list()
experimental_indexes = description_df.loc[
    description_df["Group"] == EXPERIMENTAL_GROUP,
    "Sample"
].to_list()

# Test mode
# data_df = data_df.iloc[:100]

print("Bootstrap phase")
start = time.time()

sources, scores, pvalues = \
core.extern.score_pipeline(
    data_df,
    reference_indexes,
    experimental_indexes,
    source_indexes,
    target_indexes,
    correlation=CORRELATION,
    score=SCORE,
    alternative=ALTERNATIVE,
    repeats_num=REPEATS_NUMBER,
    process_num=PROCESS_NUMBER
)
print("Computational time: {:.3f}".format(time.time() - start))

adjusted_pvalue = pvalues * len(pvalues) / \
    scipy.stats.rankdata(pvalues)
adjusted_pvalue[adjusted_pvalue > 1] = 1
adjusted_pvalue = adjusted_pvalue.flatten()

# Generate report
print("Report phase")
output_df = pd.DataFrame()
output_df["Source"] = data_df.index.to_numpy()[sources]
output_df["Score"] = scores
output_df["Pvalue"] = pvalues
output_df["FDR"] = adjusted_pvalue
output_df = output_df.sort_values(["FDR", "Pvalue"])

output_df.to_csv(
    OUTPUT_DIR_PATH.rstrip("/") + \
    "/{}_{}_{}_zscore.csv".format(CORRELATION, SCORE, ALTERNATIVE),
    sep=",",
    index=None
)
