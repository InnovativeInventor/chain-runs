import typer
import os
import tqdm
import pandas as pd
import geopandas as gpd
import yaml
import random
from gerrychain.accept import always_accept
from gerrychain import Graph, Partition, Election
from gerrychain.updaters import Tally, cut_edges, perimeter, cut_edges_by_part
from gerrychain.tree import recursive_seed_part, bipartition_tree
from gerrychain import (GeographicPartition, Partition, Graph, MarkovChain,
                        proposals, updaters, constraints, accept, Election)
from gerrychain.proposals import recom
import pcompress
from division_aware import *
from functools import partial
from utils import autodetect_election_cols

def aggregate_proportionality(elections, dists, absolute=False):
    election_names = [x["name"] for x in elections]
    def updater(partition):
        proportionality_scores = []
        for election in election_names:
            rep_seat_share = partition[election].wins("rep") / dists
            rep_vote_share = partition[election].percent("rep")
            proportionality_scores.append(rep_seat_share - rep_vote_share)

        if absolute:
            return sum(proportionality_scores)
        else:
            return sum(map(abs, proportionality_scores))

    return updater

def create_updaters(state, graph, pop_col, dists, elections: bool = True, absolute: bool = False):
    updaters = {}
    updaters["population"] = Tally(pop_col, alias="population")
    saved_updaters = list(updaters.keys())

    if elections and os.path.isfile(f"{state}.yaml"):
        with open(f"{state}.yaml") as f:
            election_meta = yaml.load(f)

        for election in election_meta["elections"]:
            updaters[election["name"]] = Election(
                election["name"],
                {"dem": election["dem"], "rep": election["rep"]}
            )
        updaters["agg_prop"] = aggregate_proportionality(election_meta["elections"], dists, absolute=False)
        if absolute:
            updaters["agg_prop_abs"] = aggregate_proportionality(election_meta["elections"], dists, absolute=True)
            saved_updaters.append("agg_prop_abs")
        saved_updaters.append("agg_prop")
    elif elections and absolute:
        raise ValueError("Can not optimize partisan metrics for state without election data")

    return saved_updaters, updaters

def create_seed_partition(graph, pop_col, tolerance, dists, updaters):
    ideal_population = sum([graph.nodes[n][pop_col] for n in graph.nodes]) / dists
    result = recursive_seed_part(
        graph,
        range(dists),
        ideal_population,
        pop_col,
        tolerance,
        method=bipartition_tree,
        n = None,
        ceil = None
    )
    seed_partition = Partition(
        graph=graph,
        assignment=result,
        updaters=updaters
    )
    return seed_partition

def create_proposal(graph, pop_col, tolerance, dists, county_col: str = "COUNTYFP20"):
    ideal_population = sum([graph.nodes[n][pop_col] for n in graph.nodes]) / dists
    proposal = partial(
        recom,
        method = partial(division_bipartition_tree,
                division_tuples=[(county_col, 1)],
                first_check_division=True),
        pop_col=pop_col,
        pop_target=ideal_population,
        epsilon=tolerance,
        node_repeats=2
    )
    return proposal

def optimize_value(value, exp=1, minimize=False):
    def acceptance(partition):
        if minimize:
            other_score = partition[value]
            score = partition.parent[value]
        else:
            score = partition[value]
            other_score = partition.parent[value]
        if score > other_score:
            return True
        else:
            probability = (score/other_score)**exp

            if random.random() < probability:
                return True
            else:
                return False
    return acceptance


def main(state: str, steps: int, name: str, dists: int, optimize: str = "neutral", county_aware: bool = True, pop_col: str = "TOTPOP20", tolerance: float = 0.01):
    if not os.path.isfile(f"graphs/{state}_vtd20.json"):
        gdf = gpd.read_file(f"/home/max/git/vtd-migration/products/{state}_vtd20.shp")
        graph = Graph.from_geodataframe(gdf)
        graph.to_json(f"graphs/{state}_vtd20.json")

    else:
        graph = Graph.from_json(f"graphs/{state}_vtd20.json")

    counties, nodes_by_county = get_divisions(graph, 'COUNTYFP20')

    if "abs" in optimize:
        saved_updaters, updaters = create_updaters(state, graph, pop_col, dists, elections=True, absolute=True)
    else:
        saved_updaters, updaters = create_updaters(state, graph, pop_col, dists, elections=("prop" in optimize))

    try:
        seed_partition = create_seed_partition(graph, pop_col, tolerance, dists, updaters)
    except KeyError:
        print(state)
        raise

    constraint = constraints.within_percent_of_ideal_population(seed_partition, tolerance)
    proposal = create_proposal(graph, pop_col, tolerance, dists)

    if optimize == "neutral":
        chain = MarkovChain(
            proposal = proposal,
            constraints = [constraint],
            accept= always_accept,
            initial_state = seed_partition,
            total_steps = steps
        )
    elif optimize == "agg_prop":
        chain = MarkovChain(
            proposal = proposal,
            constraints = [constraint],
            accept= optimize_value("agg_prop", minimize=True),
            initial_state = seed_partition,
            total_steps = steps
        )
    elif optimize == "agg_prop_abs":
        chain = MarkovChain(
            proposal = proposal,
            constraints = [constraint],
            accept= optimize_value("agg_prop", minimize=True),
            initial_state = seed_partition,
            total_steps = steps
        )

    metrics = {k: [] for k in saved_updaters}

    filename = f"{state}-{dists}-{optimize}-{county_aware}-{steps}-{name}"
    for partition in tqdm.tqdm(pcompress.Record(chain, f"results/{filename}.chain"), total=steps):
        for key in saved_updaters:
            metrics[key].append(partition[key])

    metric_output = pd.DataFrame(metrics)
    metric_output.to_csv(f"results/{filename}.csv")

if __name__ == "__main__":
    typer.run(main)
