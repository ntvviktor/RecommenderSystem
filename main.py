import torch
import json
import csv
from Dataset import Dataset
from Evaluator import Evaluator
from CDAE import CDAE
from utils import train_model
from DataUtils import pre_preprocess_data

# Define hyperparameters, all of this can be fine tune to enhance the accuracy
data_path = "books/train_data.csv"
train_ratio = 0.7
hidden_dim = 50
corruption_ratio = 0.5
num_epochs = 100
batch_size = 512
testing_batch_size = 512
learning_rate = 0.001
early_stop = True
patience = 50
top_k = [5]
activation = "tanh"
device = torch.device("cpu")

columns = {"user_id": "user", "book_id": "item", "rating": "rating"}

save_path = "./books/user_item_rating.csv"
pre_preprocess_data(
    data_path=data_path,
    save_path=save_path,
    sep=",",
    columns=columns,
    min_ratings_threshold=60,
    min_ratings_count_threshold=50,
)

dataset = Dataset(
    data_path=save_path, save_path="training.json", sep=",", device=device
)

eval_pos, eval_target = dataset.eval_data()
item_popularity = dataset.item_popularity

evaluator = Evaluator(eval_pos, eval_target, item_popularity, top_k)
recommender_model = CDAE(
    num_users=dataset.num_users, num_items=dataset.num_items, hidden_dim=hidden_dim,
    corruption_ratio=corruption_ratio, activation=activation
)

cade_model, loss_recorder, metric_recorder = train_model(
    recommender_model,
    dataset,
    evaluator,
    batch_size=batch_size,
    test_batch_size=testing_batch_size,
    learning_rate=learning_rate,
    epochs=num_epochs,
    early_stop=early_stop,
)


with open("model_loss.json", "w") as f:
    json.dump(metric_recorder, f, ensure_ascii=False, indent=4)

with open("model_metric.csv", 'w', newline='') as f:
    wr = csv.writer(f, quoting=csv.QUOTE_NONE)
    wr.writerow(["loss"])
    wr.writerow(loss_recorder)

torch.save(cade_model.state_dict(), "cdae_recommender.pth")
