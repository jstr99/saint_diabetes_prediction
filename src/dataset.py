import numpy as np
import pandas as pd

from sklearn import preprocessing
from torch.utils.data import Dataset, DataLoader


def generate_splits(dataset_size, num_supervised_train_data, 
                      validation_split, test_split, 
                      random_seed, shuffle_dataset=True,):
    """Generate data samplers for supervised and semi-supervised training """

    # Creating data indices for training and validation splits:
    indices = list(range(dataset_size))

    split_val = int(validation_split * dataset_size)
    split_test = int(test_split * dataset_size)
    
    if shuffle_dataset:
        np.random.seed(random_seed)
        np.random.shuffle(indices)

    # should not change for all operations
    test_indices = indices[:split_test] 
    val_indices = indices[split_test : split_test+split_val]
    
    if num_supervised_train_data == 'all':
        sup_train_indices = indices[split_test+split_val: ]
        ssl_train_indices = []
    else:
        num_supervised_train_data = int(num_supervised_train_data)
        sup_train_indices = indices[split_test+split_val: split_test+split_val+num_supervised_train_data]   
        ssl_train_indices = indices[split_test+split_val+num_supervised_train_data: ]

    return sup_train_indices, val_indices, test_indices, ssl_train_indices

# custom preprocessing function for each dataset
def preprocess_bank(data, target, cls_token_idx):
    """
    preprocess: function
        this is a function that process the features
        and return the:
        - the processed data in the order of [numerical_features, categorical features]
        - number of numerical features
        - number of categorical features
        - list of cat_len length describes the 
        number of catogeries in each catogrical column 
    """
    # copying the data
    data = data.copy()

    # adding the cls token to beginning of data
    data.insert(loc=cls_token_idx, column='cls', value='cls')

    categ_cols = data.select_dtypes(include=['object', 'category']).columns
    num_cols = [col for col in data.columns if col not in categ_cols]

    # z-transform and add missing value token
    num_data = data[num_cols]
    num_data = (num_data-num_data.mean())/num_data.std()
    # num_data = (num_data-num_data.min())/(num_data.max() - num_data.min()) min-max scaling

    num_data = num_data.fillna(-99999)
    new_data = pd.concat([data[categ_cols], num_data], axis=1)

    # label encoding 
    labelencode = preprocessing.LabelEncoder()
    cat_data = new_data[categ_cols]
    cat_data = cat_data.apply(labelencode.fit_transform)


    # cat columns come first
    new_data = pd.concat([cat_data.astype(np.int32), new_data[num_cols].astype(np.float32)], axis=1)

    labels = labelencode.fit_transform(target)
    labels = pd.DataFrame(labels ,columns = target.columns)
    
    cats = []

    for cat in cat_data.columns:
        cats.append(len(pd.unique(new_data[cat])))

    return new_data, labels, len(num_data.columns), len(cat_data.columns), cats

class DatasetTabular(Dataset):
    '''
    Creates tabular data set 

    Attributes
    ------------------------
    features: bs x n , 
    labels: bs x q, 
    num_len :lenght of numerical columns  
    cat_len:lenght of catogrical columns  
    cats:list of cat_len length describes the  number of catogeries in each catogrical column 
    '''
    def __init__(self, data, y):
        '''
        Parameters
        ------------------------
        data: DataFrame
            contains the features. It's assumed that the features
            are on the order of [numerical_features, categorical features]
        y: DataFrame
            represents the target variable
        '''
        self.data = data.values  # bs x n
        self.y = y.values        # bs x 1

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        sample = self.data[idx]
        label = self.y[idx]

        return sample, label

    def make_weights_for_balanced_classes(self):
        """adopted from https://discuss.pytorch.org/t/balanced-sampling-between-classes-with-torchvision-dataloader/2703/3"""

        nclasses = len(np.unique(self.y))
        count = np.zeros(nclasses)
        for idx in range(len(self.y)):
            target = self.y[idx]
            count[target] += 1

        N = float(sum(count))
        weight_per_class = N / count
        weight = np.zeros(len(self))
        for idx in range(len(self.y)):
            target = self.y[idx]
            weight[idx] = weight_per_class[target]
        return weight
    
def generate_dataset(train_df, train_y, 
                     val_df, val_y, 
                     test_df, test_y,):
    train_dataset = DatasetTabular(train_df, train_y)
    val_dataset = DatasetTabular(val_df, val_y)
    test_dataset = DatasetTabular(test_df, test_y)

    return train_dataset, val_dataset, test_dataset