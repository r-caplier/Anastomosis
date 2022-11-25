import os
import pandas as pd

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEV_NULL_PATH = "/dev/null"

LOGS_PATH = os.path.join(ROOT_PATH, "logs")
LOGS_DOWNLOAD_PATH = os.path.join(LOGS_PATH, "download")

DATA_RAW_PATH = os.path.join(ROOT_PATH, "data", "data_raw")
DATA_CLEAN_PATH = os.path.join(ROOT_PATH, "data", "data_clean")
ENTITIES_PATH = os.path.join(ROOT_PATH, "data", "entities")
RELATIONS_PATH = os.path.join(ROOT_PATH, "data", "relations")
PREDICTIONS_PATH = os.path.join(ROOT_PATH, "data", "predictions")
UMLS_PATH = os.path.join(ROOT_PATH, "data", "UMLS")

with open(os.path.join(ROOT_PATH, "data", "2021AB_SN", "SG")) as f:
    df_group = pd.read_csv(f, delimiter='|', names=["Group Abbrev",
                           "Group Name", "TUI", "Semantic Type"], index_col=False)
TUI_MAP = {}
for i, infos in df_group[["Group Abbrev", "TUI"]].iterrows():
    TUI_MAP[infos["TUI"]] = infos["Group Abbrev"]
