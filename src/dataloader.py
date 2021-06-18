import torch
from torch.utils.data.sampler import WeightedRandomSampler
from torch.utils.data import Dataset, DataLoader

from config import args
from dataset import DatasetTabular, generate_dataset


def generate_dataloader(num_supervised_train_data, experiment, seed):
    # TODO: Get dataframes into generator
    train_dataset, val_dataset, test_dataset = generate_dataset()
    
    # create sampler
    train_weight = train_sup_dataset.make_weights_for_balanced_classes()
    train_weight = torch.from_numpy(train_sup_weight)
    train_sampler = WeightedRandomSampler(train_weight.type('torch.DoubleTensor'), 
                                        len(train_weight),
                                        replacement=False,)
    
    pin_memory = True if torch.cuda.is_available() else False
    
    # Generate dataloaders
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, 
                            sampler=train_sampler, num_workers=args.num_workers, 
                            pin_memory=pin_memory)
        
    validation_loader = DataLoader(val_dataset, batch_size=args.batch_size, 
                                num_workers=args.num_workers,  
                                shuffle=False,)
    
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, 
                            num_workers=args.num_workers, 
                            pin_memory=pin_memory, shuffle=False,)
    
    return train_loader, validation_loader, test_loader