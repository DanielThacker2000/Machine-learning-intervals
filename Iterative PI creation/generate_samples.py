# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 08:41:20 2024

@author: dan
"""

import numpy as np
from scipy import stats
from scipy.stats import norm, halfnorm, t
from scipy.interpolate import UnivariateSpline

import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnnotationBbox, TextArea
import random
rng = np.random.RandomState(42) #Set seed
alpha = 0.1

# =============================================================================
# Define the mixture model
# =============================================================================
class MixtureModel(stats.rv_continuous):
    def __init__(self, submodels, *args, weights = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.submodels = submodels
        if weights is None:
            weights = [1 for _ in submodels]
        if len(weights) != len(submodels):
            raise(ValueError(f'There are {len(submodels)} submodels and {len(weights)} weights, but they must be equal.'))
        self.weights = [w / sum(weights) for w in weights]
        
    def _pdf(self, x):
        pdf = self.submodels[0].pdf(x) * self.weights[0]
        for submodel, weight in zip(self.submodels[1:], self.weights[1:]):
            pdf += submodel.pdf(x)  * weight
        return pdf
            
    def _sf(self, x):
        sf = self.submodels[0].sf(x) * self.weights[0]
        for submodel, weight in zip(self.submodels[1:], self.weights[1:]):
            sf += submodel.sf(x)  * weight
        return sf

    def _cdf(self, x):
        cdf = self.submodels[0].cdf(x) * self.weights[0]
        for submodel, weight in zip(self.submodels[1:], self.weights[1:]):
            cdf += submodel.cdf(x)  * weight
        return cdf

    def rvs(self, size):
        submodel_choices = np.random.choice(len(self.submodels), size=size, p = self.weights)
        submodel_samples = [submodel.rvs(size=size) for submodel in self.submodels]
        rvs = np.choose(submodel_choices, submodel_samples)
        return rvs

# =============================================================================
# Simulate data functions
# =============================================================================
#Cubic
# def generate_data_mixture(num_samples, mixture_model):
    

def randomly_generate_cube(x_train_dict, y_train_dict, noise_type, std, num_samples, range_start=-1,range_stop=1,half_norm_loc = 1,  std_dev=0.4):
    """
    y = x**3 + normal noise
    9 in 10 chance for x to be x= uniform(-1,1), if not, normally distributed with mean 1 and std 0.55, means some values are very sparse and far away
    from https://proceedings.neurips.cc/paper/2021/file/46c7cb50b373877fb2f8d5c4517bb969-Paper.pdf
    """
    y_train = []
    x_train = []
    mean = 1
    std_dev=0.4 #std for normal function


    for i in range(num_samples):
       
        decider = random.randrange(1,10) #Produces a integer between the range
       
        if decider <=8:
            x = random.uniform(range_start, range_stop) #Produces a random float value
        else:
            x = halfnorm.rvs(loc = half_norm_loc, scale = std_dev, size=1)
            x=x[0]
            #x = np.random.normal(loc=1, scale=standard_deviation)
        noise = np.random.normal(loc=0, scale=std)
        y = x**3 + noise 
        y_train.append(y)  # Append standard_deviation as a new row
        x_train.append(x)  # Append gaussian vector as a new row
    x_train = np.array(x_train)
    y_train = np.array(y_train)
    #plt.figure()
    #plt.scatter(x_train,y_train)
    # Sort x_train and ensure y_train matches the sorted x_train
    sorted_indices = np.argsort(x_train)
    x_train_sorted = x_train[sorted_indices]
    y_train_sorted = y_train[sorted_indices]
    x_train_sorted = np.transpose(x_train_sorted)
    y_train_sorted = np.transpose(y_train_sorted)
    x_train_dict[std] = x_train_sorted.reshape(-1,1)
    y_train_dict[std] = y_train_sorted.reshape(-1,1)
    return x_train_dict, y_train_dict

def cube_function(x):
    return x**3
def linear_function(x):
    return x
def normal_mixture_function(x):
    scaler = 40
    mixture_model = MixtureModel([stats.norm(3, 1), 
                                  stats.norm(9, 0.1), 
                                  stats.norm(11,3)],
                                 weights = [0.2, 0.01, 0.05])
    return scaler*mixture_model.pdf(x)

def iterate_over_std(x_train_dict, y_train_dict, noise_type, std, x_vals, function): # add function choice here

    if noise_type == "norm":
        noise_maker  = stats.norm(0,std)
    if noise_type =="student-t":
        noise_maker  = stats.t(0,std)
    else:
        noise_maker  = stats.norm(0,std)
    y_train = []
    x_train = []
    for x in x_vals:
        #x = np.random.normal(loc=1, scale=standard_deviation)
        noise = noise_maker.rvs(size=1)
        y = function(x) + noise 
        y_train.append(y)  
        x_train.append(x)  
    x_train = np.array(x_train)
    y_train = np.array(y_train)

    x_train_sorted = np.transpose(x_train)
    y_train_sorted = np.transpose(y_train)
    x_train_dict[std] = x_train_sorted.reshape(-1,1)
    y_train_dict[std] = y_train_sorted.reshape(-1,1)
    return x_train_dict, y_train_dict


    
#Normally distributed but hetorscedastic - very tricky for mlp to solve -  easy for CQR
def generate_data_norm(num_samples, std_dev=0.5):
    x_train = np.linspace(start=0, stop=10, num=num_samples)
    y_true_mean = 10 + 0.5 * x_train**3
    y_train = y_true_mean + rng.normal(loc=0, scale=std_dev + 0.5 * x_train**3, size=x_train.shape[0])
    #plt.scatter(x_train,y_train)
    return np.transpose(np.array([x_train])), np.transpose(np.array([y_train])) #y_true_mean

#Sine function + linear
def generate_data_sin_unif(num_samples, std_dev=0.7):
    """
    y = 2*sin(pi*x ) + pi*x + noise
    Noise is normal
    From Adaptive, distribution-free prediction intervals for deep networks
    """
    def f(Z):
        return(2.0*np.sin(np.pi*Z) + np.pi*Z)
    p = 1
    X = np.random.uniform(size=(num_samples,p))
    beta = np.zeros((p,))
    beta[0:5] = 1.0
    Z = np.dot(X,beta)
    E = np.random.normal(size=(num_samples,),scale=std_dev)
    #Y = f(Z) + np.sqrt(1.0+Z**2) * E
    Y = f(Z) + E
    return X.astype(np.float32), np.transpose(np.array([Y.astype(np.float32)]))

def generate_data_exp(num_samples, std_dev=2):
    "Uniformly distribute x points between -1 and 3. f(x) is a y = e^x + noise. Noise is normal with SD 2"
    y_train = []
    x_train = []
    mean = 1
    standard_deviation=1
   
       
    rv = norm(loc = mean, scale = standard_deviation)
    x = np.linspace(start=-1, stop=3, num=num_samples)
    #x = np.random.normal(loc=mean, scale=standard_deviation)
    noise = np.random.normal(loc=1, scale=std_dev,size=(num_samples,))
    y = np.exp(x) + noise
    y_train.append(y)  # Append standard_deviation as a new row
    x_train.append(x)  # Append gaussian vector as a new row
       
    return np.transpose(np.array(x_train)), np.transpose(np.array(y_train))

def x_sinx(x):
    """One-dimensional x*sin(x) function."""
    return x*np.sin(x)

def generate_data_with_heteroscedastic_noise(x_train_dict, y_train_dict, min_x, max_x, std, n_samples):
    """
    Generate 1D noisy data uniformely from the given function
    and standard deviation for the noise.
    """
    X_train = np.linspace(min_x, max_x, n_samples)
    np.random.shuffle(X_train)
    X_test = np.linspace(min_x, max_x, n_samples*5)
    y_train = (
        x_sinx(X_train) +
        (np.random.normal(0, std, len(X_train)) * X_train)
    )

    x_train_dict[std] = X_train.reshape(-1, 1)
    y_train_dict[std] = y_train.reshape(-1, 1)
    return x_train_dict, y_train_dict


def generate_data_with_constant_noise(x_train_dict, y_train_dict, min_x, max_x, std, n_samples):
    """
    Generate 1D noisy data uniformely from the given function
    and standard deviation for the noise.
    """
    X_train = np.linspace(min_x, max_x, n_samples)
    np.random.shuffle(X_train)
    X_test = np.linspace(min_x, max_x, n_samples)
    y_train = x_sinx(X_train)
    y_train += np.random.normal(0, std, y_train.shape[0])

    x_train_dict[std] = X_train.reshape(-1, 1)
    y_train_dict[std] = y_train.reshape(-1, 1)
    return x_train_dict, y_train_dict

def generate_data(num_samples=300,stds=[0.3,0.5,0.7,1],noise_types=["norm","student-t","mixture"], function=linear_function):
    y_train_dict = {}
    x_train_dict = {}

    x_vals = np.linspace(start=0, stop=10, num=num_samples)

    for noise_type in noise_types:
        if function =="cube":
            for std in stds:
                x_train_dict, y_train_dict = randomly_generate_cube(x_train_dict, y_train_dict, noise_type, std, num_samples)
        elif function =="sinex_con":
            for std in stds:
                x_train_dict, y_train_dict = generate_data_with_constant_noise(x_train_dict, y_train_dict, -5, 5, std, num_samples)
        elif function =="sinex_het":
            for std in stds:
                x_train_dict, y_train_dict = generate_data_with_heteroscedastic_noise(x_train_dict, y_train_dict, -5, 5, std, num_samples)
        else:
            for std in stds:
                x_train_dict, y_train_dict = iterate_over_std(x_train_dict, y_train_dict, noise_type, std, x_vals, function)
        
    return x_train_dict, y_train_dict