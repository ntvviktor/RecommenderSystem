import pickle
import numpy as np
import pandas as pd 
from collections import Counter

# df = pd.read_csv("./movielens-20m-dataset/rating.csv")

# print(df.head())

# df.userId = df.userId - 1

# # map old movie index to new movie index
# unique_movie_ids = set(df.movieId.values)
# movie2idx = {}
# count = 0
# for movie_id in unique_movie_ids:
#     movie2idx[movie_id] = count
#     count += 1

# # add them to the data frame
# # takes awhile
# df['movie_idx'] = df.apply(lambda row: movie2idx[row.movieId], axis=1)

# df = df.drop(columns=['timestamp'])

# df.to_csv('./movielens-20m-dataset/edited_rating.csv', index=False)

df = pd.read_csv("./movielens-20m-dataset/edited_rating.csv")
print("Original dataframe size: ", len(df))

N = df.userId.max() + 1
M = df.movie_idx.max() + 1

user_ids_count = Counter(df.userId)
movie_ids_count = Counter(df.movie_idx)

n = 10000
m = 2000

user_ids= [u for u, c in user_ids_count.most_common(n)]
movie_ids = [m for m, c in movie_ids_count.most_common(m)]

df_small = df[df.userId.isin(user_ids) & df.movie_idx.isin(movie_ids)].copy()

new_user_id_map = {}
i = 0 

new_user_id_map = {}
i = 0
for old in user_ids:
  new_user_id_map[old] = i
  i += 1
print("i:", i)

new_movie_id_map = {}
j = 0
for old in movie_ids:
  new_movie_id_map[old] = j
  j += 1
print("j:", j)

print("Setting new ids")
df_small.loc[:, 'userId'] = df_small.apply(lambda row: new_user_id_map[row.userId], axis=1)
df_small.loc[:, 'movie_idx'] = df_small.apply(lambda row: new_movie_id_map[row.movie_idx], axis=1)
# df_small.drop(columns=['userId', 'movie_idx'])
# df_small.rename(index=str, columns={'new_userId': 'userId', 'new_movie_idx': 'movie_idx'})
print("max user id:", df_small.userId.max())
print("max movie id:", df_small.movie_idx.max())

print("small dataframe size:", len(df_small))
df_small.to_csv('./movielens-20m-dataset/small_rating.csv', index=False)