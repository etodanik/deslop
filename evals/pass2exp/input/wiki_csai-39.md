In machine learning, a **classifier** is an algorithm or model that assigns a category (class label) to a given input based on its features. Classification is one of the most common tasks in **supervised learning**, where the model learns from a dataset of labeled examples and then predicts labels for new, unseen data.

**How it works**

1. **Training data:** A set of examples, each with features (input variables) and a known label (e.g., an email's words and whether it is spam or not).
2. **Learning:** The algorithm finds patterns or a decision rule that maps features to labels by optimizing some objective, such as minimizing classification error or a loss function.
3. **Prediction:** The trained classifier takes new inputs and outputs a predicted class, and often also a probability or confidence score for each class.
4. **Evaluation:** The model is tested on held-out data to estimate how well it generalizes.

**Types of classification problems**

- **Binary classification:** Two classes (spam vs. not spam, disease vs. no disease)
- **Multiclass classification:** More than two mutually exclusive classes (handwritten digits 0-9)
- **Multilabel classification:** Each instance can have several labels at once (tags for a photo)
- **Imbalanced classification:** Some classes are much rarer than others (fraud detection)

**Common classifier algorithms**

- **Logistic regression**
- **Naive Bayes**
- **k-nearest neighbors (k-NN)**
- **Decision trees** and ensemble methods like **random forests** and **gradient boosting**
- **Support vector machines (SVMs)**
- **Neural networks**, including convolutional and transformer-based models

**Discriminative vs. generative classifiers**

- **Discriminative** classifiers (logistic regression, SVMs, neural nets) model the decision boundary or the conditional probability P(y | x) directly.
- **Generative** classifiers (Naive Bayes, Gaussian mixture models) model how the data is generated, P(x | y) and P(y), and use Bayes' rule to classify.

**Evaluation metrics**

- **Accuracy:** Fraction of correct predictions
- **Precision and recall:** How many predicted positives are correct, and how many actual positives are found
- **F1 score:** Harmonic mean of precision and recall
- **ROC curve and AUC:** Trade-off between true and false positive rates
- **Confusion matrix:** A table of predicted vs. actual classes

**Challenges**

Overfitting and underfitting, class imbalance, noisy or biased data, feature selection, interpretability, and ensuring fairness.

**Applications**

Spam filtering, image recognition, medical diagnosis, sentiment analysis, credit scoring, fraud detection, and many more.