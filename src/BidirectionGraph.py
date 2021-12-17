import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import networkx.algorithms.community as community
import plotly.graph_objs as go
from chart_studio import plotly
from plotly.offline import iplot
import matplotlib
import glob, os


def load_dumped_quotes(directory):
    """
    The function takes as input the directory where the dumped quotes are stored
    and gives as output the edge information to construct the multiedge-directed graph
    """
    os.chdir(directory)
    quotes_df = pd.DataFrame()
    for file in glob.glob("*.json"):
        men_df = pd.read_json(file, lines=True)
        men_df_grouped = (
            men_df.groupby(["mentioner", "mentioned"])
            .agg({"sentiment": "mean"})
            .reset_index()
        )
        men_df_grouped["topic_index"] = (
            men_df.groupby(["mentioner", "mentioned"])["topic_index"]
            .agg(lambda x: pd.Series.mode(x).iat[0])
            .reset_index()["topic_index"]
        )
        men_df_weight = (
            men_df.groupby(["mentioner", "mentioned"])
            .size()
            .reset_index(name="weight")
        )
        men_df_grouped["weight"] = men_df_weight["weight"]
        quotes_df = pd.concat([quotes_df, men_df_grouped], axis=0)
    quotes_df_final = (
        quotes_df.groupby(["mentioner", "mentioned"])
        .agg({"weight": "sum"})
        .reset_index()
    )
    quotes_df_final["sentiment"] = (
        quotes_df.groupby(["mentioner", "mentioned"])
        .apply(
            lambda x: pd.Series(
                [np.average(x["sentiment"], weights=x["weight"])]
            )
        )
        .reset_index()[0]
    )
    quotes_df_final["topic_index"] = (
        quotes_df.groupby(["mentioner", "mentioned"])["topic_index"]
        .agg(lambda x: pd.Series.mode(x).iat[0])
        .reset_index()["topic_index"]
    )
    quotes_df_final["topic_index"] = quotes_df_final["topic_index"].apply(
        topic_reclustering
    )
    quotes_df_0 = quotes_df_final[quotes_df_final["topic_index"] == 0]
    quotes_df_1 = quotes_df_final[quotes_df_final["topic_index"] == 1]
    quotes_df_2 = quotes_df_final[quotes_df_final["topic_index"] == 2]
    quotes_df_3 = quotes_df_final[quotes_df_final["topic_index"] == 3]
    quotes_df_4 = quotes_df_final[quotes_df_final["topic_index"] == 4]
    quotes_df_all = [
        quotes_df_0,
        quotes_df_1,
        quotes_df_2,
        quotes_df_3,
        quotes_df_4,
    ]
    return quotes_df_all


def construct_network_by_topic(quotes_df_all, catalogue_df):

    """
    The function takes as input the edges list for multiedge-directed graph and
    construct networks for each topics
    """
    G_all = []
    for men_df_grouped in quotes_df_all:
        G = nx.MultiDiGraph()
        for i, row in men_df_grouped.iterrows():
            if not G.has_node(row.mentioner):
                if row.mentioner.lower() in catalogue_df.name_low.values:
                    name = catalogue_df.loc[
                        catalogue_df["name_low"] == row.mentioner.lower()
                    ].name.values[0]
                    if not G.has_node(name):
                        G.add_node(name)
                        G.nodes[name]["party"] = catalogue_df.loc[
                            catalogue_df["name_low"] == row.mentioner.lower()
                        ].parties.values[0]
                        G.nodes[name]["nparty"] = (
                            0
                            if G.nodes[name]["party"] == "Democratic Party"
                            else 1
                        )

            if not G.has_node(row.mentioned):
                if row.mentioned in catalogue_df.name.values:
                    name = catalogue_df.loc[
                        catalogue_df["name_low"] == row.mentioned.lower()
                    ].name.values[0]
                    if not G.has_node(name):
                        G.add_node(name)
                        G.nodes[name]["party"] = catalogue_df.loc[
                            catalogue_df["name_low"] == row.mentioned.lower()
                        ].parties.values[0]
                        G.nodes[name]["nparty"] = (
                            0
                            if G.nodes[name]["party"] == "Democratic Party"
                            else 1
                        )

            if (
                row.mentioner in catalogue_df.name.values
                and row.mentioned in catalogue_df.name.values
            ):
                G.add_edge(
                    row.mentioner,
                    row.mentioned,
                    weight=row.weight,
                    sentiment=row.sentiment,
                )
        G_all.append(G)
    return G_all


def get_plotting_info(G_all):
    """
    The function takes as input the generated networks for each topics,
    filters out the 20 most significant nodes,
    outputs the edges, nodes, indexes for visibility in plotting,
    and the subnetworks, layouts, labels and colormaps.

    """
    g_centr_parts_all = []
    Laycentr_all = []
    labels_centr_all = []
    colmap_centr_all = []
    edges = []
    nodes = []
    for G in G_all:
        communities = community.kernighan_lin_bisection(
            G.to_undirected(), seed=42
        )
        g0 = G.subgraph(communities[0])
        centr0 = nx.degree_centrality(g0)
        sorted_centr0 = [
            x[0]
            for x in sorted(centr0.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]
        ]
        g1 = G.subgraph(communities[1])
        centr1 = nx.degree_centrality(g1)
        sorted_centr1 = [
            x[0]
            for x in sorted(centr1.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]
        ]
        sorted_centers = []
        sorted_centers.extend(sorted_centr0)
        sorted_centers.extend(sorted_centr1)
        g_centr_parts = G.subgraph(sorted_centers)
        Laycentr = nx.random_layout(g_centr_parts)
        labels_centr = [n for n in g_centr_parts.nodes()]
        colors = ["blue", "red"]
        colmap_centr = ["black"] * nx.number_of_nodes(g_centr_parts)
        counter = 0
        for i, n in enumerate(sorted_centr0):
            colmap_centr[i] = colors[0]
        for i, n in enumerate(sorted_centr1):
            colmap_centr[i + len(sorted_centr0)] = colors[1]
        g_centr_parts_all.append(g_centr_parts)
        Laycentr_all.append(Laycentr)
        labels_centr_all.append(labels_centr)
        colmap_centr_all.append(colmap_centr)
        edges.append(g_centr_parts.number_of_edges())
        nodes.append(g_centr_parts.number_of_nodes())
    index = [
        0,
        edges[0] + 1,
        sum(edges[0:2]) + 2,
        sum(edges[0:3]) + 3,
        sum(edges[0:4]) + 4,
    ]
    return (
        edges,
        nodes,
        index,
        g_centr_parts_all,
        Laycentr_all,
        labels_centr_all,
        colmap_centr_all,
    )


def topic_reclustering(x):
    """
    sub_clustering of topics that have similar themes
    """
    if x == 0 or x == 4:
        return 0
    elif x == 1:
        return 1
    elif x == 2:
        return 2
    elif x == 3:
        return 3
    elif x == 5:
        return 4
    else:
        return 5


def interpret_topic(x):
    """
    interpret topic integers into names
    """
    if x == 0:
        return "Scandal"
    elif x == 1:
        return "Terrorisim"
    elif x == 2:
        return "Election"
    elif x == 3:
        return "Geopolitical"
    elif x == 4:
        return "Financial"
    else:
        return "Legal System"


def plotly_graph_bar(
    g, L, labels, colormap, edges, nodes, index
):  # CF: m_y mention_y dataframe containing index of nodes, edges to use

    # CF: m_y is mention_y dataframe containing index of nodes, edges to use, index to count from for each plot, etc.
    # this datafarme is useful in toggling visibility of nodes/edges by maneuvering the visibility of corresponding index

    scatters = []
    # CF: initialize scatters list to store all plot [node,node,node,node,edge,node,node,node,edge....]

    for j in range(
        len(g)
    ):  # CF: embed codes in a loop to interate through years
        edge_index = 0
        node_index = 0
        Xe = []
        Ye = []
        for e in g[j].edges():
            Xe += [[L[j][e[0]][0], L[j][e[1]][0], None]]
            Ye += [[L[j][e[0]][1], L[j][e[1]][1], None]]
        edge_count = edges[
            j
        ]  # CF: get edge indexes to use from m_y for each year
        node_count = nodes[
            j
        ]  # CF: get node indexes to use from m_y for each year
        # add edges
        for i in range(0, edge_count):
            scatters.append(
                go.Scatter(
                    x=Xe[i],
                    y=Ye[i],
                    mode="lines",
                    line=dict(
                        shape="spline",
                        width=list(
                            nx.get_edge_attributes(g[j], "weight").values()
                        )[i]
                        ** 0.25,
                        color="mediumaquamarine",
                    ),
                )
            )
        Xv = [L[j][k][0] for k in list(g[j].nodes())]
        Yv = [L[j][k][1] for k in list(g[j].nodes())]
        # add nodes
        try:
            scatters.append(
                go.Scatter(
                    x=Xv[node_index : node_index + node_count],
                    y=Yv[node_index : node_index + node_count],
                    mode="markers",
                    marker=dict(
                        color=colormap[j][
                            node_index : node_index + node_count
                        ],
                        size=14,  # [np.log(g[i].degree[v])*200 + 5 for v in g[i]][:node_count],#[np.log(g[i].degree[v])*400 + 5 for v in g[i]]
                        line=dict(
                            color=colormap[j][
                                node_index : node_index + node_count
                            ],
                            width=2,
                        ),
                    ),
                    hovertemplate=[
                        label + "<extra></extra>" for label in labels[j]
                    ],
                )
            )
        except:
            print(i)

    axis = dict(
        showbackground=False,
        showline=False,
        zeroline=False,
        showgrid=False,
        showticklabels=False,
        title="",
        visible=False,
    )
    layout = go.Layout(
        width=1000,
        height=1000,
        showlegend=False,
        scene=dict(
            xaxis=dict(axis),
            yaxis=dict(axis),
        ),
        margin=dict(t=100),
        hovermode="closest",
        paper_bgcolor="rgba(255,255,255,255)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig = go.Figure(data=scatters, layout=layout)

    # list of buttons
    b_l = []
    # iterate through years to write into button list and slider
    for i in range(len(g)):
        # index of scatter plot to start from in current year
        scatter_index = index[i]
        # total number of scatter plot to go thorugh for current year
        scatter_count = int(1 + edges[i])
        # initialize all visibility to false
        l_visable = [False] * (sum(edges) + len(nodes))
        # label
        topic = interpret_topic(i)
        # update visibility
        for j in range(scatter_count):
            l_visable[
                scatter_index + j
            ] = True  # set all records starting from scatter index in range edge_count to True
        l = dict(
            label=topic,
            method="update",
            args=[
                {"visible": l_visable},
                {
                    "title": topic,
                    "annotations": [
                        dict(
                            ax=(L[i][edge[0]][0] + L[i][edge[1]][0]) / 2,
                            ay=(L[i][edge[0]][1] + L[i][edge[1]][1]) / 2,
                            axref="x",
                            ayref="y",
                            x=(L[i][edge[1]][0] * 3 + L[i][edge[0]][0]) / 4,
                            y=(L[i][edge[1]][1] * 3 + L[i][edge[0]][1]) / 4,
                            xref="x",
                            yref="y",
                            showarrow=True,
                            arrowcolor="rgb"
                            + str(
                                matplotlib.colors.to_rgb(
                                    matplotlib.cm.coolwarm(
                                        (
                                            np.sign(
                                                g[i].get_edge_data(
                                                    u=edge[0], v=edge[1]
                                                )[0]["sentiment"]
                                            )
                                            * np.power(
                                                abs(
                                                    g[i].get_edge_data(
                                                        u=edge[0], v=edge[1]
                                                    )[0]["sentiment"]
                                                ),
                                                0.5,
                                            )
                                            + 1
                                        )
                                        / 2
                                    )
                                )
                            ),
                            arrowhead=2,
                            arrowsize=np.log(
                                g[i].get_edge_data(u=edge[0], v=edge[1])[0][
                                    "weight"
                                ]
                            ),
                            arrowwidth=1,
                            opacity=1,
                        )
                        for edge in g[i].edges
                    ],
                },
            ],
        )
        b_l.append(l)

    # add drop_down list to figure with button list configuration dictionary
    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=b_l,
            )
        ]
    )

    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.write_html("topic_sentiment.html")
    iplot(fig)
