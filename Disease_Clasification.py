import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

dataset=pd.read_csv(r"C:/Users/praha/OneDrive/Desktop/Project_Helath_Care/Training.csv")

dataset.head()

dataset=dataset.drop(columns="Unnamed: 133")

dataset["prognosis"]=dataset["prognosis"].rename("Disease_Clssify")

dataset.rename(columns={"prognosis": "Disease_Clssify"}, inplace=True)

dataset.isnull().sum()

x=dataset.iloc[:,:-1]
y=dataset["Disease_Clssify"]

from sklearn.model_selection import train_test_split
x_train,x_test,y_train,y_test=train_test_split(x,y,test_size=0.20,random_state=42)

from sklearn.linear_model import LogisticRegression
lr=LogisticRegression()
lr.fit(x_train,y_train)


bias=lr.score(x_test,y_test)*100
bias

variance=lr.score(x_train,y_train)*100
variance

y_pread=lr.predict(x_test)

dataset_com=pd.DataFrame({"Actual":y_test,"Predict":y_pread})
dataset_com

import pickle

# Save the model
with open("health_model.pkl", "wb") as file:
    pickle.dump(lr, file)
