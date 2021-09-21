import glob
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import typer
import pcompress
from chains import *
from division_aware import num_division_splits
import gerrychain.metrics
import tqdm

def main(filename: str):
    metrics = {
        # "swing_tracker": [],
        "safe_count": [],
        "competitive_count": [],
        "split_count": [],
        "polsby": [],
        "cut_edges": [],
        "agg_prop": [],
        "agg_prop_abs": []
    }
    info = filename.split("/")[1].split("-")
    graph = Graph.from_json(f"graphs/{info[0]}_vtd20.json")
    if info[0] == "VA":
        saved_updaters, updaters = create_updaters(info[0], graph, "TOTPOP", int(info[1]), absolute=True)
    else:
        saved_updaters, updaters = create_updaters(info[0], graph, "TOTPOP20", int(info[1]), absolute=True)

    counties, nodes_by_county = get_divisions(graph, 'COUNTYFP20')

    election_cols = [k for k, v in updaters.items() if isinstance(v, Election)]

    for partition in tqdm.tqdm(pcompress.Replay(graph, filename, updaters = dict(updaters), geographic=True)):
        swing_tracker = [0] * len(partition.parts)
        for part in partition.parts.keys():
            times_won = 0
            for election_col in election_cols:
                election = partition[election_col].percents_for_party
                if election["rep"][part] >= election["dem"][part]:
                    times_won += 1
            swing_tracker[times_won] += 1

        split_count = num_division_splits(graph,partition,counties,nodes_by_county)
        polsby = sum(gerrychain.metrics.polsby_popper(partition).values()) / len(partition.parts)
        cut_edges = len(partition["cut_edges"])

        # metrics["swing_tracker"].append(swing_tracker)
        metrics["safe_count"].append(swing_tracker[0] + swing_tracker[-1])
        metrics["competitive_count"].append(sum(swing_tracker) - swing_tracker[0] - swing_tracker[-1])
        metrics["split_count"].append(split_count)
        metrics["polsby"].append(polsby)
        metrics["cut_edges"].append(cut_edges)
        metrics["agg_prop"].append(partition["agg_prop"])
        metrics["agg_prop_abs"].append(partition["agg_prop_abs"])

    metric_output = pd.DataFrame(metrics)

    metric_output.to_csv(f"{filename}.csv")
    for col in metrics:
        sns.histplot(metric_output[col])
        plt.savefig(f"{filename}-{col}.png")
        plt.close()
        plt.cla()
        plt.clf()

if __name__ == "__main__":
    typer.run(main)
