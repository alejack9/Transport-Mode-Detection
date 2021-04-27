import math

import pandas as pd
import torch
from matplotlib import pyplot as plt
from sklearn.metrics import classification_report


def train_loop(dataloader, model, loss_fn, optimizer, scheduler, num_epochs, device):
    print('----------------------------------')
    model.train()
    # size = len(dataloader.dataset)
    prev_loss = -1
    for epoch in range(num_epochs):
        print("Epoch: {}/{}".format(epoch, num_epochs))
        for batch, (X, y) in enumerate(dataloader):
            # iteration = batch * len(X)
            X, y = X.to(device), y.to(device)
            optimizer.zero_grad()

            # Compute prediction and loss
            pred = model(X)
            loss = loss_fn(pred, y)
            if math.isnan(loss.item()):
                print('Nan detected')
                print(pred, y)
                exit()

            loss.backward()
            optimizer.step()

        scheduler.step()
            # if iteration % 100 == 0:
            #     loss, current = loss.item(), iteration
        print("loss: {}".format(loss))
        if loss == prev_loss:
            break
        else:
            prev_loss = loss
    print('Done')
    print('----------------------------------')


def test_loop(dataloader, model, device, name=None):
    model.eval()
    predictions = []
    actual_labels = []

    # avoid memory consumption to calculate gradient: we are not training the network
    with torch.no_grad():
        for X, y in dataloader:
            X, y = X.to(device), y.to(device)
            a = model(X)
            predictions.append(a)
            actual_labels.append(y)
    # matrix of size (size(dataloader.X),k): the higher is the value, the higher is the probability of that class
    predictions = torch.stack(predictions).squeeze()
    actual_labels = torch.stack(actual_labels).squeeze().cpu()
    # keep the class with the maximum value
    predictions = predictions.argmax(dim=1, keepdim=True).cpu()
    actual_labels.cpu()
    df = pd.DataFrame(classification_report(actual_labels, predictions, output_dict=True)).transpose()
    if name is not None:
        df.to_csv(name)
    print(df)
