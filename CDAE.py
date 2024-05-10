import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class CDAE(nn.Module):
    """
    Collaborative Denoising Autoencoder Recommendation Model Implementation
    """

    def __init__(
        self,
        num_users,
        num_items,
        hidden_dim=50,
        activation="tanh",
        corruption_ratio=0.3,
        device="cpu",
    ):
        super().__init__()
        self.num_users = num_users
        self.num_items = num_items
        self.hidden_dim = hidden_dim
        self.activation = activation
        self.corruption_ratio = corruption_ratio
        self.device = torch.device(device)

        self.user_embedding = nn.Embedding(num_users, hidden_dim)
        self.encoder = nn.Linear(self.num_items, self.hidden_dim)
        self.decoder = nn.Linear(self.hidden_dim, self.num_items)
        self.to(self.device)

    def _apply_activation(self, activation, x):
        activation = activation.lower()
        if activation == "sigmoid":
            return F.sigmoid(x)
        elif activation == "tanh":
            return F.tanh(x)
        elif activation == "relu":
            return F.relu(x)
        else:
            raise NotImplementedError("Choose the right activation function")

    def forward(self, user_id, rating_matrix, apply_dropout=True):
        """
        Forward propagation step, the input layer of the Autoencoder
        args:
            user_id: id of user
            rating_matrix: user x item matrix
            apply_dropout: make two situation, at training time, set it to True to ovoid overfitting
            at inference time, set it to false
        """
        # normalize the rating matrix
        user_degree = torch.linalg.norm(rating_matrix, ord=2, dim=1).view(
            -1, 1
        )  # user, 1
        item_degree = torch.linalg.norm(rating_matrix, ord=2, dim=0).view(
            1, -1
        )  # 1, item
        normalize = torch.sqrt(user_degree @ item_degree)
        zero_mask = normalize == 0
        normalize = torch.masked_fill(normalize, zero_mask.bool(), 1e-10)
        normalized_rating_matrix = rating_matrix / normalize
        # corrupt the rating matrix
        if apply_dropout is True:
            normalized_rating_matrix = F.dropout(
                normalized_rating_matrix, self.corruption_ratio, training=self.training
            )
        # build the collaborative denoising autoencoder
        enc = self.encoder(normalized_rating_matrix) + self.user_embedding(user_id)
        enc = self._apply_activation(self.activation, enc)
        dec = self.decoder(enc)

        return torch.sigmoid(dec)

    def train_loop(self, dataset, optimizer, batch_size=512, verbose=True):
        self.train()
        # (user, item) rating pairs
        train_matrix = dataset.train_matrix

        num_training = train_matrix.shape[0]
        num_batches = int(np.ceil(num_training / batch_size))

        perm = np.random.permutation(num_training)
        loss = 0.0
        for b in range(num_batches):
            optimizer.zero_grad()

            if (b + 1) * batch_size >= num_training:
                batch_idx = perm[b * batch_size:]
            else:
                batch_idx = perm[b * batch_size: (b + 1) * batch_size]

            batch_matrix = torch.FloatTensor(train_matrix[batch_idx].toarray()).to(self.device)
            batch_idx = torch.LongTensor(batch_idx).to(self.device)
            pred_matrix = self.forward(batch_idx, batch_matrix)

            # Cross Entropy Loss
            batch_loss = nn.MSELoss(reduction="mean")(pred_matrix, batch_matrix)
            batch_loss.backward()
            optimizer.step()

            loss += batch_loss.item()

            if verbose and b % 50 == 0:
                print(f'({b}/{num_batches}) loss = {batch_loss.item():.4f}')
        return loss

    def predict(self, eval_pos, test_batch_size):
        """
        Predict the model on test set
        Args:
            eval_pos: position of the evaluated (test) item
            test_batch_size: batch size for test set
        -> numpy array predictions
        """
        with torch.no_grad():
            input_matrix = torch.FloatTensor(eval_pos.toarray()).to(self.device)
            preds = np.zeros_like(input_matrix)

            num_data = input_matrix.shape[0]
            # num_of_user x number of items is the shape of the input matrix
            num_batches = int(np.ceil(num_data / test_batch_size))
            # randomize the distint indexes
            perm = list(range(num_data))
            for b in range(num_batches):
                if (b + 1) * test_batch_size >= num_data:
                    batch_idx = perm[b * test_batch_size :]
                else:
                    batch_idx = perm[b * test_batch_size : (b + 1) * test_batch_size]
                test_batch_matrix = input_matrix[batch_idx]
                batch_idx = torch.LongTensor(batch_idx).to(self.device)
                batch_pred_matrix = self.forward(batch_idx, test_batch_matrix)
                batch_pred_matrix.masked_fill(test_batch_matrix.bool(), float("-inf"))
                preds[batch_idx] = batch_pred_matrix.detach().cpu().numpy()
        return preds
