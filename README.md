# CS-401 Applied Data Analysis Project Folder

## Team: Date A Data
- Castiglione Thomas `thomas.castiglione@epfl.ch`
- Chuanfang Ning `chuangfang.ning@epfl.ch`
- Guoyuan Liu `guoyuan.liu@epfl.ch`
- Irvin Mero `irvin.merozambrano@epfl.ch`

## Abstract: 
*A 150 word description of the project idea and goals. What’s the motivation behind your project? What story would you like to tell, and why?*
## Research Questions
With some preliminary analysis, >>>>>>>link to analysis notebook [qid catalogue and dataset filter]], we find that 13% of the quotations are uttered by politicians. And 48% of the political quotations are from US. With the rich political data in the dataset, we decide to analyze the network between politicians when they quote something and tell a datastory about the ecosystem of the political world.
It has been widely discussed about the polarization of the United States society especially in terms of the political structure. The two major contemporary parties, namely the Republican Party and the Democratic Party are two obvious ends on the spectrum, and they are reported to be even more divided now. (NW et al., 2014; Wilson et al., 2020)
With Quotebank,  we plan to extract the “mentioning” and “being mentioned” relationship among the American politicians to build a political social network based on data from multiple news sources. This social network on the individual level could help to:

- Observe the overall political landscape of the United States. We can visually validate how divided the politicians are.
- Identify potential hubs in the social networks of politicians. The centrality analysis could reveal the structural importance of a node (person) in the network. (Borgatti et al., 2009)

## Proposed additional datasets
- Partisan Audience Bias Scores (Robertson et al., 2018)

    This data set is made available from Harvard dataverse and contains 19023 domains with the bias score. The score is compiled from the sharing patterns by known Democrats and Republicans on Twitter. The same dataset optionally contains other scores to validate the method. We plan to use the dataset to calibrate the source of quotation so that the distribution is centered and unbiased in terms of political ideology. This is relevant since we want to show an objective politician network that can reflect real situations instead of the potential bias from media.
- Wikidata
    >>>>>>>>
    *Source, Discuss data size and format if relevant. It is your responsibility to check that what you propose is feasible.*

## Methods
### A. Preprocessing: 
1. Analyze the latest wikidata dump, build a catalogue by filtering out alive politicians with their qids, names, alternative names, nationalities and parties. 
2. Use the catalogue to filter the Quotebank quotations from 2015 to 2020, which are uttered by politicians with known names, nationalities and parties. 
3. Calibrate the source of quotations according to the media bias score to have a neutral sampling.
4. Cluster the politicians in two ways, i.e. by their parties (national) and by their nationality (international).
5. Query the filtered quotebank data and pick out the quotation lines which include the names/alternative names of another politician(s).>>>>>>>
### B. Data analysis:
1. Build a network model with following structures. Nodes are US politicians and edges are the mentioning or being mentioned in publicity (represented by the quotebank). The edge weight denotes the frequency and for a clear diagram, only the top nodes with most connections are kept. 
2. Do network analysis and identify the hubs by picking out nodes with frequent connections to most modes. Identify communities by picking out nodes with same parties and closely connected. This could be done qualitatively by visual or quantitatively by centrality analysis.
3. Evolve the network connections from mentioning times to >>>>>>>

### C. Visualisation and Gitpage:
Visualize the network model in B.1 and add a function allowing users to track or untrack politicians in the graph according to their interest.


### Descriptive statistics to get:
For both world and usa dataset:
Number of politicians
Number of quotes per politicians distribution
?(Time distribution of the citations)
Check the equilibration of the citation (democrates vs republicans) with catalogue        (only keep democrates and republicans?)

## Proposed timeline
- Add bias value to the source (url).
- Implement efficient algorithm to pick up politician names in quotations from politician.
- Visualize the network.
- Write data story.
>>>>>>>

## Organization within the team
- Chuanfang:
- Guoyuan:
- Irvin:
- Thomas:


## Questions for TAs (optional)
* Add here any questions you have for us related to the proposed project*
