import pandas as pd
import bz2
import time
from qwikidata.entity import WikidataItem
from qwikidata.linked_data_interface import get_entity_dict_from_api

'''
    The interpretation is done in 3 ways
    single qid interpretation (gender: take the latest)
    list qid interpretation (candidacy_election, parties) (take all from latest to oldest)
    list in list qid interpretation (position_held) (with a list of [position name, start date (if present), end date (if present)])
'''

def interpret_qids(WIKI_DATA_FILTERED, Q_catalogue, WIKI_DATA_FILTERED_LABELED, WIKI_DATA_FILTERED_MISSINGQ, single_interpret, list_interpret, listlist_interpret, verbose = False):
    '''
    Function takes as input the path for dumped politician catalogue (WIKI_DATA_FILTERED),
    the qid mapping catalogue (Q_catalogue) (as panda dataframe)
    and interpreted all qids in the politician catalogue into corresponding names.
    The interpreted catalogue is dumped to WIKI_DATA_FILTERED_LABELED
    if there are missing values that cannot be found in Q_catalogue,
    leave the unknown QIDs as they are in the intrepreted files,
    and store all unknown QIDs into WIKI_DATA_FILTERED_MISSINGQ.
    If verbose is True, print all unknown QIDs and the interpreted records at runtime.
    '''
    Q_catalogue = pd.read_csv(Q_catalogue, compression='bz2', index_col='QID').drop(columns='Description')
    global Q_catalogue_global, Unrecorded_Q, verbose_global
    Q_catalogue_global = Q_catalogue
    verbose_global = verbose
    CHUNKSIZE = 1000
    Unrecorded_Q = []
    with bz2.open(WIKI_DATA_FILTERED_LABELED, 'wb') as out_path_labeled:
        with bz2.open(WIKI_DATA_FILTERED_MISSINGQ, 'wb') as out_path_missingq:
            with pd.read_json(WIKI_DATA_FILTERED, lines=True, compression='bz2', chunksize=CHUNKSIZE) as df_reader:
                for chunk in df_reader:
                    t1=time.time()
                    chunk['gender'] = chunk['gender'].apply(single_interpret)
                    chunk['parties'] = chunk['parties'].apply(list_interpret)
                    chunk['candidacy_election'] = chunk['candidacy_election'].apply(list_interpret)
                    #chunk['religion'] = chunk['religion'].apply(list_interpret)
                    #religion property in wikipedia is messed up with instances like churches, shrines etc. better filter this another way
                    try:
                        chunk['positions held'] = chunk['positions held'].apply(listlist_interpret)
                    except:
                        chunk['positions held'] = chunk['positions held'].apply(list_interpret)
                    chunk['region'] = chunk['positions held'].apply(state_interpret)
                    chunk['state'] = chunk[chunk['nationality']=='Q30']['positions held'].apply(lambda x:x)
                    chunk.to_json(path_or_buf=out_path_labeled,orient='records',lines=True)
                    t2=time.time()
                    dt=t2-t1
                    print("Interpreted {} records and found {} undocumented qids [records/s: {:.2f}]".format(CHUNKSIZE,len(Unrecorded_Q), CHUNKSIZE / dt))
                pd.DataFrame(Unrecorded_Q).to_json(path_or_buf=out_path_missingq,orient='records',lines=True)
    return Q_catalogue_global

def single_interpret(x):
    """
    Function for single value interpretation. e.g. qid Record undocumented QIDs if not already recorded.
    """
    global Q_catalogue_global, Unrecorded_Q, verbose_global
    try:
        return Q_catalogue_global.loc[x]['Label']
    except KeyError as e:
        try:
            if verbose_global:
                print(f'Trying online interpretation for {x}.')
            y = WikidataItem(get_entity_dict_from_api(x)).get_label()
            if y=='':
                raise ValueError('returned null label')
            Q_catalogue_global = Q_catalogue_global.append(pd.DataFrame([[x,y]], columns=['QID','Label']).set_index('QID'))
            return y
        except:
            if verbose_global:
                print(f'Online interpretation failed for {x}.')
            if (x not in Unrecorded_Q):
                Unrecorded_Q.append(x)
                if verbose_global:
                    print (x)
            return x

def list_interpret(x):
    """
    Function for list interpretation. e.g. [qid1,qid2] Record undocumented QIDs if not already recorded.
    """
    global Q_catalogue_global, Unrecorded_Q, verbose_global
    tmp = []
    for i in x:
        try:
            tmp.append(Q_catalogue_global.loc[i]['Label'])
        except KeyError as e:
            try:
                if verbose_global:
                    print(f'Trying online interpretation for {i}.')
                y = WikidataItem(get_entity_dict_from_api(i)).get_label()
                if y=='':
                    raise ValueError('returned null label')
                Q_catalogue_global = Q_catalogue_global.append(pd.DataFrame([[i,y]], columns=['QID','Label']).set_index('QID'))
                tmp.append(y)
            except:
                if verbose_global:
                    print(f'Online interpretation failed for {i}.')
                tmp.append(i)
                if (i not in Unrecorded_Q):
                    Unrecorded_Q.append(i)
                    if verbose_global:
                        print (i)
    return tmp

def listlist_interpret(x):
    """
    Function for list interpretation. e.g. [[qid1,time1-1,time1-2],[qid2,time2-1,time2-2] Record undocumented QIDs if not already recorded.
    """
    global Q_catalogue_global, Unrecorded_Q, verbose_global
    tmp = []
    for i in x:
        tmp1 = []
        try:
            tmp1.append(Q_catalogue_global.loc[i[0]]['Label'])
        except KeyError as e:
            try:
                if verbose_global:
                    print(f'Trying online interpretation for {i[0]}.')
                y = WikidataItem(get_entity_dict_from_api(i[0])).get_label()
                if y=='':
                    raise ValueError('returned null label')
                Q_catalogue_global = Q_catalogue_global.append(pd.DataFrame([[i[0],y]], columns=['QID','Label']).set_index('QID'))
                tmp1.append(y)
            except:
                if verbose_global:
                    print(f'Online interpretation failed for {i[0]}.')
                tmp1.append(i[0])
                if (i[0] not in Unrecorded_Q):
                    Unrecorded_Q.append(i[0])
                    if verbose_global:
                        print (i[0])
        tmp1.append(i[1:2])
        tmp.append(tmp1)
    return tmp

def region_interpret(x):
    """
    Function for list interpretation. e.g. [[qid1,time1-1,time1-2],[qid2,time2-1,time2-2] Record undocumented QIDs if not already recorded.
    """
    tmp = ''
    for i in x:
        try:
            tmp = locationtagger.find_locations(text = i[0]).regions
        except KeyError as e:
            pass
    return tmp

def state_interpret(x):
    """
    Function for list interpretation. e.g. [[qid1,time1-1,time1-2],[qid2,time2-1,time2-2] Record undocumented QIDs if not already recorded.
    """
    tmp = []
    state_list =   ['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana',
'Iowa','Kansas','Kentucky','Louisiana,Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska',
'Nevada','New Hampshire','New Jersey','New Mexico','New York','North' 'Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island',
'South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West' 'Virginia','Wisconsin','Wyoming']
    for i in x:
        try:
            if i in state_list:
                tmp.append(i)
            else:
                pass
        except KeyError as e:
            pass
    return tmp