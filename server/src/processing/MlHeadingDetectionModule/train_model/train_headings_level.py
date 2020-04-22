import argparse
import os

import pandas as pd
import numpy as np
from sklearn import metrics
from sklearn.feature_selection import RFECV
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn_porter import Porter
from sklearn import preprocessing

parser = argparse.ArgumentParser(description='Train a decision tree to recognize headings.')
parser.add_argument('dataset_dir', help='folder containing the .csv files generated by build_dataset.py')
parser.add_argument('out_dir', help='folder in which to save the trained model')
args = parser.parse_args()

dataset_dir = args.dataset_dir
paths = os.listdir(dataset_dir)
X = []
y = []

for path in paths:
    df = pd.read_csv(os.path.join(dataset_dir, path), header=0)
    df_headings = df.loc[df['label']=='heading'].reset_index().copy()
    df_headings['font_size'] = df_headings['font_size'].apply(lambda x: round(x, 2))
    
    if len(df_headings) < 3:
        continue
        
    for i in range(len(df_headings)):
        X.append([df_headings['font_size'][i], df_headings['is_bold'][i], df_headings['text_case'][i]])
        # X.append([df_headings['font_size'][i], df_headings['is_bold'][i]])
            
    y = y + list(df_headings['level'])
    

#X = preprocessing.scale(X)

X_res, y_res = X, y
X_train, X_test, y_train, y_test = train_test_split(X_res, y_res, test_size=0.2)

parameters = {'min_samples_leaf':[1,2,3], 'min_samples_split':[2,3], 'criterion':['entropy','gini']}
clf_cv = GridSearchCV(DecisionTreeClassifier(), parameters).fit(X_res, y_res)
clf = DecisionTreeClassifier(min_samples_leaf=clf_cv.best_params_['min_samples_leaf'],
                             min_samples_split=clf_cv.best_params_['min_samples_split'],
                             criterion=clf_cv.best_params_['criterion'],
                             splitter='best')
selector = RFECV(clf, step=1, cv=10, scoring=metrics.make_scorer(metrics.accuracy_score))
selector = selector.fit(X_res, y_res)

y_pred = selector.predict(X_test)
print('accuracy:', metrics.accuracy_score(y_test, y_pred))

porter = Porter(selector.estimator_, language='js')
output = porter.export(embed_data=True)

with open(os.path.join(args.out_dir, 'model_level.js'), mode='w+', encoding='utf8') as f:
    f.write('export ' + output)
