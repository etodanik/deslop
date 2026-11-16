In machine learning, a **classifier** is an algorithm or model that assigns a category (class label) to an input based on its features. Classification is a common task in **supervised learning**, where the model learns from a dataset of labeled examples and then predicts labels for new, unseen data.

It works in four steps.

1. **Training data:** A set of examples, each with features (input variables) and a known label (e.g., an email's words and whether it is spam).
2. **Learning:** The algorithm looks for a decision rule that maps features to labels, by optimizing some objective such as minimizing classification error or a loss function.
3. **Prediction:** The trained classifier takes new inputs and outputs a predicted class, and usually a probability for each class.
4. **Evaluation:** The model is tested on held-out data to estimate how well it generalizes.

Classification problems come in four types.

- **Binary:** Two classes (spam vs. not spam, disease vs. no disease)
- **Multiclass:** More than two mutually exclusive classes (handwritten digits 0-9)
- **Multilabel:** Each instance can have several labels (tags for a photo)
- **Imbalanced:** Some classes are much rarer than others (fraud detection)

Common classifier algorithms:

- Logistic regression
- Naive Bayes
- k-nearest neighbors (k-NN)
- Decision trees and ensembles such as random forests and gradient boosting
- Support vector machines (SVMs)
- Neural networks, including convolutional and transformer-based models

**Discriminative vs. generative classifiers.** Discriminative classifiers (logistic regression, SVMs, neural nets) model the decision boundary, or the conditional probability P(y | x), directly. Generative classifiers (Naive Bayes, Gaussian mixture models) model how the data is generated, P(x | y) and P(y), and use Bayes' rule to classify.

Evaluation metrics:

- **Accuracy:** Fraction of correct predictions
- **Precision and recall:** How many predicted positives are correct, and how many actual positives are found
- **F1 score:** Harmonic mean of precision and recall
- **ROC curve and AUC:** Trade-off between true and false positive rates
- **Confusion matrix:** A table of predicted vs. actual classes

Typical difficulties are overfitting and underfitting, class imbalance, noisy or biased data, feature selection, interpretability, and making sure the results are fair. Applications include spam filtering, image recognition, medical diagnosis, sentiment analysis, credit scoring, fraud detection, and many more.
