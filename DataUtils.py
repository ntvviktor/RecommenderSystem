import pickle
import numpy as np
import pandas as pd
import scipy.sparse as sp


def load_data(data_path):
    """
    Function that load the processed data from `preprocess()` function
    arg: 
        data_path: the path of the json byte representation data
    """
    with open(data_path, "rb") as f:
        data = pickle.load(f)
        
    train_df, train_matrix, test_matrix, user_id_map, user_popularity, item_id_map, item_popularity, num_users, num_items = \
        data["train_df"], data['train_matrix'], data['test_matrix'], data['user_id_dict'], data['user_popularity'], data['item_id_dict'], data[
            'item_popularity'], data['num_users'], data['num_items']
    
    return train_df, train_matrix, test_matrix, user_id_map, user_popularity, item_id_map, item_popularity, num_users, num_items


def pre_preprocess_data(data_path: str, save_path: str, sep: str, columns: dict,
                        min_ratings_threshold=20, min_ratings_count_threshold=8) -> None:
    """
    Write to file a more standard version
    args:
        data_path: an input data path
        save_path: a preprocessed save data path
        sep: separate string of each csv line
        columns: a column dictionary to rename the final columns must be user, item, rating
        min_ratings_threshold: a mininum rating threshold per user, default 20 ratings
        min_ratings_count_threshold: a mininum rating count threshold per item, default 8
    
    Save a new csv file into the local file system to call preprocess function before being fed into a recommendation model
    """
    data = pd.read_csv(data_path, sep=sep, engine="python")
    data = data.rename(columns=columns)
    zero_rating_row_dix = data[data["rating"] == 0].index
    data = data.drop(zero_rating_row_dix)
    
    # Count book ratings per user
    # Select user that has number of rating at `min_ratings_threshold`
    num_ratings_per_user = data.groupby('user')['rating'].count()

    # Filter users with more than the minimum threshold
    knowledgeable_user_ids = num_ratings_per_user[num_ratings_per_user > min_ratings_threshold].index
    knowledgeable_user_ratings = data[data['user'].isin(knowledgeable_user_ids)]

    # Select item that has minimum rating at `min_ratings_count_threshold`
    rating_counts = knowledgeable_user_ratings.groupby('item').count()['rating']
    popular_books = rating_counts[rating_counts >= min_ratings_count_threshold].index
    final_ratings = knowledgeable_user_ratings[knowledgeable_user_ratings['item'].isin(popular_books)]
    
    data_group = final_ratings.groupby('user')
    for i, group in data_group:
        num_items_user = len(group)
        if num_items_user <= 4:
            final_ratings = final_ratings.drop(final_ratings[final_ratings["user"] == i].index)
    
    df = final_ratings.copy()
    
    df.to_csv(save_path, index=False)


def preprocess(data_path: str, save_path: str, sep=",", train_ratio=0.8,
               binarize_threshold=0.0,
               order_by_popularity=True):
    """
    Function to preprocess the raw data
    args:
        data_path: input data path (.csv format)       
        save_path: save output path (byte data json representation)
    """
    print("Preprocess start...")
    
    # TODO: Fine-tune this part for a specific dataset, in this case we use book rating
    data = pd.read_csv(data_path, sep=sep,
                       dtype={"user": int, "item": int, "rating": float}, engine="python")
    
    num_users = len(pd.unique(data.user))
    num_items = len(pd.unique(data.item))
    print('Initial users: {}, items: {}'.format(num_users, num_items))
    
    # Apply a binarize threshold
    # Binarize ratings into implicit feedback
    if binarize_threshold > 0.0:
        print("Binarize ratings greater than or equal to %.f" % binarize_threshold)
        data = data[data['ratings'] >= binarize_threshold]

    # Convert ratings into implicit feedback
    data['ratings'] = 1.0
    
    num_items_by_user = data.groupby('user', as_index=True).size()
    num_users_by_item = data.groupby('item', as_index=True).size()
    
    # Assign new user IDs
    print('Assign new user id from 0..n')
    user_frame = num_items_by_user.to_frame()
    user_frame.columns = ['item_cnt']
    
    if order_by_popularity:
        user_frame = user_frame.sort_values(by='item_cnt', ascending=False)
    user_frame['new_id'] = list(range(num_users))

    # Add old user IDs into new consecutive user IDs
    frame_dict = user_frame.to_dict()
    user_id_dict = frame_dict['new_id']
    user_frame = user_frame.set_index('new_id')
    user_to_num_items = user_frame.to_dict()['item_cnt']

    data.user = [user_id_dict[x] for x in data.user.tolist()]
    
    # Assign new item IDs
    print('Assign new item id from 0..n')
    item_frame = num_users_by_item.to_frame()
    item_frame.columns = ['user_cnt']

    if order_by_popularity:
        item_frame = item_frame.sort_values(by='user_cnt', ascending=False)
    item_frame['new_id'] = range(num_items)

    # Add old item IDs into new consecutive item IDs
    frame_dict = item_frame.to_dict()
    item_id_dict = frame_dict['new_id']
    item_frame = item_frame.set_index('new_id')
    item_to_num_users = item_frame.to_dict()['user_cnt']

    data.item = [item_id_dict[x] for x in data.item.tolist()]

    num_users, num_items = len(user_id_dict), len(item_id_dict)
    
    print("Split data into training set and test set")
    data_group = data.groupby('user')
    train_list, test_list = [], []

    num_zero_train, num_zero_test = 0, 0
    """
    This loop is to ensure that the data will contain both user rating in training set
    and test set, if the user has the total number of rating equal to 1
    It will not run
    """
    for _, group in data_group:
        num_items_user = len(group)
        if num_items_user >= 2:
            num_train = max(1, int(train_ratio * num_items_user))
            num_test = num_items_user - num_train
        
        # TODO: Sort value of a group based on timestamp (if needed)
        # group = group.sort_values(by = "timestamps")
        idx = np.ones(num_items_user, dtype='bool')

        # Holdout feedback for test per user
        test_idx = np.random.choice(num_items_user, num_test, replace=False)
        idx[test_idx] = False
        
        if len(group[idx]) == 0:
            num_zero_train += 1
        else:
            train_list.append(group[idx])

        if len(group[np.logical_not(idx)]) == 0:
            num_zero_test += 1
        else:
            test_list.append(group[np.logical_not(idx)])
            
    train_df = pd.concat(train_list)
    test_df = pd.concat(test_list)
    print('# zero train, test: %d, %d' % (num_zero_train, num_zero_test))
    # Transform train and test data frames into sparse matrices
    train_sparse = dataframe_to_sparse_matrix(train_df, shape=(num_users, num_items))
    test_sparse = dataframe_to_sparse_matrix(test_df, shape=(num_users, num_items))
    
    # Save data and statistics
    data_to_save = {
        'train_df': train_df,
        'train_matrix': train_sparse,
        'test_matrix': test_sparse,
        'user_id_dict': user_id_dict,
        'user_popularity': user_to_num_items,
        'item_id_dict': item_id_dict,
        'item_popularity': item_to_num_users,
        'num_users': num_users,
        'num_items': num_items
    }
    
    with open(save_path, 'wb') as f:
        pickle.dump(data_to_save, f)

    print('Preprocess finished.')
    
    
def dataframe_to_sparse_matrix(df: pd.DataFrame, shape) -> sp.csr_matrix:
    """
    Utility function to transform raw data into sparse matrix
    Returns a sparse matrix
    Parameter df: dataframe
    Parameter shape: shape of a sparse matrix
    """
    
    rows, cols = df.user, df.item
    values = df.ratings
    
    sp_data = sp.csr_matrix((values, (rows, cols)), dtype='float64', shape=shape)
    
    num_nonzeros = np.diff(sp_data.indptr)
    rows_to_drop = num_nonzeros == 0
    if sum(rows_to_drop) > 0:
        print('%d empty users are dropped from matrix.' % sum(rows_to_drop))
        sp_data = sp_data[num_nonzeros != 0]

    return sp_data