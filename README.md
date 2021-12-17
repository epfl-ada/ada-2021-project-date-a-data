# U_Cite: American politician network inferred from public quotations  
## [Data Story](https://irvin-mero.github.io/date_a_data/)
## Team: Date A Data
- Castiglione Thomas `thomas.castiglione@epfl.ch`
- Chuanfang Ning `chuangfang.ning@epfl.ch`
- Guoyuan Liu `guoyuan.liu@epfl.ch`
- Irvin Mero `irvin.merozambrano@epfl.ch`

## Repository structure
Files for Milestone3
```
.
├── Analysis_Visualisation.ipynb
├── Preprocessing.ipynb
├── README.md
├── data/
├── images/
├── model/
└── src/
```
There are 2 main notebooks doing repectively preprocessing and analysis of the data.
- `Preprocessing.ipynb`: processing pipeline from raw datasets to usable data for analysis and visualisation.
- `Analysis_Visualisation.ipynb`: Analysis of the processed data from last notebook with visualisations.
The src folder includes the utility functions necessary for running the main notebooks.

## Background
![plot](https://github.com/epfl-ada/ada-2021-project-date-a-data/blob/main/images/Headphoto.jpeg?raw=true)
It is well-known from public sentiment that the US has a bi-polar political landscape, with Democrats on one side and Republicans on the other. The project aims to verify and back up this bi-polarity by interpreting and visualizing the political mentions of Americam politicians in a network model. 


 
## Research Questions
With some preliminary analysis in Milestone 2, we found that 13% of the quotations are uttered by politicians. And 48% of the political quotations are from the US. With the rich political data in the dataset, we decide to analyze the network between politicians through their quotation and tell a datastory about the ecosystem of the political world focusing on the United States.

With Quotebank, we can extract the “mentioning” and “being mentioned” relationship among the politicians to build a political social network based on data from multiple news sources. This social network can be constructed on the domestic level including only American politicians and on the global level to show both the domestic and international network.

The polarization of the United States politics is already backed by multiple studies, but many of them is done indirectly via survey on ideology or public behavior change ([NW et al., 2014](https://www.pewresearch.org/politics/2014/06/12/political-polarization-in-the-american-public/); [Wilson et al., 2020](https://psycnet.apa.org/record/2020-78563-040)). 

The network on the individual politician level is a direct reflection of the political structure with quantitative metrics like centrality.


On a global level, some major events also occur during the time span of quotebank (2015 - 2020) like Brexit, the US-China trade war, COVID pandemic, etc., which could be interesting to see if it is reflected from the global political network.

## Methods

The politicians are considered as nodes and the mentions in between the politicians are considered as edges in the network model. Both the nodes and the edges of the network are analyzed to reveal the politician landscape.

The network is analyzed in-depth to reveal the node centrality, communities and self-loops. The sentiments and topics of mentions are analyzed as well with NLP methods. 

With this network model we tell a data story about the bi-directional politician network in terms of frequency, sentiment and topics. In conclusion, some assumptions are proved and some fun facts are found with the help of interactive network in the [data story](https://irvin-mero.github.io/date_a_data/).
 
##  Additional datasets
- [Partisan Audience Bias Scores](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/QAN5VX)
 
    This data set is made available from Harvard dataverse and contains 19023 domains with the bias score. The score is compiled from the sharing patterns by known Democrats and Republicans on Twitter.We plan to use the dataset to calibrate the source of quotation so that the distribution is centered and unbiased in terms of political ideology. This is relevant since we want to show an objective politician network that can reflect real situations instead of the potential bias from the media.
 
- [Wikidata](https://www.wikidata.org/wiki/Wikidata:Database_download)

    Wikidata is a free, structured database that serves as a general collection of knowledge. It is used to enrich the speakers in quotebank to include information like position, political party, nationality, date of death, etc. The size of the whole dump is over 100 GB and one query on it takes about 12 hours but it is manageable since one pass is adequate and the following analysis is done on much smaller subsets.
 
## Organization within the team
- All: composing data story.
- Chuanfang: Data preprocessing and pipeline; interactive bidirection plot
- Guoyuan: Sentimental analysis, topic extraction, media bias analysis.
- Irvin: Plots on US - Global political networks, web design for the data story.
- Thomas: Statistical analysis, interactive plots on US politician networks.

