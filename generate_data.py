from pathlib import Path
import os
import zipfile

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_ZIP_PATH = BASE_DIR / "data" / "EPA_UCMR5_PFAS_data.zip"

# EPA 2024 PFAS National Primary Drinking Water Regulation limits (ppt/ng/L).
EPA_LIMITS = {
    "PFOA": 4.0,
    "PFOS": 4.0,
    "PFHxS": 10.0,
    "PFNA": 10.0,
    "HFPO-DA (GenX)": 10.0,
    "PFBS": 2000.0,
}

UCMR_TO_REPORT_NAME = {
    "PFOA": "PFOA",
    "PFOS": "PFOS",
    "PFHxS": "PFHxS",
    "PFNA": "PFNA",
    "HFPO-DA": "HFPO-DA (GenX)",
    "PFBS": "PFBS",
}

FIPS_TO_STATE = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
    "60": "AS",
    "66": "GU",
    "69": "MP",
    "72": "PR",
    "78": "VI",
}

# UCMR5 public files only expose broad system size categories. These values are
# conservative lower-bound estimates used so the existing downstream analysis
# can keep its population_served field without treating it as exact population.
SIZE_POPULATION_LOWER_BOUND = {
    "L": 10000,
    "S": 3300,
}


def find_source_zip() -> Path:
    env_path = os.environ.get("UCMR5_ZIP_PATH")
    candidates = [
        Path(env_path).expanduser() if env_path else None,
        DEFAULT_ZIP_PATH,
    ]
    for path in candidates:
        if path and path.exists():
            return path

    raise FileNotFoundError(
        "EPA UCMR5 PFAS zip file not found. Set UCMR5_ZIP_PATH or place it at "
        f"{DEFAULT_ZIP_PATH}."
    )


def normalize_state(value: str) -> str:
    if pd.isna(value):
        return "Unknown"

    text = str(value).strip().upper()
    if text in FIPS_TO_STATE:
        return FIPS_TO_STATE[text]
    if text.zfill(2) in FIPS_TO_STATE:
        return FIPS_TO_STATE[text.zfill(2)]
    return text or "Unknown"


def load_zip_lookup(source_zip: Path) -> pd.DataFrame:
    with zipfile.ZipFile(source_zip) as zf:
        with zf.open("UCMR5_ZIPCodes.txt") as file:
            zip_df = pd.read_csv(file, sep="\t", dtype=str, encoding="latin1")

    zip_df["ZIPCODE"] = zip_df["ZIPCODE"].str.strip().str.zfill(5)
    zip_lookup = (
        zip_df.dropna(subset=["ZIPCODE"])
        .groupby("PWSID")["ZIPCODE"]
        .apply(lambda values: "|".join(sorted(set(values))))
        .rename("zip_codes")
        .reset_index()
    )
    return zip_lookup


def load_detected_regulated_pfas(source_zip: Path) -> pd.DataFrame:
    columns = [
        "PWSID",
        "PWSName",
        "Size",
        "State",
        "Contaminant",
        "AnalyticalResultsSign",
        "AnalyticalResultValue",
    ]
    regulated = set(UCMR_TO_REPORT_NAME)
    frames = []

    with zipfile.ZipFile(source_zip) as zf:
        with zf.open("UCMR5_All.txt") as file:
            for chunk in pd.read_csv(
                file,
                sep="\t",
                usecols=columns,
                dtype=str,
                chunksize=250_000,
                encoding="latin1",
            ):
                chunk = chunk[
                    chunk["Contaminant"].isin(regulated)
                    & chunk["AnalyticalResultsSign"].eq("=")
                    & chunk["AnalyticalResultValue"].notna()
                ].copy()

                if chunk.empty:
                    continue

                chunk["AnalyticalResultValue"] = pd.to_numeric(
                    chunk["AnalyticalResultValue"], errors="coerce"
                )
                chunk = chunk.dropna(subset=["AnalyticalResultValue"])
                frames.append(
                    chunk[
                        [
                            "PWSID",
                            "PWSName",
                            "Size",
                            "State",
                            "Contaminant",
                            "AnalyticalResultValue",
                        ]
                    ]
                )

    if not frames:
        return pd.DataFrame(
            columns=[
                "PWSID",
                "PWSName",
                "Size",
                "State",
                "Contaminant",
                "AnalyticalResultValue",
            ]
        )

    detections = pd.concat(frames, ignore_index=True)
    return (
        detections.groupby(
            ["PWSID", "PWSName", "Size", "State", "Contaminant"],
            dropna=False,
            as_index=False,
        )["AnalyticalResultValue"]
        .max()
        .rename(columns={"AnalyticalResultValue": "result_ug_l"})
    )


def build_report_dataset(source_zip: Path) -> pd.DataFrame:
    detections = load_detected_regulated_pfas(source_zip)
    zip_lookup = load_zip_lookup(source_zip)

    df = detections.merge(zip_lookup, on="PWSID", how="left")
    df["pfas_type"] = df["Contaminant"].map(UCMR_TO_REPORT_NAME)
    df["concentration_ppt"] = (df["result_ug_l"] * 1000).round(3)
    df["epa_limit_ppt"] = df["pfas_type"].map(EPA_LIMITS)
    df["exceeds_limit"] = df["concentration_ppt"] > df["epa_limit_ppt"]
    df["state"] = df["State"].apply(normalize_state)
    df["water_system"] = df["PWSName"].str.strip()
    df["city"] = df["water_system"]
    df["zip_codes"] = df["zip_codes"].fillna("")
    df["zip_code"] = df["zip_codes"].str.split("|").str[0]
    df["population_served"] = (
        df["Size"].str.upper().map(SIZE_POPULATION_LOWER_BOUND).fillna(0).astype(int)
    )
    df["system_size"] = df["Size"]
    df["pwsid"] = df["PWSID"]

    output_columns = [
        "state",
        "city",
        "water_system",
        "zip_code",
        "zip_codes",
        "pfas_type",
        "concentration_ppt",
        "epa_limit_ppt",
        "exceeds_limit",
        "population_served",
        "system_size",
        "pwsid",
    ]
    return df[output_columns].sort_values(
        ["state", "water_system", "pfas_type"], kind="stable"
    )


def main() -> None:
    source_zip = find_source_zip()
    df = build_report_dataset(source_zip)
    output_path = BASE_DIR / "pfas_data.csv"
    df.to_csv(output_path, index=False)

    exceeded = int(df["exceeds_limit"].sum())
    print(f"Source: {source_zip}")
    print(f"Total system-PFAS detection records: {len(df)}")
    print(f"Water systems covered: {df['pwsid'].nunique()}")
    print(f"States/territories covered: {df['state'].nunique()}")
    print(f"Records exceeding EPA limits: {exceeded}")
    print()
    print("First 10 rows:")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
