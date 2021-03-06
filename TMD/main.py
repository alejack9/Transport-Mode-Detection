import numpy as np
import torch
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from os import makedirs, path

import evaluation
import data_layer
import model_runner
import preprocessing

from pytorch import nn_main


# for reproducibility
def set_deterministic_behavior():
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    np.random.seed(0)


if __name__ == '__main__':
    set_deterministic_behavior()

    models_dir = 'saved_models'
    use_saved_if_available, save_models = True, True

    if not path.exists(models_dir):
        print("WARNING: Making not existing folder: {}".format(models_dir))
        makedirs(models_dir)
        makedirs(path.join(models_dir, "csvs"))

    X, y, num_classes = data_layer.load_data()

    # encoding of target values for the neural network
    lenc = LabelEncoder()
    y_encoded = lenc.fit_transform(y)

    # show the dataset main characteristics
    # preprocessing.priori_analysis(X, y)
    # create 4 different sub-datasets
    X_subsets, subsets_sizes = preprocessing.create_datasets(X)

    best_models = {}
    losses = {}
    # for each sub-dataset
    for fs, X_current in zip(subsets_sizes, X_subsets):
        # 20% for testing
        X_train, X_test, y_train, y_test = train_test_split(X_current, y, test_size=0.20, random_state=42, stratify=y)
        # replace missing values
        X_train, X_test = preprocessing.remove_nan(X_train, X_test)

        # cross-validation to find the best models
        current_bests = model_runner.retrieve_best_models(X_train, y_train, fs, use_saved_if_available, save_models,
                                                          models_dir)
        current_bests = evaluation.add_test_scores(current_bests, X_test, y_test)
        best_models.update(current_bests)

        # retrieve the best neural network
        best_mlp, loss = nn_main.run(X_current.to_numpy(), y_encoded, models_dir, use_saved_if_available, save_models)
        if loss is not None:
            losses[fs] = loss
        best_models.update(best_mlp)

        # plot roc curve and confusion matrix of each best model
        evaluation.partial_results_analysis(current_bests, X_test, y_test, X_current.columns)

    # display validation and testing complete results
    evaluation.results_analysis(best_models, subsets_sizes, losses)
