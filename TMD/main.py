from os import makedirs, path
from functools import reduce
import numpy as np
import pandas as pd
import visualization
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from joblib import dump, load
import data_layer
import model_runner
from data_layer import load_data
from sklearn.decomposition import PCA
import torch
from models_params import models
from sklearn.model_selection import train_test_split


def get_columns_names(sensors):
    to_ret = []
    for sensor in sensors:
        for measure in ['#min', '#max', '#mean', '#std']:
            to_ret.append('android.sensor.' + sensor + measure)
    return to_ret


def pca_analysis():
    std_scaler = StandardScaler()
    smp_imputer = SimpleImputer(strategy="median")
    pca = PCA()
    pca.fit(smp_imputer.fit_transform(std_scaler.fit_transform(X)))
    most_important = [np.abs(pca.components_[i]).argmax() for i in range(X.shape[1])]
    most_important_names = [X.columns[most_important[i]] for i in range(X.shape[1])]
    visualization.plot_explained_variance(most_important_names, pca.explained_variance_)


def results_analysis(accuracies_train, accuracies_test, best_estimators):
    visualization.plot_confusions(best_estimators, X_trainval, y_trainval)
    accuracies_train, accuracies_test, models_names = (list(t) for t in zip(*sorted(
        zip(accuracies_train, accuracies_test, best_estimators.keys()), reverse=True)))
    [print(name, '{:.2f}'.format(train_score), '{:.2f}'.format(test_score)) for train_score, test_score, name in
     zip(accuracies_train, accuracies_test, models_names)]
    visualization.plot_accuracies(models_names, accuracies_train, accuracies_test, False)


if __name__ == '__main__':
    torch.manual_seed(0)
    # torch.use_deterministic_algorithms(True)
    np.random.seed(0)
    # true aumenta le performance ma lo rende non-deterministico
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    models_dir = 'saved_models1'
    use_saved_if_available = True
    save_models = False

    if not path.exists(models_dir):
        print("WARNING: Making not existing folder: {}".format(models_dir))
        makedirs(models_dir)

    unused_features = get_columns_names([
        'light', 'gravity', 'magnetic_field', 'magnetic_field_uncalibrated', 'pressure', 'proximity']
    )
    print('Unused features list:')
    print(reduce(lambda a, b: a + '\n' + b, unused_features))
    print('----------------------------------------')

    X, y, num_classes = load_data()
    # X = X.drop(unused_features, axis=1)

    pca_analysis()

    visualization.plot_class_distribution(y)
    visualization.plot_missingvalues_var(X)

    # visualization.boxplot(X)

    visualization.plot_density_all(X)
    # for col in X.columns:
    #     visualization.density(X[col])

    X_trainval, X_test, y_trainval, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

    X_trainval, imputer = data_layer.preprocess(X_trainval)

    X_test = imputer.transform(X_test)

    best_estimators = {}
    predicts = []
    accuracies_train = []
    accuracies_test = []
    results = []

    for est_name, est, params in models:
        if use_saved_if_available and path.exists(path.join(models_dir, est_name + ".joblib")):
            print("Saved model found: {}".format(est_name))
            best_estimators[est_name] = load(path.join(models_dir, est_name + ".joblib"))
        else:
            res, best_estimators[est_name] = model_runner.run_trainval(X_trainval, y_trainval, est, params, cv=10)
            if save_models:
                dump(best_estimators[est_name], path.join(models_dir, est_name + ".joblib"))
            results.append(pd.DataFrame(res))
        accuracies_train.append(best_estimators[est_name].score(X_trainval, y_trainval))
        predicts.append(best_estimators[est_name].predict(X_test))
        accuracies_test.append(best_estimators[est_name].score(X_test, y_test))

    # print('------------------------------------')
    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.max_rows', None)
    # pd.set_option('display.max_colwidth', None)
    # print([result.columns for result in results])
    # names = list(best_estimators.keys())
    # [(print(names[i]), print(
    #     result.loc[:, result.columns.str.startswith("param_")].assign(mean_test_score=result['mean_test_score'],
    #                                                                   rank_test_score=result['rank_test_score'])),
    #   print('---')) for i, result in
    #  enumerate(results)]

    visualization.plot_roc_for_all(best_estimators, X_test, y_test, np.unique(y_test))

    results_analysis(accuracies_train, accuracies_test, best_estimators)

    # kf = KFold(n_splits=10)
    # for train_index, val_index in kf.split(X_trainval):
    #     X_train, X_val, y_train, y_val = X_trainval.iloc[train_index], X_trainval.iloc[val_index],\
    #                                      y_trainval.iloc[train_index], y_trainval.iloc[val_index]
    #
    #     models = [SVM,...]
    #     methods = ["std", "scaling"]
    #     scores = np.array((2,5))
    #
    #     for i in range(len(methods)):
    #         X_train, X_val = data_layer.preprocess(X_train, X_val, method=methods[i])
    #         for j in range(len(models)):
    #             #scores[i,j] = models[j].train_model(X_train, X_val)
    #             from sklearn.svm import SVC
    #
    #             param_grid = {'C': [0.001, 0.01, 0.1, 1, 10, 100],
    #                           'gamma': [0.001, 0.01, 0.1, 1, 10, 100]}
    #
    #
    #
    #
    #
    #     break

    # preprocess test set with X_trainval means for missing values
