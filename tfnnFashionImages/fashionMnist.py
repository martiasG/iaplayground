import math
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
import numpy as np
import pandas as pd
import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.python.framework import ops
import argparse
import sys
import datetime
import time

def random_mini_batches_tf(X, Y, mini_batch_size=32, thread_count=1, queue_capacity=100, seed=0):
    np.random.seed(seed)

    print('THREADS COUNT:', thread_count)
    print('QUEUE CAPACITY:', queue_capacity)
    print('BATCH SIZE:', mini_batch_size)
    print('SEED:', seed)

    m = X.shape[1]
    permutation = list(np.random.permutation(m))
    shuffled_X = X[:, permutation]
    shuffled_Y = Y[:, permutation].reshape((Y.shape[0],m))

    data_input_x = tf.constant(shuffled_X.T)
    data_input_y = tf.constant(shuffled_Y.T)
    batch_size = mini_batch_size

    batch_x_y = tf.train.shuffle_batch((data_input_x, data_input_y),
                     enqueue_many=True,
                     batch_size=batch_size,
                     num_threads=thread_count,
                     capacity=queue_capacity,
                     min_after_dequeue = math.floor(queue_capacity/4),
                     allow_smaller_final_batch=True)

    return batch_x_y

def random_mini_batches_exp(X, Y, mini_batch_size=32, seed=0):
    m = X.shape[1]                  # number of training examples
    mini_batches = []
    np.random.seed(seed)

    # Step 1: Shuffle (X, Y)
    permutation = list(np.random.permutation(m))
    shuffled_X = X[:, permutation]
    shuffled_Y = Y[:, permutation].reshape((Y.shape[0],m))

    for index in range(0, shuffled_X.shape[1], mini_batch_size):
        mini_batch_X=shuffled_X[:,index:min(index+mini_batch_size,shuffled_X.shape[1])]
        mini_batch_Y=shuffled_Y[:,index:min(index+mini_batch_size,shuffled_Y.shape[1])]
        mini_batch = (mini_batch_X, mini_batch_Y)
        mini_batches.append(mini_batch)

    return mini_batches

def random_mini_batches_orig(X, Y, mini_batch_size = 64, seed = 0):
    """
    Creates a list of random minibatches from (X, Y)

    Arguments:
    X -- input data, of shape (input size, number of examples)
    Y -- true "label" vector (1 for blue dot / 0 for red dot), of shape (1, number of examples)
    mini_batch_size -- size of the mini-batches, integer

    Returns:
    mini_batches -- list of synchronous (mini_batch_X, mini_batch_Y)
    """

    m = X.shape[1]                  # number of training examples
    mini_batches = []
    np.random.seed(seed)

    # Step 1: Shuffle (X, Y)
    permutation = list(np.random.permutation(m))
    shuffled_X = X[:, permutation]
    shuffled_Y = Y[:, permutation].reshape((Y.shape[0],m))

    # Step 2: Partition (shuffled_X, shuffled_Y). Minus the end case.
    num_complete_minibatches = math.floor(m/mini_batch_size) # number of mini batches of size mini_batch_size in your partitionning
    for k in range(0, num_complete_minibatches):
        mini_batch_X = shuffled_X[:, k * mini_batch_size : k * mini_batch_size + mini_batch_size]
        mini_batch_Y = shuffled_Y[:, k * mini_batch_size : k * mini_batch_size + mini_batch_size]
        mini_batch = (mini_batch_X, mini_batch_Y)
        mini_batches.append(mini_batch)

    # Handling the end case (last mini-batch < mini_batch_size)
    if m % mini_batch_size != 0:
        mini_batch_X = shuffled_X[:, num_complete_minibatches * mini_batch_size : m]
        mini_batch_Y = shuffled_Y[:, num_complete_minibatches * mini_batch_size : m]
        mini_batch = (mini_batch_X, mini_batch_Y)
        mini_batches.append(mini_batch)

    return mini_batches

def one_hot_matrix(labels, C):
    """
    Creates a matrix where the i-th row corresponds to the ith class number and the jth column
                     corresponds to the jth training example. So if example j had a label i. Then entry (i,j)
                     will be 1.
    Arguments:
    labels -- vector containing the labels
    C -- number of classes, the depth of the one hot dimension

    Returns:
    one_hot -- one hot matrix
    """
    C = tf.constant(C, name='C')
    one_hot_matrix = tf.one_hot(labels, C, axis=0)
    sess = tf.Session()
    one_hot = sess.run(one_hot_matrix)
    sess.close()

    return one_hot

def init_dataset_normalize():
    train_df = pd.read_csv('dataset/fashion-mnist_train.csv')
    test_df = pd.read_csv('dataset/fashion-mnist_test.csv')

    Y_train_orig = train_df['label'].values[1:]
    Y_test_orig = test_df['label'].values[1:]

    Y_train = one_hot_matrix(Y_train_orig, 10)
    Y_test = one_hot_matrix(Y_test_orig, 10)

    X_train_orig = train_df.T[1:].T.values[1:].T
    X_test_orig = test_df.T[1:].T.values[1:].T

    X_train_flatten = X_train_orig
    X_test_flatten = X_test_orig

    # Normalize image vectors
    X_train = X_train_flatten/255.
    X_test = X_test_flatten/255.

    return X_train, Y_train, X_test, Y_test

def visualizeImage(X_train_orig):
    index = 1
    plt.imshow(X_train_orig.T[index].reshape(28,28), cmap='gray')
    plt.show()

def flatternArrays(X_train_orig, X_test_orig):
    X_train_flatten = X_train_orig.reshape(X_train_orig.shape[0], -1).T
    X_test_flatten = X_test_orig.reshape(X_test_orig.shape[0], -1).T
    return X_train_orig, X_test_orig

def create_placeholders(n_x, n_y):
    X = tf.placeholder(tf.float32, shape=[n_x, None], name='X')
    Y = tf.placeholder(tf.float32, shape=[n_y, None], name='Y')
    return X, Y

def init_parameters(n_x, n_h1, n_h2, n_h3, n_h4):
    # Images are 28*28 so 728
    # The dataset has 10 different outfits
    # So b4 and w4 will be [10, ]
    W1 = tf.get_variable('W1', [n_h1, n_x], initializer = tf.contrib.layers.xavier_initializer(seed = 1))
    b1 = tf.get_variable('b1', [n_h1, 1], initializer = tf.zeros_initializer())
    W2 = tf.get_variable('W2', [n_h2, n_h1], initializer = tf.contrib.layers.xavier_initializer(seed = 1))
    b2 = tf.get_variable('b2', [n_h2, 1], initializer = tf.zeros_initializer())
    W3 = tf.get_variable('W3', [n_h3, n_h2], initializer = tf.contrib.layers.xavier_initializer(seed = 1))
    b3 = tf.get_variable('b3', [n_h3, 1], initializer = tf.zeros_initializer())
    W4 = tf.get_variable('W4', [n_h4, n_h3], initializer = tf.contrib.layers.xavier_initializer(seed = 1))
    b4 = tf.get_variable('b4', [n_h4, 1], initializer = tf.zeros_initializer())
    parameters = {"W1": W1,
                  "b1": b1,
                  "W2": W2,
                  "b2": b2,
                  "W3": W3,
                  "b3": b3,
                  "W4": W4,
                  "b4": b4}
    return parameters

def foward_prop(X, parameters, keep_prob):
    print('[FOWARD PROPAGATION]')
    print('KEEP PROP:', tf.Session().run(keep_prob))
    W1 = parameters["W1"]
    W2 = parameters["W2"]
    W3 = parameters["W3"]
    W4 = parameters["W4"]
    b1 = parameters["b1"]
    b2 = parameters["b2"]
    b3 = parameters["b3"]
    b4 = parameters["b4"]

    Z1 = tf.add(tf.matmul(W1, X), b1)
    A1 = tf.nn.relu(Z1)
    A1dropout=tf.nn.dropout(A1, keep_prob)
    Z2 = tf.add(tf.matmul(W2, A1dropout), b2)
    A2 = tf.nn.relu(Z2)
    A2dropout=tf.nn.dropout(A2, keep_prob)
    Z3 = tf.add(tf.matmul(W3, A2dropout), b3)
    A3 = tf.nn.relu(Z3)
    A3dropout=tf.nn.dropout(A3, keep_prob)
    Z4 = tf.add(tf.matmul(W4, A3dropout), b4)

    return Z4

def compute_cost(Z3, Y):
    return tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(
                logits=tf.transpose(Z3),
                labels=tf.transpose(Y)))

def model(X_train,
          Y_train,
          X_test,
          Y_test,
          learning_rate = 0.0001,
          num_epochs = 1500,
          minibatch_size = 32,
          keep_probability=1,
          L1=50,
          L2=25,
          L3=12,
          L4=10,
          batch_method="experimental",
          thread_count=1,
          queue_capacity=100,
          print_cost = True):

    # tf.set_random_seed(1)                             # to keep consistent results
    ops.reset_default_graph()                         # to be able to rerun the model without overwriting tf variables
    seed = 3
    (n_x, m) = X_train.shape                          # (n_x: input size, m : number of examples in the train set)
    n_y = Y_train.shape[0]                            # n_y : output size
    costs = []                                        # To keep track of the cost

    # Create Placeholders of shape (n_x, n_y)
    X, Y = create_placeholders(n_x, n_y)
    keep_prob = tf.constant(keep_probability, name='keep_prob')

    # Initialize parameters
    print('[NETWORK SIZE]')
    print('L1:', L1)
    print('L2:', L2)
    print('L3:', L3)
    print('L4:', L4)
    parameters = init_parameters(n_x, L1, L2, L3, L4)
    # Forward propagation: Build the forward propagation in the tensorflow graph
    Z3 = foward_prop(X, parameters, keep_prob)

    # Cost function: Add cost function to tensorflow graph
    cost = compute_cost(Z3, Y)

    # Backpropagation: Define the tensorflow optimizer. with AdamOptimizer.
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate, beta1=0.9, beta2=0.999).minimize(cost)

    # Initialize all the variables
    init = tf.global_variables_initializer()

    # Start the session to compute the tensorflow graph
    with tf.Session() as sess:
        # Run the initialization
        sess.run(init)

            # CREATE QUEUE
        if batch_method == 'tensorflow':
            minibatch_queue = random_mini_batches_tf(X_train, Y_train, minibatch_size, thread_count, queue_capacity, seed)
            coord = tf.train.Coordinator()
            threads = tf.train.start_queue_runners(coord=coord)

        # Do the training loop
        for epoch in range(num_epochs):
            epoch_cost = 0.                       # Defines a cost related to an epoch
            num_minibatches = int(m / minibatch_size) # number of minibatches of size minibatch_size in the train set
            seed = seed + 1

            minibatches=[]
            if batch_method == 'experimental':
                minibatches = random_mini_batches_exp(X_train, Y_train, minibatch_size, seed)
            if batch_method == 'basic':
                minibatches = random_mini_batches(X_train, Y_train, minibatch_size, seed)

            #GET MINIBATCHES FROM QUEUE
            if batch_method == 'tensorflow':
                for i in range(0, m, minibatch_size):
                    minibatch = sess.run(minibatch_queue)
                    minibatch_X, minibatch_Y = minibatch
                    _ , minibatch_cost = sess.run([optimizer, cost], feed_dict={X: minibatch_X.T, Y: minibatch_Y.T})
                    epoch_cost += minibatch_cost/num_minibatches
            else:
                for minibatch in minibatches:
                    # Select a minibatch
                    (minibatch_X, minibatch_Y) = minibatch
                    _ , minibatch_cost = sess.run([optimizer, cost], feed_dict={X: minibatch_X, Y: minibatch_Y})
                    epoch_cost += minibatch_cost/num_minibatches

            # Print the cost every epoch
            if print_cost == True and epoch % 100 == 0:
                print ("Cost after epoch %i: %f" % (epoch, epoch_cost))
            if print_cost == True and epoch % 5 == 0:
                costs.append(epoch_cost)

        #CLOSE QUEUE mini_batch
        if batch_method == 'tensorflow':
            coord.request_stop()
            coord.join(threads)

        # plot the cost
        plt.plot(np.squeeze(costs))
        plt.ylabel('cost')
        plt.xlabel('iterations (per tens)')
        plt.title("Learning rate =" + str(learning_rate))
        plt.savefig('./cost_function_graph/COST_FUNCTION_'+datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

        # lets save the parameters in a variable
        parameters = sess.run(parameters)
        print ("Parameters have been trained!")
        saveParams(parameters)

        # Calculate the correct predictions
        correct_prediction = tf.equal(tf.argmax(Z3), tf.argmax(Y))

        # Calculate accuracy on the test set
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))

        print ("Train Accuracy:", accuracy.eval({X: X_train, Y: Y_train}))
        print ("Test Accuracy:", accuracy.eval({X: X_test, Y: Y_test}))

        return parameters

def predict(X, parameters):

    W1 = tf.convert_to_tensor(parameters["W1"], tf.float32)
    b1 = tf.convert_to_tensor(parameters["b1"], tf.float32)
    W2 = tf.convert_to_tensor(parameters["W2"], tf.float32)
    b2 = tf.convert_to_tensor(parameters["b2"], tf.float32)
    W3 = tf.convert_to_tensor(parameters["W3"], tf.float32)
    b3 = tf.convert_to_tensor(parameters["b3"], tf.float32)
    W4 = tf.convert_to_tensor(parameters["W4"], tf.float32)
    b4 = tf.convert_to_tensor(parameters["b4"], tf.float32)

    params = {"W1": W1,
              "b1": b1,
              "W2": W2,
              "b2": b2,
              "W3": W3,
              "b3": b3,
              "W4": W4,
              "b4": b4}

    x = tf.placeholder("float", [X.shape[0], 1])

    z4 = forward_propagation_for_predict(x, params)
    p = tf.argmax(z4)

    sess = tf.Session()
    prediction = sess.run(p, feed_dict = {x: X})
    a4 = tf.nn.sigmoid(z4)
    propabilities = sess.run(a4, feed_dict= {x: X})
    sumProb = np.sum(propabilities)
    densityProb = np.divide(propabilities, sumProb)
    zz4 = sess.run(z4, feed_dict= {x: X})

    return prediction, densityProb, zz4

def forward_propagation_for_predict(X, parameters):
    """
    Implements the forward propagation for the model: LINEAR -> RELU -> LINEAR -> RELU -> LINEAR -> SOFTMAX

    Arguments:
    X -- input dataset placeholder, of shape (input size, number of examples)
    parameters -- python dictionary containing your parameters "W1", "b1", "W2", "b2", "W3", "b3"
                  the shapes are given in initialize_parameters

    Returns:
    Z3 -- the output of the last LINEAR unit
    """

    # Retrieve the parameters from the dictionary "parameters"
    W1 = parameters['W1']
    b1 = parameters['b1']
    W2 = parameters['W2']
    b2 = parameters['b2']
    W3 = parameters['W3']
    b3 = parameters['b3']
    W4 = parameters['W4']
    b4 = parameters['b4']
                                                           # Numpy Equivalents:
    Z1 = tf.add(tf.matmul(W1, X), b1)                      # Z1 = np.dot(W1, X) + b1
    A1 = tf.nn.relu(Z1)                                    # A1 = relu(Z1)
    Z2 = tf.add(tf.matmul(W2, A1), b2)                     # Z2 = np.dot(W2, a1) + b2
    A2 = tf.nn.relu(Z2)                                    # A2 = relu(Z2)
    Z3 = tf.add(tf.matmul(W3, A2), b3)                     # Z3 = np.dot(W3,Z2) + b3
    A3 = tf.nn.relu(Z3)
    Z4 = tf.add(tf.matmul(W4, A3), b4)

    return Z4

def saveParams(parameters):
    import json

    W1 = parameters['W1'].tolist()
    b1 = parameters['b1'].tolist()
    W2 = parameters['W2'].tolist()
    b2 = parameters['b2'].tolist()
    W3 = parameters['W3'].tolist()
    b3 = parameters['b3'].tolist()
    W4 = parameters['W4'].tolist()
    b4 = parameters['b4'].tolist()

    parameters_list = {"W1": W1,
                  "b1": b1,
                  "W2": W2,
                  "b2": b2,
                  "W3": W3,
                  "b3": b3,
                  "W4": W4,
                  "b4": b4}

    with open('./parameters.json', 'w') as f:
        json.dump(parameters_list, f)

def readParams():
    import json

    with open('parameters.json', 'r') as f:
        parameters = json.load(f)
        W1 = np.array(parameters['W1'])
        b1 = np.array(parameters['b1'])
        W2 = np.array(parameters['W2'])
        b2 = np.array(parameters['b2'])
        W3 = np.array(parameters['W3'])
        b3 = np.array(parameters['b3'])
        W4 = np.array(parameters['W4'])
        b4 = np.array(parameters['b4'])

        parameters_numpy = {"W1": W1,
                      "b1": b1,
                      "W2": W2,
                      "b2": b2,
                      "W3": W3,
                      "b3": b3,
                      "W4": W4,
                      "b4": b4}

    return parameters_numpy

def saveConfig(configDict):
    import json
    with open('./hyperparameters/config_'+datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')+'.json', 'w') as f:
        json.dump(configDict, f)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch_method', help='method used to make the mini batches', default = 'experimental')
    parser.add_argument('--learning_rate', help='learning rate for the algorithm', default=0.001)
    parser.add_argument('--batch_size', help='size of mini batches', default=32)
    parser.add_argument('--keep_prob', help='probability of keeping the neuron in the dropout method', default=0.8)
    parser.add_argument('--epoch', help='iteration number', default=1500)
    parser.add_argument('--thread_count', help='This is only for batch method tensorflow', default=2)
    parser.add_argument('--queue_capacity', help='This is only for batch method tensorflow, indicate the queue capacity of the batches', default=100)
    parser.add_argument('--L1', help='The size of hidden layer 1', default=50)
    parser.add_argument('--L2', help='The size of hidden layer 2', default=25)
    parser.add_argument('--L3', help='The size of hidden layer 3', default=12)
    parser.add_argument('--L4', help='The size of hidden layer 4', default=10)
    parser.add_argument('--predict_image_class', help='predict for image class using the pre trainned weights')
    args = parser.parse_args()

    if args.predict_image_class:
        predict_image_class(args.predict_image_class)
        return

    batch_method = args.batch_method
    learning_rate = float(args.learning_rate)
    batch_size = int(args.batch_size)
    keep_prob = float(args.keep_prob)
    epoch = int(args.epoch)
    thread_count = int(args.thread_count)
    queue_capacity = int(args.queue_capacity)
    L1 = int(args.L1)
    L2 = int(args.L2)
    L3 = int(args.L3)
    L4 = int(args.L4)

    config_dict = {'batch_method':batch_method,
                    'learning_rate':learning_rate,
                    'batch_size':batch_size,
                    'keep_prob':keep_prob,
                    'epoch':epoch,
                    'thread_count':thread_count,
                    'queue_capacity':queue_capacity,
                    'L1':L1,
                    'L2':L2,
                    'L3':L3,
                    'L4':L4}

    saveConfig(config_dict)

    print('[Parameters choosed]')
    print('BATCH METHOD:', batch_method)
    print('LEARNING RATE:', learning_rate)
    print('BATCH SIZE:', batch_size)
    print('KEEP PROB:', keep_prob)
    print('EPOCH:', epoch)
    print('L1:', L1)
    print('L2:', L2)
    print('L3:', L3)
    print('L4:', L4)
    if(batch_method=='tensorflow'):
        print('NUM THREADS:', thread_count)
        print('QUEUE CAPACITY:', queue_capacity)

    X_train, Y_train, X_test, Y_test = init_dataset_normalize()
    parameters = model(X_train,
              Y_train,
              X_test,
              Y_test,
              learning_rate = learning_rate,
              num_epochs = epoch,
              minibatch_size = batch_size,
              keep_probability=keep_prob,
              L1=L1,
              L2=L2,
              L3=L3,
              L4=L4,
              batch_method=batch_method,
              thread_count=thread_count,
              queue_capacity=queue_capacity,
              print_cost = True)

def predict_image_class(image_path):
    import scipy
    from PIL import Image
    from scipy import ndimage

    parameters = readParams()

    original_image = np.array(ndimage.imread(image_path, flatten=False))
    plt.imshow(original_image)
    plt.show()

    graycolor_image = np.array(ndimage.imread(image_path, flatten=True))
    plt.imshow(graycolor_image, cmap='gray')
    plt.show()

    image_flattern = scipy.misc.imresize(graycolor_image, size=(28,28)).reshape((1, 28*28)).T
    print('SHAPE FLATTEN: ', image_flattern.shape)

    recover_image = image_flattern.reshape(28,28)
    plt.imshow(recover_image, cmap='gray')
    plt.show()

    my_image_prediction, probabilities, zn = predict(image_flattern, parameters)

    print("Your algorithm predicts: y = " + str(np.squeeze(my_image_prediction)))

def image_test():
    X_train, Y_train, X_test, Y_test = init_dataset_normalize()
    parameters = readParams()

    print(X_test.shape)
    image = X_test[:, 5000].reshape(X_test.shape[0], 1)
    print(image.shape)
    print("LABEL: ", Y_test[:, 5000])

    my_image_prediction, probabilities, zn = predict(image, parameters)

    print("Your algorithm predicts: y = " + str(np.squeeze(my_image_prediction)))
    print(probabilities)
    print(zn)

def show_image(image_sample):
    import scipy
    from PIL import Image
    from scipy import ndimage
    print(image_sample.shape)
    print(image_sample.T[0])
    plt.imshow(image_sample.T[0].reshape(28,28), cmap='gray')
    plt.show()

main()
