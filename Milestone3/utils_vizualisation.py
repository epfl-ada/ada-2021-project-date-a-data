from chart_studio import plotly
from plotly.offline import iplot
import plotly.graph_objs as go
import numpy as np
import networkx as nx

def scaler(list):
    return [i/sum(list) for i in list]

def plotly_graph(g,Layout,labels,parties='grey',colormap='white',centrality=10,title=''):
    Xv=[Layout[k][0] for k in list(g.nodes())]
    Yv=[Layout[k][1] for k in list(g.nodes())]
    Xe=[]
    Ye=[]
    for e in g.edges():
        Xe+=[[Layout[e[0]][0],Layout[e[1]][0],None]]
        Ye+=[[Layout[e[0]][1],Layout[e[1]][1],None]]
    scatters=[]
    for i in range(len(g.edges())):
        if list(nx.get_edge_attributes(g,'weight').values())[i] > 20:
            scatters.append(go.Scatter(x=Xe[i],y=Ye[i],mode='lines',
                        line=dict( 
                                shape='spline',
                                width=list(nx.get_edge_attributes(g,'weight').values())[i]**.2,
                                color='mediumaquamarine'),
                        ))
    scatters.append(go.Scatter(x=Xv,y=Yv,mode='markers',
            marker=dict(
                color=parties,
                size=[15+np.sqrt(i*15000) for i in centrality],
                opacity=1,
                line=dict(
                    color=colormap,
                    width=[2+np.sqrt(100*i) for i in centrality],
                )),
            hovertemplate=[label+'<extra></extra>' for label in labels]
             ))
    axis=dict(showbackground=False,
            showline=False,
            zeroline=False,
            showgrid=False,
            showticklabels=False,
            title='',
            visible=False
            )
    layout = go.Layout(
            width=1000,
            height=1000,
            showlegend=False,
            scene=dict(
                xaxis=dict(axis),
                yaxis=dict(axis),
            ),
        margin=dict(
            t=100
        ),
        hoverdistance=1,
        paper_bgcolor='rgba(255,255,255,255)',
        plot_bgcolor='rgba(0,0,0,0)',
            )
    fig=go.Figure(data=scatters,layout=layout)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(title_text=title, title_x=0.5)
    iplot(fig)

def plotly_graph_bipartite(g,Layout,labels,parties='grey',colormap='white',centrality=10,title=''):
    Xv=[Layout[k][0] for k in list(g.nodes())]
    Yv=[Layout[k][1] for k in list(g.nodes())]
    Xe=[]
    Ye=[]
    for e in g.edges():
        Xe+=[[Layout[e[0]][0],Layout[e[1]][0],None]]
        Ye+=[[Layout[e[0]][1],Layout[e[1]][1],None]]
    scatters=[]
    for i in range(len(g.edges())):
            scatters.append(go.Scatter(x=Xe[i],y=Ye[i],mode='lines',
                        line=dict( 
                                shape='spline',
                                width=list(nx.get_edge_attributes(g,'weight').values())[i]**.2,
                                color='mediumaquamarine'),
                        ))
    scatters.append(go.Scatter(x=Xv,y=Yv,mode='markers',
            marker=dict(
                color=parties,
                size=25,
                opacity=1,
                line=dict(
                    color=colormap,
                    width=4
                )),
            hovertemplate=[label+'<extra></extra>' for label in labels]
             ))
    axis=dict(showbackground=False,
            showline=False,
            zeroline=False,
            showgrid=False,
            showticklabels=False,
            title='',
            visible=False
            )
    layout = go.Layout(
            width=1000,
            height=1000,
            showlegend=False,
            scene=dict(
                xaxis=dict(axis),
                yaxis=dict(axis),
            ),
        margin=dict(
            t=100
        ),
        hoverdistance=1,
        paper_bgcolor='rgba(255,255,255,255)',
        plot_bgcolor='rgba(0,0,0,0)',
            )
    fig=go.Figure(data=scatters,layout=layout)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(title_text=title, title_x=0.5,autosize=True)
    iplot(fig)

def plotly_graph_self(g,Layout,labels,parties='grey',colormap='white',centrality=10,title=''):
    Xv=[Layout[k][0] for k in list(g.nodes())]
    Yv=[Layout[k][1] for k in list(g.nodes())]
    Xe=[]
    Ye=[]
    for e in g.edges():
        Xe+=[[Layout[e[0]][0],Layout[e[1]][0],None]]
        Ye+=[[Layout[e[0]][1],Layout[e[1]][1],None]]
    scatters=[]
    for i in range(len(g.edges())):
        if list(nx.get_edge_attributes(g,'weight').values())[i] > 20:
            scatters.append(go.Scatter(x=Xe[i],y=Ye[i],mode='lines',
                        line=dict( 
                                shape='spline',
                                width=list(nx.get_edge_attributes(g,'weight').values())[i]**.2,
                                color='mediumaquamarine'),
                        ))
    scatters.append(go.Scatter(x=Xv,y=Yv,mode='markers+text',
            marker=dict(
                color=parties,
                size=[15+np.sqrt(i*15000) for i in centrality],
                opacity=1,
                line=dict(
                    color=colormap,
                    width=[2+np.sqrt(100*i) for i in centrality],
                )),
            text=labels,
            textposition='top center',
            hovertemplate='none'
             ))
    axis=dict(showbackground=False,
            showline=False,
            zeroline=False,
            showgrid=False,
            showticklabels=False,
            title='',
            visible=False
            )
    layout = go.Layout(
            width=1000,
            height=1000,
            showlegend=False,
            hovermode=None,
            scene=dict(
                xaxis=dict(axis),
                yaxis=dict(axis),
            ),
        margin=dict(
            t=100
        ),
        hoverdistance=1,
        paper_bgcolor='rgba(255,255,255,255)',
        plot_bgcolor='rgba(0,0,0,0)',
            )
    fig=go.Figure(data=scatters,layout=layout)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(title_text=title, title_x=0.5)
    iplot(fig)
