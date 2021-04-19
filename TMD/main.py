import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
import time

import data_layer
from data_layer import loadData
import visualization
from sklearn.model_selection import train_test_split, KFold
from sklearn.decomposition import PCA
from sklearn.model_selection import GridSearchCV
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
# import seaborn as sb
# import matplotlib.pyplot as plt
import torch
# from sklearn.metrics import confusion_matrix
# from sklearn.naive_bayes import GaussianNB
# from sklearn.ensemble import RandomForestClassifier
# from sklearn import metrics
# from sklearn.impute import SimpleImputer
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV, train_test_split

if __name__ == '__main__':
    torch.manual_seed(0)
    #torch.use_deterministic_algorithms(True)
    np.random.seed(0)
    # true aumenta le performance ma lo rende non-deterministico
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    X, y, num_classes = loadData()

    #X, _ = data_layer.preprocess(X, X)

    unused_features = ["android.sensor.light#mean","android.sensor.light#min","android.sensor.light#max","android.sensor.light#std",
                        "android.sensor.gravity#mean","android.sensor.gravity#min","android.sensor.gravity#max","android.sensor.gravity#std",
                        "android.sensor.magnetic_field#mean","android.sensor.magnetic_field#min","android.sensor.magnetic_field#max","android.sensor.magnetic_field#std",
                        "android.sensor.magnetic_field_uncalibrated#mean","android.sensor.magnetic_field_uncalibrated#min","android.sensor.magnetic_field_uncalibrated#max","android.sensor.magnetic_field_uncalibrated#std",
                        "android.sensor.pressure#mean","android.sensor.pressure#min","android.sensor.pressure#max","android.sensor.pressure#std",
                        "android.sensor.proximity#mean","android.sensor.proximity#min","android.sensor.proximity#max","android.sensor.proximity#std"]
    X.drop(unused_features, axis = 1)

    stdScaler = StandardScaler()
    smpImputer = SimpleImputer(strategy="median")
    pca = PCA()
    pca.fit(smpImputer.fit_transform(stdScaler.fit_transform(X)))
    most_important = [np.abs(pca.components_[i]).argmax() for i in range(X.shape[1])]
    most_important_names = [X.columns[most_important[i]] for i in range(X.shape[1])]
    # visualization.plot_explained_variance(most_important_names, pca.explained_variance_)


    #visualization_priori.plot_class_distribution(y)
    #visualization.plot_missingvalues_var(X)
    #visualization.boxplot(X)
    # for col in X.columns:
    #     visualization.density(X[col])

    X_trainval, X_test, y_trainval, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)


    # param_grid = {'C': [0.001, 0.01, 0.1, 1, 10, 100],
    #               'gamma': [0.001, 0.01, 0.1, 1, 10, 100]}
    param_grid = [
        {
            'clf': (SVC(),),
            'clf__kernel': ('linear', 'poly', 'rbf'),
            'clf__C': (0.001, 0.01, 0.1, 1, 10),
            'clf__gamma': (0.001, 0.01, 0.1, 1, 10),
        },
        {
            'clf': (GaussianNB(),)
        },
        {
            'clf': (RandomForestClassifier(random_state=42, n_jobs=-1),),
            'clf__n_estimators': (10, 20, 50, 100, 200)
        },
        {
            'scaler' : (StandardScaler(), MinMaxScaler())
        }
    ]

    pipeline = Pipeline([('fillnan', SimpleImputer(strategy="median")),
                         ('scaler', StandardScaler()),
                         ('clf', RandomForestClassifier(random_state=42))])
    grid_search = GridSearchCV(pipeline, param_grid, cv=10, verbose=10)
    time0 = time.time()
    grid_search.fit(X_trainval, y_trainval)


    results = pd.DataFrame(grid_search.cv_results_)
    results['param_clf'] = results["param_clf"].apply(lambda x: str(type(x)))
    pd.set_option("display.max_colwidth", None)
    print(results.iloc[results.groupby('param_clf')['mean_test_score'].idxmax()]["params"])
    # print(results[results[''], :])

    print(time.time() - time0)

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

    #preprocess test set with X_trainval means for missing values



