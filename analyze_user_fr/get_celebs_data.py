import psycopg2
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import pickle
engine = create_engine('postgresql://yoni:dordordor@voila-aurora-cluster.cluster-ck82h9f9wsbf.us-east-1.rds.amazonaws.com:5432/dummy_users')
engine.connect()
table_df = pd.read_sql_table(
    'celebs_fr_data',
    con=engine
)
table_df.fr_data = table_df.fr_data.apply(pickle.loads).apply(np.array)
table_df.to_json('celebs_data.json')
# with open('all_celebs_data.pickle', 'wb') as f:
#     pickle.dump(table_df, f)
# import numpy as np
# from pandas import DataFrame
# import pickle
# with open('all_celebs_data.pickle', 'rb') as f:
#     all_celebs_data = pickle.load(f)
#
# embeddings = all_celebs_data.iloc[0].fr_data
# def get_most_lookalike_celebs(embeddings, num_celebs=20):
#     all_celeb_embeddings = np.stack(all_celebs_data.fr_data, axis=0)
#     distances = np.linalg.norm(embeddings - all_celeb_embeddings, axis=1)
#     name_distances = DataFrame({'distance': distances,'celebname': all_celebs_data.celebname})
#     name_distances.sort_values(by=['distance'], inplace=True)
#     return name_distances[0:num_celebs].to_dict(orient='records')
#
#
#
# print(get_most_lookalike_celebs(embeddings=embeddings))