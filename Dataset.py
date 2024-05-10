import numpy as np
import torch

# Import utility scripts
from DataUtils import preprocess, load_data


class Dataset:
    """
    Dataset class implementation to preprocess and transform data into a trainable form
    """

    def __init__(self, data_path, save_path, sep, device, train_ratio=0.8) -> None:
        self.train_ratio = train_ratio
        self.num_negatives = 3
        self.device = device
        # Proprocess data
        preprocess(data_path, save_path, sep, train_ratio)
        (
            self.train_df,
            self.train_matrix,
            self.test_matrix,
            self.user_id_map,
            self.user_popularity,
            self.item_id_map,
            self.item_popularity,
            self.num_users,
            self.num_items,
        ) = load_data(save_path)

    def obtain_data_statistic(self) -> dict:
        """
        Return a dictionary representation of some basic statistic about the dataset
        """
        # Save preprocessed data
        ratings_per_user = list(self.user_popularity.values())
        num_ratings = np.sum(ratings_per_user)
        stat_info = {
            "Total users": self.num_users,
            "Total items": self.num_items,
            "Total ratings": num_ratings,
            "Sparsity ratio": (
                (1 - (num_ratings / (self.num_users * self.num_items))) * 100
            ),
            "Min/Max/Avg. ratings per users": [
                min(ratings_per_user),
                max(ratings_per_user),
                np.mean(ratings_per_user),
            ],
            "Number of train users": self.train_matrix.shape[0],
            "Number of train ratings": self.train_matrix.nnz,
            "Number of test users": self.test_matrix.shape[0],
            "Number of test ratings": self.test_matrix.nnz,
        }

        return stat_info

    def sparse_matrix_to_dict(self, sparse_matrix) -> dict:
        """
        Return dictionary that holds a data of a sparse_matrix
        """
        return_dict = {}
        num_users = sparse_matrix.shape[0]
        for u in range(num_users):
            items_u = sparse_matrix.indices[
                sparse_matrix.indptr[u] : sparse_matrix.indptr[u + 1]
            ]
            return_dict[u] = items_u.tolist()

        return return_dict

    def eval_data(self):
        return self.train_matrix, self.sparse_matrix_to_dict(self.test_matrix)

    def generate_pairwise_data_from_matrix(
        self, rating_matrix, num_negatives=1, p=None
    ) -> tuple[torch.LongTensor, torch.LongTensor, torch.LongTensor]:
        """
        Return a pairwise interation from matrix {(u, i) :1}
        """
        num_users, num_items = rating_matrix.shape

        users = []
        positives = []
        negatives = []
        for user in range(num_users):
            if p is None:
                start = rating_matrix.indptr[user]
                end = rating_matrix.indptr[user + 1]
                pos_index = rating_matrix.indices[start:end]
                num_positives = len(pos_index)
                if num_positives == 0:
                    print(
                        "[WARNING] user %d has 0 ratings. Not generating negative samples."
                        % user
                    )
                    continue

                num_all_negatives = num_items - num_positives
                prob = np.full(num_items, 1 / num_all_negatives)
                prob[pos_index] = 0.0

            neg_items = np.random.choice(
                num_items, num_positives * num_negatives, replace=True, p=prob
            )
            for i, pos in enumerate(pos_index):
                users += [user] * num_negatives
                positives += [pos] * num_negatives
                negatives += neg_items[
                    i * num_negatives : (i + 1) * num_negatives
                ].tolist()

        return (
            torch.LongTensor(users),
            torch.LongTensor(positives),
            torch.LongTensor(negatives),
        )
