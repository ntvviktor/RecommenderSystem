import json
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.utils import shuffle
from datetime import datetime
from sortedcontainers import SortedList

with open('user2movie.json', 'rb') as f:
    user2movie = pickle.load(f)

with open('movie2user.json', 'rb') as f:
    movie2user = pickle.load(f)

with open('usermovie2rating.json', 'rb') as f:
    usermovie2rating = pickle.load(f)

with open('usermovie2rating_test.json', 'rb') as f:
    usermovie2rating_test = pickle.load(f)
  
number_of_users = np.max(list(user2movie.keys())) + 1
# the test set may contain movies the train set doesn't have data on
m1 = np.max(list(movie2user.keys()))
m2 = np.max([m for (u, m), r in usermovie2rating_test.items()])
number_of_movies = max(m1, m2) + 1
print("Number of users: ", number_of_users, "\nNumber of movies:", number_of_movies)

if number_of_users > 10000:
  print("N =", number_of_users, "are you sure you want to continue?")
  print("Comment out these lines if so...")
  exit()

# Implementation of recommendation algorithm
K = 25 
min_limit = 5
neighbors = []
averages = []
deviations = []
neighbors_json = []
for i in range(500):
    movies_i = user2movie[i]
    movies_i_set = set(movies_i)
    
    ratings_i = { m:usermovie2rating[i, m] for m in movies_i }
    avg_i = np.mean(list(ratings_i.values()))
    dev_i = { m:(rating - avg_i) for m, rating in ratings_i.items() }
    dev_i_values = np.array(list(dev_i.values()))
    sigma_i = np.sqrt(dev_i_values.dot(dev_i_values))
    
    averages.append(avg_i)
    deviations.append(dev_i)
    
    ls = SortedList()
    for j in range(500):
        if j != i:
            movies_j = user2movie[j]
            movies_j_set = set(movies_j)
            common_movies = (movies_i_set & movies_j_set) # intersection
            if len(common_movies) > min_limit:
                ratings_j = { movie:usermovie2rating[(j, movie)] for movie in movies_j }
                avg_j = np.mean(list(ratings_j.values()))
                dev_j = { movie:(rating - avg_j) for movie, rating in ratings_j.items() }
                dev_j_values = np.array(list(dev_j.values()))
                sigma_j = np.sqrt(dev_j_values.dot(dev_j_values))

                # calculate correlation coefficient
                numerator = sum(dev_i[m]*dev_j[m] for m in common_movies)
                w_ij = numerator / (sigma_i * sigma_j)
                
                ls.add((-w_ij, j))
                if len(ls) > K:
                    del ls[-1]
                    temp = ls.__repr__()
    
    temp = []
    for item in ls:
        temp.append(item)
        
    neighbors_json.append(temp)
    neighbors.append(ls)

params = {
	"neighbors": neighbors_json,
	"averages": averages,
	"deviations": deviations
}
json_obj = json.dumps(params, indent=4)


with open('parameters.json', 'w') as f:
    f.write(json_obj)

def predict(i, m):
    # calculate the weighted sum of deviations
    numerator = 0
    denominator = 0
    for neg_w, j in neighbors[i]:
        # remember, the weight is stored as its negative
        # so the negative of the negative weight is the positive weight
        try:
            numerator += -neg_w * deviations[j][m]
            denominator += abs(neg_w)
        except KeyError:
        # neighbor may not have rated the same movie
        # don't want to do dictionary lookup twice
        # so just throw exception
            pass

    if denominator == 0:
        prediction = averages[i]
    else:
        prediction = numerator / denominator + averages[i]
    prediction = min(5, prediction)
    prediction = max(0.5, prediction) # min rating is 0.5
    return prediction

train_predictions = []
train_targets = []
for (i, m), target in usermovie2rating.items():
	if i < 500:
		# calculate the prediction for this movie
		prediction = predict(i, m)

		# save the prediction and target
		train_predictions.append(prediction)
		train_targets.append(target)

test_predictions = []
test_targets = []
# same thing for test set
for (i, m), target in usermovie2rating_test.items():
	if i < 500:
		# calculate the prediction for this movie
		prediction = predict(i, m)
		if i == 10:
			break

		# save the prediction and target
		test_predictions.append(prediction)
		test_targets.append(target)

# calculate accuracy
def mse(p, t):
	p = np.array(p)
	t = np.array(t)
	return np.mean((p - t)**2)

print('train mse:', mse(train_predictions, train_targets))
print('test mse:', mse(test_predictions, test_targets))