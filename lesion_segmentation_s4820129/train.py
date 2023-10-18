from modules import ImprovedUNET
from dataset import ISICdataset
from utilities import get_data_from_url, train, DSC, accuracy
import albumentations as A
from albumentations.pytorch import ToTensorV2
from torch.utils.data import Dataset, DataLoader
import torch
from torch import nn

print('got here')
get_data_from_url('ISIC_data', '1vxd1KBIYa3zCAVONkacdclsWUAxhWLho')
TRAIN_DIR = 'ISIC_data/train'
TRUTH_DIR = 'ISIC_data/ground_truth'


train_transform = A.Compose(
        [
            A.Resize(height=256, width=256),
            A.Rotate(limit=35, p=1.0),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.1),
            A.Normalize(
                mean=[0.0, 0.0, 0.0],
                std=[1.0, 1.0, 1.0],
                max_pixel_value=255.0,
            ),
            ToTensorV2(),
        ],
    )


full_dataset = ISICdataset(
        image_dir=TRAIN_DIR,
        truth_dir=TRUTH_DIR,
        transform=train_transform,
    )

#hyperparameters
N_CHANNELS = 3
N_CLASSES = 1
BATCH_SIZE = 16
LEARNING_RATE = 0.01
EPOCHS = 3
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

train_loader = DataLoader(
    full_dataset,
    batch_size=BATCH_SIZE,
    num_workers=1,
    pin_memory=True,
    shuffle=True,
)

model = ImprovedUNET(N_CHANNELS, N_CLASSES)
optimizer = torch.optim.SGD(model.parameters(),lr=LEARNING_RATE,momentum=0.1,weight_decay=5e-4)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=200)
loss_fn = nn.BCEWithLogitsLoss()

model = model.to(DEVICE)
print(model)
print(DEVICE)

for epoch in range(EPOCHS):
    train(model, train_loader, optimizer, loss_fn, DEVICE)
    accuracy(model, train_loader, DEVICE)
    break

