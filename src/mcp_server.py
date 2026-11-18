"""MCP 服务端：用 Pandas 读取财务表并计算。"""
import json
from pathlib import Path

import pandas as pd
from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[1]
server = FastMCP("financial-table")


def calculate(path):
    df = pd.read_excel(path) if path.suffix == ".xlsx" else pd.read_csv(path)
    df.columns = df.columns.str.strip()
    amount = "gross_profit" if "gross_profit" in df else "cost"
    groups = ["company", "segment"] if "segment" in df else ["company"]
    columns = [*groups, "year", "revenue", amount, "unit", "source"]
    df = df[columns].copy()
    if df.empty or df.isna().any().any():
        raise ValueError("财务表为空或有缺失字段")
    for name in [*groups, "unit", "source"]:
        df[name] = df[name].astype(str).str.strip()
    years = pd.to_numeric(df["year"], errors="raise")
    if not years.mod(1).eq(0).all():
        raise ValueError("year 必须是整数年份")
    df["year"] = years.astype(int)
    factor = df["unit"].map({"元": 1, "万元": 10000, "亿元": 100000000})
    if factor.isna().any() or df.duplicated([*groups, "year"]).any():
        raise ValueError("金额单位未知或同一业务的年份重复")
    for name in ["revenue", amount]:
        df[name] = pd.to_numeric(df[name].astype(str).str.replace(",", ""), errors="raise") * factor
    if amount == "cost":
        df["gross_profit"] = (df["revenue"] - df["cost"]).round(2)
    df["unit"] = "元"
    df = df.sort_values([*groups, "year"])
    metrics = df.copy()
    previous = df.groupby(groups)["revenue"].shift()
    consecutive = df.groupby(groups)["year"].diff().eq(1)
    metrics["revenue_growth_pct"] = ((df["revenue"] / previous.replace(0, float("nan")) - 1) * 100).where(consecutive)
    metrics["gross_margin_pct"] = df["gross_profit"] / df["revenue"].replace(0, float("nan")) * 100
    # to_json 将无法计算的 NaN 转为 JSON null，而不是编造一个数值。
    return {"cleaned": json.loads(df.to_json(orient="records")),
            "metrics": json.loads(metrics.round(4).to_json(orient="records"))}


@server.tool()
def analyze_financials() -> dict[str, list[dict]]:
    """用深南电路年报的分产品收入和成本复算封装基板的营收同比与毛利率。"""
    return calculate(ROOT / "data" / "shennan_substrates.csv")


if __name__ == "__main__":
    server.run(transport="stdio")
